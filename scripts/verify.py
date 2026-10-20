"""One offline verification command. Python 3.10+, Git, Node.js; no dependencies."""
import argparse
import json
import os
from pathlib import Path
import platform
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = {'.task-runs', '.talk-runs', '.verification', '.aws', '.codex', '.agents'}


def child_environment():
    # Never forward provider keys, tokens, proxy credentials, or the full environment.
    allowed = {'PATH', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP',
               'TMPDIR', 'HOME', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'LANG',
               'LC_ALL', 'TZ'}
    result = {name: value for name, value in os.environ.items() if name.upper() in allowed}
    result.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    return result


def test_suite(directory, metrics):
    # A regression test must mock transport. This is a Python-process guard,
    # not a machine firewall or a sandbox inherited by arbitrary subprocesses.
    def offline(event, _args):
        if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'socket.sendto'):
            raise RuntimeError('Network access is forbidden in offline verification')
    sys.addaudithook(offline)
    suite = unittest.defaultTestLoader.discover(str(directory))
    discovered = suite.countTestCases()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    counts = {'discovered': discovered, 'run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'expected_failures': len(result.expectedFailures),
              'unexpected_successes': len(result.unexpectedSuccesses),
              'skip_reasons': [reason for _test, reason in result.skipped]}
    Path(metrics).write_text(json.dumps(counts, indent=2) + '\n', encoding='utf-8')
    return 0 if (result.wasSuccessful() and discovered and result.testsRun == discovered
                 and not result.skipped and not result.expectedFailures) else 1


