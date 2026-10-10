import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import runtime_probe as probe
from prepare_deployment import prepare


class ProbeTests(unittest.TestCase):
    def test_real_file_roundtrip_and_cleanup(self):
        result=probe.temporary_file()
        self.assertIsNone(result['error'])
        for key in ('created','write','read','delete','directory_removed'):
            self.assertTrue(result['value'][key],key)

    def test_real_child_output_and_termination(self):
        for terminate in (False,True):
            result=probe.child_probe(terminate)
            self.assertIsNone(result['error'],result)
            self.assertTrue(result['value']['output_received'])
            self.assertTrue(result['value']['reaped'])
            self.assertEqual(result['value']['terminate_sent'],terminate)

    def test_denied_child_preserves_error(self):
        with patch.object(probe.subprocess,'Popen',side_effect=PermissionError(13,'fixture denial')):
            result=probe.child_probe()
        self.assertEqual(result['error']['type'],'PermissionError')
        self.assertEqual(result['error']['errno'],13)
        self.assertFalse(result['value']['launched'])

    def test_failed_check_does_not_erase_other_results(self):
        log=io.StringIO()
        with patch.object(probe,'python_info',side_effect=RuntimeError('fixture failure')),contextlib.redirect_stderr(log):
            result=probe.run_probe('probe-test-isolation')
        self.assertEqual(result['checks']['python']['error']['message'],'fixture failure')
        self.assertEqual(result['checks']['temporary_file']['status'],'ok')
        self.assertEqual(len(result['checks']),10)
        self.assertTrue(all(json.loads(l)['probe_id']==result['probe_id'] for l in log.getvalue().splitlines()))

    def test_missing_resource_is_null_and_unavailable(self):
        with patch.object(probe,'host_memory',side_effect=FileNotFoundError('fixture absent')),contextlib.redirect_stderr(io.StringIO()):
            result=probe.run_probe('probe-test-unavailable')
        self.assertEqual(result['checks']['host_memory']['status'],'unavailable')
        self.assertIsNone(result['checks']['host_memory']['value'])

    def test_package_discovery_does_not_import_target(self):
        before=set(sys.modules)
        for name in ('torch','transformers','mcp'):
            result=probe.package_info(name)
            self.assertFalse(result['import_tested'])
            if name not in before:self.assertNotIn(name,sys.modules)

    def test_deployment_plan_rejects_mutable_revision_and_credential_url(self):
        with self.assertRaises(ValueError):prepare('https://github.com/example/probe','main')
        with self.assertRaises(ValueError):prepare('https://token@github.com/example/probe','a'*40)
        # This is explicitly synthetic validation input, not a proposed repository/SHA.
        dep,execution=prepare('https://github.com/example/probe','a'*40)
        self.assertEqual(dep['spec']['revision'],'a'*40)
        self.assertTrue(execution['input']['probe_id'].startswith('probe-'))


if __name__=='__main__':unittest.main()
