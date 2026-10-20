"""Synthetic checkout fixtures for failure aggregation and safe offline evidence."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        for directory in ('castle/scripts', 'tests', 'runtime-probe/tests'):
            (self.repo / directory).mkdir(parents=True)
        for entry in ('talk.py', 'project_tasks.py'):
            (self.repo / 'castle' / entry).write_text(
                'import argparse\nargparse.ArgumentParser().parse_args()\n', encoding='utf-8')
        for name in ('castle_engine', 'joke_mapper', 'personality_map', 'q_switch'):
            (self.repo / 'castle/scripts' / (name + '.js')).write_text('const fixture = 1;\n', encoding='utf-8')
        self.smoke = 'import unittest\nclass Fixture(unittest.TestCase):\n    def test_fixture(self):\n        self.assertEqual(2 + 2, 4)\n'
        for directory in ('tests', 'runtime-probe/tests'):
            (self.repo / directory / 'test_fixture.py').write_text(self.smoke, encoding='utf-8')
        (self.repo / 'data.json').write_text('{"fixture":"synthetic"}\n', encoding='utf-8')
        (self.repo / '.gitignore').write_text('.verification/\n', encoding='utf-8')
        self.git('init', '--quiet')
        self.git('add', '.')
        self.git('-c', 'user.name=Offline Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '--quiet', '-m', 'Synthetic verification fixture')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, env=verify.child_environment(),
                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def run_verifier(self):
        output = self.repo / '.verification' / str(len(list(self.repo.glob('.verification/*'))))
        verifier = verify.Verifier(self.repo, output)
        result = verifier.run()
        saved = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        return result, {item['name']: item for item in saved['checks']}, output

    def test_success_discovers_counts_without_reading_untracked_live_data(self):
        (self.repo / 'untracked.json').write_text('not json', encoding='utf-8')
        (self.repo / '.task-runs').mkdir()
        (self.repo / '.task-runs/private.json').write_text('SYNTHETIC_PRIVATE_SENTINEL', encoding='utf-8')
        result, checks, output = self.run_verifier()
        self.assertEqual(result, 0)
        self.assertEqual(checks['tracked-json']['counts']['files'], 1)
        self.assertEqual(checks['javascript-syntax']['counts']['files'], 4)
        for suite in ('conversation-project-tests', 'runtime-probe-tests'):
            self.assertEqual(checks[suite]['counts']['discovered'], 1)
            self.assertEqual(checks[suite]['counts']['run'], 1)
        self.assertNotIn('SYNTHETIC_PRIVATE_SENTINEL', ''.join(path.read_text(encoding='utf-8') for path in output.iterdir()))

    def test_failing_tests_and_invalid_json_do_not_hide_independent_checks(self):
        (self.repo / 'tests/test_fixture.py').write_text(self.smoke.replace('2 + 2, 4', '2 + 2, 5'), encoding='utf-8')
        (self.repo / 'data.json').write_text('not json', encoding='utf-8')
        result, checks, output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertEqual(checks['conversation-project-tests']['counts']['failures'], 1)
        self.assertEqual(checks['conversation-project-tests']['status'], 'failed')
        self.assertEqual(checks['tracked-json']['status'], 'failed')
        for name in ('runtime-probe-tests', 'python-compilation', 'javascript-syntax', 'cli-help', 'diff-whitespace'):
            self.assertEqual(checks[name]['status'], 'passed')
        self.assertIn('AssertionError', (output / 'conversation-project-tests.log').read_text(encoding='utf-8'))

    def test_missing_node_is_explicit_failure_and_later_checks_still_run(self):
        original = shutil.which
        with patch.object(verify.shutil, 'which', side_effect=lambda name: None if name == 'node' else original(name)):
            result, checks, _output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertIn('Missing required tool: node', checks['javascript-syntax']['error'])
        self.assertEqual(checks['cli-help']['status'], 'passed')
        self.assertEqual(checks['diff-whitespace']['status'], 'passed')

    def test_missing_git_does_not_prevent_test_suites_or_help(self):
        original = shutil.which
        with patch.object(verify.shutil, 'which', side_effect=lambda name: None if name == 'git' else original(name)):
            result, checks, _output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertIn('Missing required tool: git', checks['tracked-sources']['error'])
        self.assertEqual(checks['conversation-project-tests']['status'], 'passed')
        self.assertEqual(checks['runtime-probe-tests']['status'], 'passed')
        self.assertEqual(checks['cli-help']['status'], 'passed')
        self.assertIn('discovery unavailable', checks['tracked-json']['error'])

    def test_staged_whitespace_is_checked_in_addition_to_committed_changes(self):
        (self.repo / 'dirty.py').write_text('value = 1  \n', encoding='utf-8')
        self.git('add', 'dirty.py')
        result, checks, output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertEqual(checks['diff-whitespace']['status'], 'failed')
        self.assertIn('trailing whitespace', (output / 'diff-whitespace.log').read_text(encoding='utf-8'))

    def test_skipped_tests_fail_explicitly_and_private_output_is_refused(self):
        skipped = self.smoke.replace('    def test_fixture', '    @unittest.skip("synthetic unavailable prerequisite")\n    def test_fixture')
        (self.repo / 'tests/test_fixture.py').write_text(skipped, encoding='utf-8')
        result, checks, _output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertEqual(checks['conversation-project-tests']['counts']['skipped'], 1)
        self.assertEqual(checks['conversation-project-tests']['counts']['skip_reasons'], ['synthetic unavailable prerequisite'])
        with self.assertRaisesRegex(ValueError, 'private run directory'):
            verify.Verifier(self.repo, self.repo / '.task-runs/evidence')
        with self.assertRaisesRegex(ValueError, 'private run directory'):
            verify.Verifier(self.repo, self.repo / '.TASK-RUNS/evidence')

    def test_test_process_has_no_provider_credentials_and_network_is_blocked(self):
        source = '''import os, socket, unittest
class Offline(unittest.TestCase):
    def test_offline(self):
        self.assertNotIn('OPENROUTER_API_KEY', os.environ)
        self.assertNotIn('GH_TOKEN', os.environ)
        with self.assertRaisesRegex(RuntimeError, 'Network access is forbidden'):
            socket.create_connection(('localhost', 9))
'''
        (self.repo / 'tests/test_fixture.py').write_text(source, encoding='utf-8')
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-not-a-credential'}):
            result, checks, _output = self.run_verifier()
        self.assertEqual(result, 0)
        self.assertEqual(checks['conversation-project-tests']['counts']['run'], 1)

    def test_existing_evidence_is_never_overwritten(self):
        output = self.repo / '.verification/preserved'
        output.mkdir(parents=True)
        (output / 'failure.log').write_text('preserve this failure', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            verify.Verifier(self.repo, output)
        self.assertEqual((output / 'failure.log').read_text(encoding='utf-8'), 'preserve this failure')

    def test_accidentally_tracked_private_data_fails_without_copying_contents(self):
        private = self.repo / '.TASK-RUNS/private.json'
        private.parent.mkdir()
        private.write_text('{"private":"SYNTHETIC_DO_NOT_UPLOAD"}', encoding='utf-8')
        self.git('add', '.TASK-RUNS/private.json')
        result, checks, output = self.run_verifier()
        self.assertEqual(result, 1)
        self.assertIn('Private tracked path is forbidden', checks['tracked-sources']['error'])
        self.assertEqual(checks['tracked-json']['status'], 'failed')
        self.assertNotIn('SYNTHETIC_DO_NOT_UPLOAD', ''.join(path.read_text(encoding='utf-8') for path in output.iterdir()))

    def test_zero_tests_and_expected_failures_are_reported_without_green(self):
        for source, metric in [
                ('# Synthetic empty suite\n', 'discovered'),
                (self.smoke.replace('    def test_fixture', '    @unittest.expectedFailure\n    def test_fixture')
                           .replace('2 + 2, 4', '2 + 2, 5'), 'expected_failures')]:
            with self.subTest(metric=metric):
                (self.repo / 'tests/test_fixture.py').write_text(source, encoding='utf-8')
                result, checks, _output = self.run_verifier()
                self.assertEqual(result, 1)
                self.assertEqual(checks['conversation-project-tests']['status'], 'failed')
                self.assertEqual(checks['conversation-project-tests']['counts'][metric], 0 if metric == 'discovered' else 1)
                self.assertEqual(checks['runtime-probe-tests']['status'], 'passed')