class Verifier:
    def __init__(self, repo, output, base=None):
        self.repo = Path(repo).resolve()
        self.output = Path(output).resolve()
        # Refuse live-ledger/transcript locations and any existing output directory.
        if any(part.lower() in PRIVATE - {'.verification'} for part in self.output.parts):
            raise ValueError('Verification output cannot use a private run directory')
        self.output.mkdir(parents=True, exist_ok=False)
        self.base = base
        self.paths = None
        self.report = {'schema_version': 'castle-offline-verification/1',
                       'source_commit': None, 'platform': platform.system(),
                       'python': platform.python_version(), 'node': None,
                       'checks': [], 'passed': False, 'offline_only': True}

    def save(self):
        (self.output / 'summary.json').write_text(
            json.dumps(self.report, indent=2) + '\n', encoding='utf-8')

    def command(self, args, log, input_data=None):
        log.write('COMMAND: ' + json.dumps([str(arg) for arg in args]) + '\n')
        log.flush()
        try:
            result = subprocess.run(args, cwd=self.repo, env=child_environment(),
                                    input=input_data, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=180)
        except subprocess.TimeoutExpired as exc:
            partial = exc.stdout or b''
            log.write(partial.decode('utf-8', errors='replace'))
            raise RuntimeError('Required command timed out after 180 seconds') from exc
        output = result.stdout.decode('utf-8', errors='replace')
        log.write(output + '\nEXIT: ' + str(result.returncode) + '\n')
        log.flush()
        if result.returncode:
            raise RuntimeError('Required command failed with exit ' + str(result.returncode))
        return output

    def git(self, args, log, input_data=None):
        executable = shutil.which('git')
        if not executable:
            raise RuntimeError('Missing required tool: git')
        return self.command([executable, *args], log, input_data).rstrip('\r\n')

    def safe_path(self, relative):
        path = self.repo / relative
        if (any(part.lower() in PRIVATE or part.lower() == '.env' or part.lower().startswith('.env.')
                for part in Path(relative).parts) or path.suffix.lower() in ('.key', '.pem')):
            raise ValueError('Private tracked path is forbidden: ' + relative)
        if not path.resolve().is_relative_to(self.repo):
            raise ValueError('Tracked source escapes checkout: ' + relative)
        resolved = path.resolve().relative_to(self.repo)
        if any(part.lower() in PRIVATE or part.lower() == '.env' or part.lower().startswith('.env.') for part in resolved.parts):
            raise ValueError('Tracked source points to private data: ' + relative)
        return path

    def sources(self, suffix):
        if self.paths is None:
            raise RuntimeError('Tracked-file discovery unavailable; Git is required')
        return [self.safe_path(name) for name in self.paths if name.lower().endswith(suffix)]

    def discover(self, log):
        # ls-files is NUL-separated so spaces and Unicode filenames remain intact.
        listed = self.git(['ls-files', '-z'], log)
        self.paths = [name for name in listed.split('\0') if name]
        for name in self.paths:
            self.safe_path(name)
        if not self.paths:
            raise RuntimeError('No tracked sources discovered')
        self.report['source_commit'] = self.git(['rev-parse', '--verify', 'HEAD'], log)
        return {'tracked_files': len(self.paths)}

    def suite(self, directory, log):
        metrics = self.output / (directory.replace('/', '-') + '.json')
        try:
            self.command([sys.executable, str(Path(__file__).resolve()), '--suite',
                          str(self.repo / directory), '--metrics', str(metrics)], log)
        finally:
            if metrics.exists():
                # Retain actual runner outcomes even when the command failed.
                self.report['checks'][-1]['counts'] = json.loads(metrics.read_text(encoding='utf-8'))
        if not metrics.exists():
            raise RuntimeError('Test runner did not produce current-run metrics')
        return self.report['checks'][-1]['counts']

    def compile_python(self, log):
        paths = self.sources('.py')
        if not paths:
            raise RuntimeError('No tracked Python sources discovered')
        errors = []
        with tempfile.TemporaryDirectory(prefix='castle-compile-') as temporary:
            for index, path in enumerate(paths):
                try:
                    py_compile.compile(str(path), cfile=str(Path(temporary) / f'{index}.pyc'), doraise=True)
                except (OSError, py_compile.PyCompileError) as exc:
                    errors.append(path.relative_to(self.repo).as_posix())
                    log.write(str(exc) + '\n')
        self.report['checks'][-1]['counts'] = {'files': len(paths), 'failed_files': len(errors)}
        if errors:
            raise RuntimeError('Python compilation failed: ' + ', '.join(errors))
        return self.report['checks'][-1]['counts']

    def parse_json(self, log):
        paths = self.sources('.json')
        if not paths:
            raise RuntimeError('No tracked JSON sources discovered')
        errors = []
        def reject_constant(_value):
            raise ValueError('Nonfinite number is not valid JSON')
        for path in paths:
            try:
                json.loads(path.read_text(encoding='utf-8'), parse_constant=reject_constant)
            except (OSError, ValueError) as exc:
                errors.append(path.relative_to(self.repo).as_posix())
                log.write(path.relative_to(self.repo).as_posix() + ': ' + str(exc) + '\n')
        self.report['checks'][-1]['counts'] = {'files': len(paths), 'failed_files': len(errors)}
        if errors:
            raise RuntimeError('Tracked JSON parsing failed: ' + ', '.join(errors))
        return self.report['checks'][-1]['counts']

    def javascript(self, log):
        paths = [path for path in self.sources('.js') if path.parent == self.repo / 'castle/scripts']
        node = shutil.which('node')
        if not node:
            raise RuntimeError('Missing required tool: node (JavaScript syntax checks cannot run)')
        self.report['node'] = self.command([node, '--version'], log).strip()
        if not paths:
            raise RuntimeError('No Castle JavaScript scripts discovered')
        errors = []
        for path in paths:
            try:
                self.command([node, '--check', str(path)], log)
            except RuntimeError:
                errors.append(path.name)
        self.report['checks'][-1]['counts'] = {'files': len(paths), 'failed_files': len(errors)}
        if errors:
            raise RuntimeError('JavaScript syntax failed: ' + ', '.join(errors))
        return self.report['checks'][-1]['counts']

    def cli_help(self, log):
        entries = ['castle/talk.py', 'castle/project_tasks.py']
        errors = []
        for entry in entries:
            try:
                self.command([sys.executable, str(self.safe_path(entry)), '--help'], log)
            except (RuntimeError, ValueError):
                errors.append(entry)
        self.report['checks'][-1]['counts'] = {'commands': len(entries), 'failed_commands': len(errors)}
        if errors:
            raise RuntimeError('CLI help failed: ' + ', '.join(errors))
        return self.report['checks'][-1]['counts']

    def whitespace(self, log):
        if self.paths is None:
            raise RuntimeError('Tracked-file discovery unavailable; cannot safely check diffs')
        for path in self.paths:
            self.safe_path(path)
        base = self.base
        if not base:
            try:
                base = self.git(['merge-base', 'HEAD', 'origin/main'], log)
            except RuntimeError:
                base = 'HEAD'
            if base == self.report['source_commit'] or base == 'HEAD':
                try:
                    base = self.git(['rev-parse', '--verify', 'HEAD^'], log)
                except RuntimeError:
                    base = self.git(['mktree'], log, b'')
        elif set(base) == {'0'}:
            base = self.git(['mktree'], log, b'')
        errors = []
        commands = [['diff', '--check', base, 'HEAD'], ['diff', '--check'], ['diff', '--cached', '--check']]
        for args in commands:
            try:
                self.git(args, log)
            except RuntimeError:
                errors.append(args)
        self.report['diff_base'] = base
        self.report['checks'][-1]['counts'] = {'commands': len(commands), 'failed_commands': len(errors)}
        if errors:
            raise RuntimeError('Committed, working-tree, or staged whitespace check failed')
        return self.report['checks'][-1]['counts']

    def run(self):
        checks = [('tracked-sources', self.discover),
                  ('conversation-project-tests', lambda log: self.suite('tests', log)),
                  ('runtime-probe-tests', lambda log: self.suite('runtime-probe/tests', log)),
                  ('python-compilation', self.compile_python), ('tracked-json', self.parse_json),
                  ('javascript-syntax', self.javascript), ('cli-help', self.cli_help),
                  ('diff-whitespace', self.whitespace)]
        for name, action in checks:
            item = {'name': name, 'status': 'running'}
            self.report['checks'].append(item)
            self.save()
            started = time.monotonic()
            with (self.output / (name + '.log')).open('x', encoding='utf-8') as log:
                try:
                    item['counts'] = action(log)
                    item['status'] = 'passed'
                except Exception as exc:
                    item.update(status='failed', error=type(exc).__name__ + ': ' + str(exc))
                    log.write(item['error'] + '\n')
                finally:
                    item['elapsed_seconds'] = round(time.monotonic() - started, 3)
                    self.save()
            print(name + ': ' + item['status'] + ' ' + json.dumps(item.get('counts', {})), flush=True)
        self.report['passed'] = all(item['status'] == 'passed' for item in self.report['checks'])
        self.save()
        print('Evidence: ' + str(self.output), flush=True)
        return 0 if self.report['passed'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='PR base SHA or main push before SHA; default: local merge base')
    parser.add_argument('--output', type=Path, help='New directory for verifier-only evidence')
    parser.add_argument('--suite', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--metrics', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.suite is not None:
        return test_suite(args.suite, args.metrics)
    output = args.output or ROOT / '.verification' / uuid.uuid4().hex
    try:
        return Verifier(ROOT, output, args.base).run()
    except (OSError, ValueError) as exc:
        print('Verification setup failed: ' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
