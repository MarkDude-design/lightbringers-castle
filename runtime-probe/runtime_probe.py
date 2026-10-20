"""Bounded runtime observations. Standard library only; no network or installs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid


def error_info(exc):
    return {'type':type(exc).__name__, 'message':str(exc),
            'errno':getattr(exc, 'errno', None)}


def emit(probe_id, event, **fields):
    print(json.dumps({'probe_id':probe_id, 'event':event, **fields}),
          file=sys.stderr, flush=True)


def python_info():
    return {'version':sys.version, 'implementation':platform.python_implementation(),
            'system':platform.system(), 'release':platform.release(),
            'machine':platform.machine()}


def temporary_file():
    state={'created':False, 'write':False, 'read':False, 'delete':False,
           'directory_removed':False, 'cleanup_error':None}
    directory=None
    try:
        directory=tempfile.TemporaryDirectory(prefix='runtime-probe-')
        state['created']=True
        path=Path(directory.name)/'marker.txt'
        path.write_text('runtime-probe-marker', encoding='utf-8');state['write']=True
        state['read']=path.read_text(encoding='utf-8')=='runtime-probe-marker'
        if not state['read']:raise RuntimeError('Temporary-file contents did not match')
        path.unlink();state['delete']=not path.exists()
    except Exception as exc:
        return {'value':state, 'error':error_info(exc)}
    finally:
        if directory is not None:
            try:
                directory.cleanup()
                state['directory_removed']=not Path(directory.name).exists()
            except Exception as exc:
                state['cleanup_error']=error_info(exc)
    return {'value':state, 'error':state['cleanup_error']}


def _await_child_ready(proc, ready):
    deadline=time.monotonic()+5
    while True:
        remaining=deadline-time.monotonic()
        if remaining<=0:
            raise TimeoutError('Child did not emit readiness within 5 seconds')
        if ready.wait(min(0.05,remaining)):
            if proc.poll() is not None:
                raise RuntimeError('Child exited before termination probe')
            return
        if proc.poll() is not None:
            raise RuntimeError('Child exited before termination probe')


def child_probe(terminate=False):
    """Launch only fixed Python code; pass an empty child environment."""
    code="print('runtime-probe-child-ready', flush=True)"
    if terminate:code += '; import time; time.sleep(30)'
    proc=None
    value={'launched':False, 'output_received':False, 'stdout':None, 'stderr':None,
           'terminate_sent':False, 'kill_fallback':False, 'returncode':None,
           'reaped':False, 'cleanup_error':None}
    failure=None
    ready=threading.Event()
    outputs={'stdout':[], 'stderr':[]}
    readers=[]
    reader_errors=[]

    def read_stream(name, stream):
        # Each pipe has one reader. communicate() timeout output is not a
        # portable readiness signal (Windows may not expose it until EOF).
        try:
            for line in iter(stream.readline,''):
                outputs[name].append(line)
                if name=='stdout' and line.rstrip('\r\n')=='runtime-probe-child-ready':
                    ready.set()
        except Exception as exc:
            reader_errors.append(error_info(exc))
        finally:
            stream.close()

    try:
        proc=subprocess.Popen([sys.executable,'-I','-u','-c',code],
                              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,text=True,env={})
        value['launched']=True
        for name in ('stdout','stderr'):
            reader=threading.Thread(target=read_stream,
                                    args=(name,getattr(proc,name)),daemon=True)
            reader.start()
            readers.append(reader)
        if terminate:
            _await_child_ready(proc,ready)
            proc.terminate();value['terminate_sent']=True
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill();value['kill_fallback']=True
                proc.wait(timeout=2)
        else:
            proc.wait(timeout=5)
    except Exception as exc:
        failure=error_info(exc)
    finally:
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.kill();value['kill_fallback']=True
                proc.wait(timeout=2)
                value.update(returncode=proc.returncode,reaped=True)
            except Exception as exc:
                value['cleanup_error']=error_info(exc)
            for reader in readers:
                reader.join(timeout=2)
            if any(reader.is_alive() for reader in readers):
                value['cleanup_error']=value['cleanup_error'] or error_info(
                    TimeoutError('Child output reader did not finish within 2 seconds'))
            value.update(stdout=''.join(outputs['stdout']),stderr=''.join(outputs['stderr']),
                         output_received=ready.is_set())
            if reader_errors:
                value['cleanup_error']=value['cleanup_error'] or reader_errors[0]
    if failure is None and value['cleanup_error'] is None:
        if not value['output_received']:
            failure=error_info(RuntimeError('Expected child output missing'))
        elif not terminate and value['returncode']!=0:
            failure=error_info(RuntimeError('Child returned nonzero status'))
    return {'value':value,'error':failure or value['cleanup_error']}


def package_info(name):
    # Discovery only: do not import torch/transformers/mcp or execute their code.
    found=importlib.util.find_spec(name) is not None
    version=None
    try:version=importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:pass
    return {'module_discoverable':found,'distribution_version':version,
            'import_tested':False, 'usable_for_inference':None}


def host_memory():
    wanted={'MemTotal':'total_bytes','MemAvailable':'available_bytes'}
    values={'total_bytes':None,'available_bytes':None,'scope':'host-visible; not a container quota'}
    for line in Path('/proc/meminfo').read_text().splitlines():
        key,_,rest=line.partition(':')
        if key in wanted:
            number,unit=rest.split()
            if unit!='kB':raise ValueError('Unexpected memory unit')
            values[wanted[key]]=int(number)*1024
    return values


def cgroup_memory():
    # Observe only the cgroup-v2 mount root visible in this container. Do not
    # claim these are this process's limits if the mount is not namespaced.
    root=Path('/sys/fs/cgroup')
    limit_text=(root/'memory.max').read_text().strip()
    current=int((root/'memory.current').read_text().strip())
    limit=None if limit_text=='max' else int(limit_text)
    return {'limit_bytes':limit,'current_bytes':current,
            'headroom_bytes':None if limit is None else max(0,limit-current),
            'scope':'visible cgroup-v2 mount root; process membership not established'}


def disk_space():
    usage=shutil.disk_usage(tempfile.gettempdir())
    return {'total_bytes':usage.total,'used_bytes':usage.used,'free_bytes':usage.free,
            'scope':'temporary filesystem; persistence and per-user quota untested'}


def run_probe(probe_id=None, context='local'):
    probe_id=probe_id or 'probe-'+uuid.uuid4().hex
    if not isinstance(probe_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',probe_id):
        raise ValueError('probe_id must contain 1..100 letters, numbers, underscores or hyphens')
    report={'schema_version':1,'probe_id':probe_id,'context':context,
            'started_at':datetime.now(timezone.utc).isoformat(),'checks':{}}
    emit(probe_id,'probe_started',context=context)
    checks=[('python',python_info),('temporary_file',temporary_file),
            ('child_return',child_probe),('child_termination',lambda:child_probe(True)),
            *[('package_'+name,lambda name=name:package_info(name)) for name in ('torch','transformers','mcp')],
            ('host_memory',host_memory),('cgroup_memory',cgroup_memory),('temporary_disk',disk_space)]
    for name,check in checks:
        start=time.monotonic()
        try:
            result=check()
            if 'value' not in result or 'error' not in result:result={'value':result,'error':None}
            status='error' if result['error'] else 'ok'
        except Exception as exc:
            result={'value':None,'error':error_info(exc)}
            status='unavailable' if isinstance(exc,(FileNotFoundError,NotImplementedError)) else 'error'
        report['checks'][name]={'status':status,**result,'elapsed_seconds':round(time.monotonic()-start,6)}
        emit(probe_id,'check_completed',check=name,status=status)
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    report['summary']={s:sum(c['status']==s for c in report['checks'].values()) for s in ('ok','error','unavailable')}
    emit(probe_id,'probe_finished',summary=report['summary'])
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-id');parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=run_probe(args.probe_id)
    output=json.dumps(report,indent=2,allow_nan=False)+'\n'
    if args.output:args.output.write_text(output,encoding='utf-8')
    print(output,end='')
    raise SystemExit(1 if report['summary']['error'] else 0)
