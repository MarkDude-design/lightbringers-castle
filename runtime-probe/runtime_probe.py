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


def child_probe(terminate=False):
    """Launch only fixed Python code; pass an empty child environment."""
    code="print('runtime-probe-child-ready', flush=True)"
    if terminate:code += '; import time; time.sleep(30)'
    proc=None
    value={'launched':False, 'output_received':False, 'stdout':None, 'stderr':None,
           'terminate_sent':False, 'kill_fallback':False, 'returncode':None,
           'reaped':False, 'cleanup_error':None}
    failure=None
    try:
        proc=subprocess.Popen([sys.executable,'-I','-u','-c',code],
                              stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,text=True,env={})
        value['launched']=True
        if terminate:
            deadline=time.monotonic()+5
            while True:
                try:
                    proc.communicate(timeout=0.1)
                    raise RuntimeError('Child exited before termination probe')
                except subprocess.TimeoutExpired as exc:
                    partial=exc.output or b''
                    if isinstance(partial,bytes):partial=partial.decode('utf-8',errors='replace')
                    if 'runtime-probe-child-ready' in partial:break
                    if time.monotonic()>=deadline:
                        raise TimeoutError('Child did not emit readiness within 5 seconds')
            proc.terminate();value['terminate_sent']=True
            try:out,err=proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill();value['kill_fallback']=True
                out,err=proc.communicate(timeout=2)
        else:
            out,err=proc.communicate(timeout=5)
        value.update(stdout=out,stderr=err,returncode=proc.returncode,reaped=True,
                     output_received='runtime-probe-child-ready' in out)
        if not value['output_received']:raise RuntimeError('Expected child output missing')
        if not terminate and proc.returncode!=0:raise RuntimeError('Child returned nonzero status')
    except Exception as exc:
        failure=error_info(exc)
    finally:
        if proc is not None:
            try:
                if proc.poll() is None:
                    proc.kill();value['kill_fallback']=True
                out,err=proc.communicate(timeout=2)
                value.update(stdout=out,stderr=err,returncode=proc.returncode,reaped=True)
            except Exception as exc:
                value['cleanup_error']=error_info(exc)
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
