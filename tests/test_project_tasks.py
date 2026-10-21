"""Offline transactions exercise real packet/artifact/accounting boundaries."""
import copy
import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'castle'))
import project_tasks as tasks


class ProjectTaskTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        (self.repo / 'castle').mkdir()
        # The fixture has explicit LF bytes on every host; production packets
        # must continue hashing source bytes exactly as they exist on disk.
        (self.repo / 'castle/example.py').write_bytes(b'def greet():\n    return "hello"\n')
        self.config = {
            'task': {'task_id': 'fixture-task', 'goal': 'Propose a bounded greeting fix.',
                     'acceptance_criteria': ['Preserve the public function name.'],
                     'boundaries': ['Proposals only; do not execute or apply changes.'],
                     'source_files': ['castle/example.py'], 'allowed_files': ['castle/example.py']},
            'worker_model': 'fixture/worker:free', 'reviewer_model': 'fixture/reviewer:free',
            'budget_usd': '0.01', 'allow_paid': False, 'max_completion_tokens': 1200,
            'pricing': {},
        }
        for role in ('worker', 'reviewer'):
            self.config['pricing'][self.config[role + '_model']] = {
                'observed_on': datetime.now(timezone.utc).date().isoformat(),
                'source': 'Synthetic offline fixture, not a market quote',
                'input_usd_per_million': '0', 'output_usd_per_million': '0'}
        self.packet = self.freeze()
        self.requests = []

    def freeze(self):
        return tasks.freeze_packet(self.repo, self.config['task'], 'a' * 40)

    def ticket(self, packet=None):
        packet = packet or self.packet
        return {'schema_version': 'castle-ticket/0.1', 'packet_sha256': tasks.digest(packet),
                'problem': 'The greeting lacks punctuation.',
                'source_refs': [{'path': 'castle/example.py', 'start_line': 1, 'end_line': 2}],
                'allowed_files': ['castle/example.py'], 'proposed_change': 'Add punctuation to the return value.',
                'acceptance_checks': ['Verify greet returns the punctuated text.'], 'uncertainties': []}

    def provider(self, provider, key, body):
        self.requests.append(copy.deepcopy(body))
        payload = json.loads(body['messages'][1]['content'])
        if 'worker' not in payload:
            value = self.ticket(payload['packet'])
        else:
            value = {'schema_version': 'castle-task-review/0.1',
                     'packet_sha256': payload['packet_sha256'], 'worker_sha256': payload['worker_sha256'],
                     'verdict': 'pass', 'reasons': [{'note': 'The ticket cites the actual return value.',
                         'source_refs': self.ticket()['source_refs']}], 'uncertainties': []}
        message = {'role': 'assistant', 'content': json.dumps(value)}
        return {'status': 'ok', 'text': message['content'], 'message': message, 'tool_calls': [],
                'returned_model': body['model'], 'inference_id': 'gen-' + str(len(self.requests)),
                'usage': {'prompt_tokens': 100, 'completion_tokens': 120, 'total_tokens': 220, 'cost': 0.001},
                'elapsed_seconds': 0.05, 'error': None,
                'raw': {'id': 'gen-' + str(len(self.requests)), 'model': body['model'], 'message': message}}

    def run_task(self, provider=None):
        with patch.object(tasks.talk, 'complete', side_effect=provider or self.provider):
            return tasks.run_task(self.repo, self.config, self.packet, 'fixture-private-key')

    def capped_provider(self, *args):
        # Synthetic completion-cap failure, not a copied live response.
        result = self.provider(*args)
        result.update(status='error', text=None, message=None, finish_reason='length',
                      error={'type': 'ValueError', 'message': 'No final content'},
                      usage={'prompt_tokens': 100, 'completion_tokens': 2048,
                             'total_tokens': 2148, 'cost': '0.000369954',
                             'completion_tokens_details': {'reasoning_tokens': 2045}})
        result['raw'] = {'id': result['inference_id'], 'model': result['returned_model'],
                         'choices': [{'finish_reason': 'length',
                                      'message': {'role': 'assistant', 'content': ''}}],
                         'usage': result['usage']}
        return result

    def load(self, result):
        run = tasks.find_run(self.repo, result['run'])
        manifest, receipt = tasks.read_run(run)
        return run, manifest, receipt

    def test_successful_ticket_review_and_offline_decision_have_independent_states(self):
        result = self.run_task()
        run, manifest, receipt = self.load(result)
        self.assertEqual(result['status'], 'reviewed')
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(receipt['calls'][0]['identity_state'], 'exact')
        self.assertEqual(receipt['calls'][0]['generation_id'], 'gen-1')
        self.assertEqual(receipt['artifact_hashes']['worker.json'], manifest['files']['worker.json'])
        self.assertTrue(receipt['schema_valid'])
        self.assertEqual(receipt['reviewer_verdict'], 'pass')
        self.assertEqual(receipt['human_acceptance'], 'not_recorded')
        worker_request, review_request = [json.loads(request['messages'][1]['content']) for request in self.requests]
        self.assertEqual(worker_request['packet'], review_request['packet'])
        self.assertEqual(tasks.digest(review_request['worker']), review_request['worker_sha256'])
        source_before = (self.repo / 'castle/example.py').read_bytes()
        with patch.object(tasks.talk, 'complete', side_effect=AssertionError('Offline operation spent money')):
            exported = tasks.offline_operation(self.repo, result['run'], 'export-z')
            bundle = json.loads((run / 'z-review-packet.json').read_text())
            self.assertEqual(bundle['packet'], self.packet)
            self.assertEqual(tasks.digest(bundle['worker']), exported['worker_sha256'])
            accepted = tasks.offline_operation(self.repo, result['run'], 'accept', exported['worker_sha256'], 'Reviewed locally')
        self.assertEqual(accepted['report']['accepted_result_count'], 1)
        self.assertEqual(accepted['report']['total_recorded_spend_usd'], '0.002')
        self.assertEqual(accepted['report']['cost_per_accepted_result_usd'], '0.002')
        self.assertEqual(source_before, (self.repo / 'castle/example.py').read_bytes())

    def test_paid_opt_in_and_positive_budget_are_required_before_transport(self):
        self.config['worker_model'] = 'fixture/paid'
        with patch.object(tasks.talk, 'complete') as transport:
            with self.assertRaisesRegex(ValueError, 'allow_paid'):
                self.run_task()
            self.config.update(allow_paid=True, budget_usd='0')
            with self.assertRaisesRegex(ValueError, 'positive'):
                self.run_task()
        transport.assert_not_called()

    def test_omitted_reasoning_keeps_legacy_requests_and_plan(self):
        plan = tasks.plan(self.config, self.packet)
        for role in ('worker', 'reviewer'):
            self.assertNotIn('requested_reasoning_effort', plan['roles'][role])
        result = self.run_task()
        self.assertEqual(result['status'], 'reviewed')
        for request in self.requests:
            self.assertEqual(set(request), {'model', 'messages', 'stream', 'max_tokens',
                                            'response_format', 'provider'})

    def test_low_reasoning_is_shown_offline_and_durable_before_both_calls(self):
        self.config.update(reasoning_effort='low', max_completion_tokens=2048)
        config = self.repo / 'config.json'
        config.write_text(json.dumps(self.config))
        with patch.object(tasks, 'REPO', self.repo), \
                patch.object(tasks, 'base_commit', return_value='a' * 40), \
                patch.object(tasks.talk, 'obtain_key', side_effect=AssertionError('No key prompt')), \
                patch.object(tasks.talk, 'complete', side_effect=AssertionError('No inference')), \
                patch('sys.stdout', new=io.StringIO()) as output:
            self.assertEqual(tasks.main(['dry-run', '--config', str(config)]), 0)
            plan = json.loads(output.getvalue())
        self.assertFalse(tasks.runs_root(self.repo).exists())
        for role in ('worker', 'reviewer'):
            self.assertEqual(plan['roles'][role]['requested_reasoning_effort'], 'low')

        def inspect_durable_request(*args):
            run = next(path for path in (tasks.runs_root(self.repo) / 'fixture-task').iterdir()
                       if path.is_dir())
            _, receipt = tasks.read_run(run)
            self.assertEqual(receipt['status'], 'in_flight')
            self.assertEqual(receipt['calls'][-1]['request'], args[2])
            return self.provider(*args)

        result = self.run_task(inspect_durable_request)
        run, _, receipt = self.load(result)
        self.assertEqual(result['status'], 'reviewed')
        self.assertEqual(len(self.requests), 2)
        for request, call in zip(self.requests, receipt['calls']):
            self.assertEqual(request['reasoning'], {'effort': 'low'})
            self.assertEqual(call['request'], request)
            self.assertEqual(request['max_tokens'], 2048)
            self.assertEqual(request['response_format'], {'type': 'json_object'})
            self.assertEqual(request['provider'], {'allow_fallbacks': False, 'require_parameters': True})
            self.assertNotIn('reasoning_effort', request)
        self.assertEqual(json.loads((run / 'plan.json').read_text())['roles'], plan['roles'])
        self.assertEqual(tasks.digest(self.packet), result['packet_sha256'])
        self.assertEqual(receipt['human_acceptance'], 'not_recorded')

    def test_invalid_reasoning_opt_ins_are_rejected_before_transport(self):
        for value in (None, '', False, True, 0, [], {}, 'LOW', 'medium', 'high', 'none'):
            with self.subTest(value=value):
                config = copy.deepcopy(self.config)
                config['reasoning_effort'] = value
                with patch.object(tasks.talk, 'complete') as transport:
                    with self.assertRaisesRegex(ValueError, 'reasoning_effort'):
                        tasks.run_task(self.repo, config, self.packet, 'fixture-private-key')
                transport.assert_not_called()
        config = dict(self.config, reasoning={'effort': 'low', 'exclude': True})
        with self.assertRaisesRegex(ValueError, 'fields'):
            tasks.validate_config(config)
        self.assertFalse(tasks.runs_root(self.repo).exists())

    def test_low_reasoning_cap_failure_is_charged_without_retry_or_review(self):
        self.config.update(reasoning_effort='low', max_completion_tokens=2048)
        result = self.run_task(self.capped_provider)
        _, manifest, receipt = self.load(result)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['report']['total_recorded_spend_usd'], '0.000369954')
        self.assertTrue(result['report']['accounting_complete'])
        self.assertFalse(receipt['schema_valid'])
        self.assertNotIn('worker.json', manifest['files'])
        self.assertIsNone(receipt['reviewer_verdict'])
        call = receipt['calls'][0]
        self.assertEqual(call['request']['reasoning'], {'effort': 'low'})
        self.assertEqual(call['response']['raw']['choices'][0]['finish_reason'], 'length')
        self.assertEqual(call['usage']['completion_tokens_details']['reasoning_tokens'], 2045)

    def test_reasoning_opt_in_keeps_prior_failed_charge_and_budget_gate(self):
        self.config.update(budget_usd='0.05', max_completion_tokens=2048)
        for price in self.config['pricing'].values():
            price.update(input_usd_per_million='0.075', output_usd_per_million='0.3')
        result = self.run_task(self.capped_provider)
        run, _, _ = self.load(result)
        original = {path.name: path.read_bytes() for path in run.iterdir()}
        self.config['reasoning_effort'] = 'low'
        prior = tasks.report(self.repo, self.packet['task_id'])
        plan = tasks.plan(self.config, self.packet, prior)
        self.assertTrue(plan['can_run'])
        self.assertEqual(plan['prior_task_accounting']['total_recorded_spend_usd'], '0.000369954')
        # Reserve exactly the new estimate: it only fits if the old charge is lost.
        self.config['budget_usd'] = plan['estimated_total_usd']
        self.assertGreater(Decimal(plan['estimated_total_usd']) + Decimal('0.000369954'),
                           Decimal(self.config['budget_usd']))
        self.assertFalse(tasks.plan(self.config, self.packet, prior)['can_run'])
        with patch.object(tasks.talk, 'complete') as transport:
            with self.assertRaisesRegex(ValueError, 'budget'):
                tasks.run_task(self.repo, self.config, self.packet, 'fixture-private-key')
        transport.assert_not_called()
        self.assertEqual(tasks.report(self.repo, self.packet['task_id'])['attempts'], 1)
        self.assertEqual({path.name: path.read_bytes() for path in run.iterdir()}, original)

    def test_unsupported_reasoning_response_stops_without_fallback_or_retry(self):
        self.config['reasoning_effort'] = 'low'
        def unsupported(*args):
            result = self.provider(*args)
            result.update(status='error', usage=None,
                          error={'type': 'HTTPError', 'message': 'Unsupported reasoning parameter'},
                          raw={'error': {'code': 400, 'message': 'Unsupported reasoning parameter'}})
            return result
        result = self.run_task(unsupported)
        _, _, receipt = self.load(result)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(receipt['calls'][0]['request']['reasoning'], {'effort': 'low'})
        self.assertFalse(result['report']['accounting_complete'])
        self.assertEqual(receipt['calls'][0]['response']['raw']['error']['code'], 400)
        with self.assertRaisesRegex(ValueError, 'Prior attempt accounting'):
            self.run_task()
        self.assertEqual(len(self.requests), 1)

    def test_budget_exhaustion_stops_after_worker_and_counts_reported_charge(self):
        self.config['budget_usd'] = '0.0005'
        result = self.run_task()
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['report']['total_recorded_spend_usd'], '0.001')
        self.assertIsNone(result['report']['cost_per_accepted_result_usd'])

    def test_previous_attempt_costs_share_task_budget(self):
        self.run_task()
        self.config['budget_usd'] = '0.0015'
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.run_task()
        self.assertEqual(len(self.requests), 2)

    def test_missing_accounting_blocks_reviewer_and_future_attempt(self):
        for missing in ('cost', 'total_tokens'):
            with self.subTest(missing=missing):
                self.config['task']['task_id'] = 'missing-' + missing
                self.packet = self.freeze()
                self.requests.clear()
                def incomplete(*args):
                    result = self.provider(*args)
                    del result['usage'][missing]
                    return result
                result = self.run_task(incomplete)
                self.assertEqual(len(self.requests), 1)
                self.assertFalse(result['report']['accounting_complete'])
                self.assertEqual(result['status'], 'failed')
                with self.assertRaisesRegex(ValueError, 'Prior attempt accounting'):
                    self.run_task()

    def test_malformed_worker_retains_native_evidence_without_review(self):
        def malformed(*args):
            result = self.provider(*args)
            result['text'] = '{not-json'
            result['raw']['native_extra'] = 'retained'
            return result
        result = self.run_task(malformed)
        run, manifest, receipt = self.load(result)
        self.assertEqual(len(self.requests), 1)
        self.assertNotIn('worker.json', manifest['files'])
        self.assertEqual(receipt['calls'][0]['response']['raw']['native_extra'], 'retained')
        self.assertEqual(result['report']['total_recorded_spend_usd'], '0.001')

    def test_unknown_source_reference_and_wrong_packet_hash_are_rejected(self):
        for wrong in ('source', 'hash'):
            ticket = self.ticket()
            if wrong == 'source':
                ticket['source_refs'][0]['path'] = 'castle/not-supplied.py'
            else:
                ticket['packet_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                tasks.validate_output(ticket, 'worker', self.packet)

    def test_reviewer_verdict_is_separate_from_human_acceptance(self):
        def reviewer(*args):
            result = self.provider(*args)
            if len(self.requests) == 2:
                review = json.loads(result['text'])
                review['verdict'] = 'needs_changes'
                result['text'] = json.dumps(review)
            return result
        result = self.run_task(reviewer)
        _, manifest, receipt = self.load(result)
        self.assertEqual(receipt['reviewer_verdict'], 'needs_changes')
        self.assertEqual(receipt['human_acceptance'], 'not_recorded')
        rejected = tasks.offline_operation(self.repo, result['run'], 'reject', manifest['files']['worker.json'])
        self.assertEqual(rejected['report']['accepted_result_count'], 0)
        self.assertEqual(rejected['report']['ratio_reason'], 'No accepted results')

    def test_reviewer_must_bind_exact_worker_hash(self):
        def wrong_hash(*args):
            result = self.provider(*args)
            if len(self.requests) == 2:
                review = json.loads(result['text'])
                review['worker_sha256'] = '0' * 64
                result['text'] = json.dumps(review)
            return result
        result = self.run_task(wrong_hash)
        _, manifest, receipt = self.load(result)
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn('review.json', manifest['files'])
        self.assertIsNone(receipt['reviewer_verdict'])

    def test_identity_changes_or_unreported_identity_stop_spending(self):
        for returned in ('fixture/substitute:free', None):
            self.config['task']['task_id'] = 'identity-' + ('missing' if returned is None else 'alias')
            self.packet = self.freeze()
            self.requests.clear()
            def substitute(*args):
                result = self.provider(*args)
                result['returned_model'] = returned
                return result
            result = self.run_task(substitute)
            _, _, receipt = self.load(result)
            self.assertEqual(len(self.requests), 1)
            self.assertEqual(receipt['calls'][0]['identity_state'], 'unreported' if returned is None else 'alias_review')
            self.assertEqual(result['status'], 'failed')

    def test_stop_before_worker_and_between_calls(self):
        stop = self.repo / 'STOP'
        stop.touch()
        result = self.run_task()
        self.assertEqual(self.requests, [])
        self.assertEqual(result['status'], 'stopped')
        stop.unlink()
        def stop_after_worker(*args):
            result = self.provider(*args)
            stop.touch()
            return result
        result = self.run_task(stop_after_worker)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result['status'], 'stopped')
        self.assertTrue(result['report']['accounting_complete'])

    def test_known_and_recognizable_credential_echoes_are_redacted(self):
        for secret in ('fixture-private-key', 'sk-or-v1-' + 'test-secret-123',
                       '-----BEGIN PRIVATE KEY-----\nnot-a-real-private-key\n-----END PRIVATE KEY-----'):
            self.config['task']['task_id'] = 'echo-' + str(len(self.requests))
            self.packet = self.freeze()
            before = len(self.requests)
            def echo(*args):
                result = self.provider(*args)
                result['raw']['echo'] = secret
                return result
            result = self.run_task(echo)
            run, manifest, receipt = self.load(result)
            self.assertEqual(len(self.requests) - before, 1)
            self.assertTrue(receipt['calls'][0]['credential_redacted'])
            self.assertNotIn(secret, (run / 'receipt.json').read_text())
            self.assertNotIn('worker.json', manifest['files'])

    def test_packet_hash_is_frozen_and_content_sensitive(self):
        self.assertEqual(tasks.digest(self.packet), tasks.digest(self.freeze()))
        (self.repo / 'castle/example.py').write_text('changed\n')
        self.assertNotEqual(tasks.digest(self.packet), tasks.digest(self.freeze()))
        self.assertEqual(self.packet['sources'][0]['content'], 'def greet():\n    return "hello"\n')

    def test_frozen_sources_preserve_crlf_bytes(self):
        raw = b'def greet():\r\n    return "hello"\r\n'
        (self.repo / 'castle/example.py').write_bytes(raw)
        frozen = self.freeze()
        source = frozen['sources'][0]
        self.assertEqual(source['content'], raw.decode('utf-8'))
        self.assertEqual(source['byte_length'], len(raw))
        self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertNotEqual(source['sha256'], self.packet['sources'][0]['sha256'])
        self.assertNotEqual(tasks.digest(frozen), tasks.digest(self.packet))

    def test_line_counts_match_validator_without_normalizing_source_bytes(self):
        cases = [(b'', 0), (b'one', 1), (b'one\n', 1), (b'one\n\n', 2),
                 (b'one\r\ntwo\r\n', 2), ('\u03b1\u2028\u03b2\r\n\u03b3'.encode('utf-8'), 3)]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                path = self.repo / 'castle/example.py'
                path.write_bytes(raw)
                packet = self.freeze()
                source = packet['sources'][0]
                self.assertEqual(source['line_count'], expected)
                self.assertEqual(source['content'], raw.decode('utf-8'))
                self.assertEqual(source['byte_length'], len(raw))
                self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(path.read_bytes(), raw)
                ref = {'path': source['path'], 'start_line': 1, 'end_line': expected}
                if expected:
                    tasks.validate_refs([ref], packet)
                ref['end_line'] = expected + 1
                with self.assertRaisesRegex(ValueError, 'line range'):
                    tasks.validate_refs([ref], packet)

    def test_both_roles_receive_required_field_and_line_unit_guidance_once(self):
        result = self.run_task()
        self.assertEqual(result['status'], 'reviewed')
        self.assertEqual(len(self.requests), 2)
        for request in self.requests:
            system = request['messages'][0]['content']
            self.assertIn('Every field in this contract, including nested fields, must be present', system)
            self.assertIn('"uncertainties": []', system)
            self.assertIn('1-based inclusive line ranges within line_count', system)
            self.assertIn('str.splitlines()', system)
            self.assertIn('byte_length is file size in bytes, never a citation boundary', system)
            payload = json.loads(request['messages'][1]['content'])
            self.assertEqual(payload['packet'], self.packet)
            self.assertEqual(payload['packet_sha256'], tasks.digest(self.packet))
            self.assertEqual(len(payload['packet']['sources']), 1)
            source = payload['packet']['sources'][0]
            self.assertEqual(set(source), {'path', 'sha256', 'byte_length', 'line_count', 'content'})
            self.assertEqual(source['line_count'], 2)
            # The packet holds one original content string, without numbered copies.
            self.assertEqual(source['content'], (self.repo / source['path']).read_bytes().decode('utf-8'))
            self.assertEqual(set(payload), {'packet', 'packet_sha256'} if request is self.requests[0]
                             else {'packet', 'packet_sha256', 'worker', 'worker_sha256'})
        worker_system = self.requests[0]['messages'][0]['content']
        self.assertIn('check existing handling in the supplied sources', worker_system)
        self.assertIn('remaining concrete failure path', worker_system)
        self.assertIn('existence precheck alone does not fix a file disappearance race', worker_system)

    def test_missing_uncertainties_is_rejected_in_both_roles_without_filling(self):
        for role in ('worker', 'reviewer'):
            with self.subTest(role=role):
                self.config['task']['task_id'] = 'missing-uncertainties-' + role
                self.packet = self.freeze()
                self.requests.clear()
                target_call = 1 if role == 'worker' else 2
                def missing(*args):
                    response = self.provider(*args)
                    if len(self.requests) == target_call:
                        value = json.loads(response['text'])
                        del value['uncertainties']
                        response['text'] = json.dumps(value)
                        response['message']['content'] = response['text']
                    return response
                result = self.run_task(missing)
                run, manifest, receipt = self.load(result)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(len(self.requests), target_call)
                rejected = receipt['calls'][-1]['response']
                self.assertNotIn('uncertainties', json.loads(rejected['text']))
                self.assertEqual(rejected['raw']['message']['content'], rejected['text'])
                self.assertNotIn('worker.json' if role == 'worker' else 'review.json', manifest['files'])
                self.assertFalse((run / 'decision.json').exists())
                self.assertTrue(result['report']['accounting_complete'])
                self.assertEqual(result['report']['total_recorded_spend_usd'],
                                 '0.001' if role == 'worker' else '0.002')
                self.assertIsNone(receipt['reviewer_verdict'])
                self.assertEqual(receipt['human_acceptance'], 'not_recorded')

    def test_all_advertised_output_list_bounds_match_validation(self):
        worker = self.ticket()
        review = {'schema_version': 'castle-task-review/0.1',
                  'packet_sha256': tasks.digest(self.packet), 'worker_sha256': tasks.digest(worker),
                  'verdict': 'blocked', 'reasons': [{'note': 'More evidence is needed.',
                      'source_refs': worker['source_refs']}], 'uncertainties': []}
        for role, original in (('worker', worker), ('reviewer', review)):
            system = tasks.messages_for(role, self.packet, worker if role == 'reviewer' else None)[0]['content']
            self.assertIn(json.dumps(tasks.OUTPUT_LIST_BOUNDS[role]), system)
            for path, (minimum, maximum) in tasks.OUTPUT_LIST_BOUNDS[role].items():
                counts = {minimum, maximum, maximum + 1}
                if minimum:
                    counts.add(minimum - 1)
                for count in counts:
                    with self.subTest(role=role, path=path, count=count):
                        value = copy.deepcopy(original)
                        container = value['reasons'][0] if path == 'reasons[].source_refs' else value
                        key = path.split('.')[-1]
                        seed = container[key][0] if container[key] else 'Unresolved synthetic question.'
                        container[key] = [copy.deepcopy(seed) for _ in range(count)]
                        if minimum <= count <= maximum:
                            tasks.validate_output(value, role, self.packet, worker)
                        else:
                            with self.assertRaises(ValueError):
                                tasks.validate_output(value, role, self.packet, worker)

    def test_all_documented_task_list_bounds_match_packet_freezing(self):
        names = ['castle/example.py'] + ['castle/example%d.py' % i for i in range(1, 9)]
        for name in names[1:]:
            (self.repo / name).write_bytes(b'# Synthetic offline source.\n')
        for field in ('acceptance_criteria', 'boundaries', 'source_files', 'allowed_files'):
            for count in (0, 1, 8, 9):
                with self.subTest(field=field, count=count):
                    task = copy.deepcopy(self.config['task'])
                    task['source_files'] = names[:8]
                    task[field] = (names[:count] if field.endswith('files') else ['Proposed check.'] * count)
                    if 1 <= count <= 8:
                        frozen = tasks.freeze_packet(self.repo, task, 'a' * 40)
                        key = 'sources' if field == 'source_files' else field
                        self.assertEqual(len(frozen[key]), count)
                    else:
                        with self.assertRaisesRegex(ValueError, 'List length'):
                            tasks.freeze_packet(self.repo, task, 'a' * 40)

    def test_no_repair_and_insufficient_evidence_still_require_proposed_checks(self):
        for conclusion in ('No repair is established by these sources.',
                           'Evidence is insufficient to establish a gap.'):
            for empty in (False, True):
                with self.subTest(conclusion=conclusion, empty=empty):
                    self.config['task']['task_id'] = 'conclusion-%d-%s' % (len(conclusion), empty)
                    self.packet = self.freeze()
                    self.requests.clear()
                    def conclude(*args):
                        response = self.provider(*args)
                        value = json.loads(response['text'])
                        if len(self.requests) == 1:
                            value.update(problem=conclusion, proposed_change='No edits proposed; verify existing handling.',
                                         acceptance_checks=[] if empty else ['Check the existing greeting result.'],
                                         uncertainties=['No execution evidence is supplied.'])
                        else:
                            value.update(verdict='blocked', reasons=[{
                                'note': 'The proposed check needs execution evidence.',
                                'source_refs': self.ticket()['source_refs']}])
                        response['text'] = json.dumps(value)
                        response['message']['content'] = response['text']
                        return response
                    result = self.run_task(conclude)
                    run, manifest, receipt = self.load(result)
                    self.assertEqual(result['status'], 'failed' if empty else 'reviewed')
                    self.assertEqual(len(self.requests), 1 if empty else 2)
                    response = receipt['calls'][0]['response']
                    output = json.loads(response['text'])
                    self.assertEqual(output['problem'], conclusion)
                    self.assertEqual(response['raw']['message']['content'], response['text'])
                    self.assertEqual('worker.json' in manifest['files'], not empty)
                    self.assertEqual(receipt['reviewer_verdict'], None if empty else 'blocked')
                    self.assertEqual(result['report']['total_recorded_spend_usd'], '0.001' if empty else '0.002')
                    self.assertTrue(result['report']['accounting_complete'])
                    self.assertEqual(result['report']['accepted_result_count'], 0)
                    self.assertEqual(receipt['human_acceptance'], 'not_recorded')
                    self.assertFalse((run / 'decision.json').exists())

    def test_overfull_output_lists_fail_without_retry_or_evidence_repair(self):
        for role, bounds in tasks.OUTPUT_LIST_BOUNDS.items():
            for path, (_, maximum) in bounds.items():
                with self.subTest(role=role, path=path):
                    self.config['task']['task_id'] = 'overfull-' + role + '-' + path.replace('[].', '-')
                    self.packet = self.freeze()
                    self.requests.clear()
                    target = 1 if role == 'worker' else 2
                    def overfull(*args):
                        response = self.provider(*args)
                        if len(self.requests) == target:
                            value = json.loads(response['text'])
                            container = value['reasons'][0] if path == 'reasons[].source_refs' else value
                            key = path.split('.')[-1]
                            seed = container[key][0] if container[key] else 'Synthetic uncertainty.'
                            container[key] = [copy.deepcopy(seed) for _ in range(maximum + 1)]
                            response['text'] = json.dumps(value)
                            response['message']['content'] = response['text']
                        return response
                    result = self.run_task(overfull)
                    run, manifest, receipt = self.load(result)
                    self.assertEqual(result['status'], 'failed')
                    self.assertEqual(len(self.requests), target)
                    response = receipt['calls'][-1]['response']
                    rejected = json.loads(response['text'])
                    container = rejected['reasons'][0] if path == 'reasons[].source_refs' else rejected
                    self.assertEqual(len(container[path.split('.')[-1]]), maximum + 1)
                    self.assertEqual(response['raw']['message']['content'], response['text'])
                    self.assertNotIn('worker.json' if role == 'worker' else 'review.json', manifest['files'])
                    self.assertTrue(result['report']['accounting_complete'])
                    self.assertEqual(result['report']['total_recorded_spend_usd'], '0.001' if target == 1 else '0.002')
                    self.assertEqual(receipt['human_acceptance'], 'not_recorded')
                    self.assertFalse((run / 'decision.json').exists())

    def test_focused_config_credits_host_finding_and_preserves_task_controls(self):
        root = Path(__file__).resolve().parents[1]
        directory = root / 'specs/tasks'
        previous = json.loads((directory / 'room-registry-ticket-paid-gpt-oss-20b-low-reasoning.json').read_text())
        focused = json.loads((directory / 'room-registry-enumeration-ticket-paid-gpt-oss-20b-low-reasoning.json').read_text())
        tasks.validate_config(focused)
        self.assertEqual({k: v for k, v in focused.items() if k != 'task'},
                         {k: v for k, v in previous.items() if k != 'task'})
        for field in ('task_id', 'boundaries', 'source_files', 'allowed_files'):
            self.assertEqual(focused['task'][field], previous['task'][field])
        frozen = tasks.freeze_packet(root, focused['task'], 'a' * 40)
        self.assertIn('Host finding (Codex synthetic offline probe, not a worker discovery)', frozen['goal'])
        self.assertIn('resolved.stat()', frozen['goal'])
        self.assertIn('before its read-time try/except', frozen['goal'])
        self.assertIn('host finding', ' '.join(frozen['acceptance_criteria']))
        for source in frozen['sources']:
            self.assertEqual(source['sha256'], hashlib.sha256((root / source['path']).read_bytes()).hexdigest())

    def test_host_enumeration_gap_fixture_distinguishes_read_time_handling(self):
        # Host/Codex synthetic finding: enumeration previously escaped. Keep the
        # original injection proof as a handled-result regression, not a worker discovery.
        rooms = self.repo / 'rooms'
        rooms.mkdir()
        # Exercise an alias on every host, including Linux, rather than relying
        # on a hosted Windows temp directory to happen to contain one.
        alias = self.repo / 'room-alias'
        alias.symlink_to(rooms, target_is_directory=True)
        rooms = alias
        target = rooms / 'courtyard.json'
        target.write_bytes(b'{"id":"courtyard"}\n')
        # Windows temp roots can contain an 8.3 alias or junction; room_paths
        # uses resolved paths, so match that same identity before patching.
        target = target.resolve()
        original_stat = Path.stat
        original_is_file = Path.is_file
        original_bytes = target.read_bytes()
        for error in (FileNotFoundError, PermissionError, OSError):
            with self.subTest(error=error.__name__):
                state = {'armed': False, 'is_file_results': [], 'failures': 0}
                def existing(path):
                    result = original_is_file(path)
                    if path == target:
                        state['is_file_results'].append(result)
                        state['armed'] = result
                    return result
                def disappearing(path, *args, **kwargs):
                    # Path.resolve may stat on some Python/platform versions.
                    # Arm only after the real is_file check has returned true.
                    if path == target and state['armed']:
                        state['failures'] += 1
                        raise error('Synthetic enumeration size-stat failure')
                    return original_stat(path, *args, **kwargs)
                with patch.object(Path, 'stat', disappearing), patch.object(Path, 'is_file', existing):
                    result = tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)
                self.assertEqual(result, {'ok': False, 'data': None, 'error': {
                    'code': 'unknown_room', 'message': 'Unknown Castle room ID.', 'available_rooms': []}})
                self.assertEqual(state['is_file_results'], [True])
                self.assertEqual(state['failures'], 1)
                with patch.object(Path, 'read_text', side_effect=error('Synthetic read-time failure')):
                    result = tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)
                self.assertFalse(result['ok'])
                self.assertEqual(result['error']['code'], 'room_read_failed')
                self.assertEqual(result['error']['message'], error.__name__)
        self.assertTrue(tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)['ok'])
        self.assertEqual(target.read_bytes(), original_bytes)

    def test_byte_length_citation_is_rejected_without_clipping_or_trusting_metadata(self):
        # Synthetic source with the observed 125-line/4842-byte shape.
        raw = b'x' * 4717 + b'\n' * 125
        (self.repo / 'castle/example.py').write_bytes(raw)
        self.packet = self.freeze()
        source = self.packet['sources'][0]
        self.assertEqual((source['line_count'], source['byte_length']), (125, 4842))
        valid = self.ticket()
        self.assertEqual(valid['uncertainties'], [])
        valid['source_refs'][0]['end_line'] = 125
        tasks.validate_output(valid, 'worker', self.packet)
        forged = copy.deepcopy(self.packet)
        forged['sources'][0]['line_count'] = 4842
        ref = dict(valid['source_refs'][0], end_line=4842)
        with self.assertRaisesRegex(ValueError, 'line range'):
            tasks.validate_refs([ref], forged)
        def byte_boundary(*args):
            response = self.provider(*args)
            value = json.loads(response['text'])
            value['source_refs'][0]['end_line'] = 4842
            response['text'] = json.dumps(value)
            response['message']['content'] = response['text']
            return response
        result = self.run_task(byte_boundary)
        _, manifest, receipt = self.load(result)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(len(self.requests), 1)
        self.assertFalse(receipt['schema_valid'])
        self.assertNotIn('worker.json', manifest['files'])
        rejected = json.loads(receipt['calls'][0]['response']['text'])
        self.assertEqual(rejected['source_refs'][0]['end_line'], 4842)
        self.assertEqual(result['report']['total_recorded_spend_usd'], '0.001')
        self.assertEqual((self.repo / 'castle/example.py').read_bytes(), raw)

    def test_legacy_packet_without_line_count_still_validates_and_exports_unchanged(self):
        self.packet = copy.deepcopy(self.packet)
        del self.packet['sources'][0]['line_count']
        expected_hash = tasks.digest(self.packet)
        result = self.run_task()
        run, _, _ = self.load(result)
        self.assertEqual(result['status'], 'reviewed')
        original = (run / 'packet.json').read_bytes()
        with patch.object(tasks.talk, 'complete', side_effect=AssertionError('Offline export inferred')):
            tasks.offline_operation(self.repo, result['run'], 'export-z')
        bundle = json.loads((run / 'z-review-packet.json').read_text())
        self.assertNotIn('line_count', bundle['packet']['sources'][0])
        self.assertEqual(bundle['packet_sha256'], expected_hash)
        self.assertEqual((run / 'packet.json').read_bytes(), original)
        self.assertEqual(hashlib.sha256(original).hexdigest(), expected_hash)

    def test_path_boundaries_block_escape_secret_files_symlinks_and_sizes(self):
        outside = self.repo.parent / ('outside-' + self.repo.name + '.txt')
        outside.write_text('outside\n')
        self.addCleanup(outside.unlink)
        (self.repo / 'castle/escape.txt').symlink_to(outside)
        (self.repo / '.env').write_text('private\n')
        (self.repo / 'castle/alias.txt').symlink_to(self.repo / '.env')
        (self.repo / 'castle/huge.txt').write_bytes(b'a' * (tasks.MAX_FILE_BYTES + 1))
        for name in ('../outside.txt', str(outside), '.env', '.talk-runs/result.jsonl',
                     '.task-runs/packet.json', 'castle/escape.txt', 'castle/alias.txt',
                     'castle/huge.txt', 'castle/credentials.txt', 'C:\\secret.txt'):
            with self.subTest(name=name):
                self.config['task']['source_files'] = [name]
                self.config['task']['allowed_files'] = [name]
                with self.assertRaises(ValueError):
                    self.freeze()

    def test_secrets_in_sources_are_not_frozen(self):
        (self.repo / 'castle/example.py').write_text('key="sk-or-v1-' + 'not-a-real-token"\n')
        with self.assertRaisesRegex(ValueError, 'Secret-like'):
            self.freeze()

    def test_interrupted_request_is_discoverable_and_cannot_be_repeated(self):
        with patch.object(tasks.talk, 'complete', side_effect=KeyboardInterrupt):
            result = tasks.run_task(self.repo, self.config, self.packet, 'fixture-private-key')
        run, manifest, receipt = self.load(result)
        self.assertTrue((run / 'packet.json').exists())
        self.assertEqual(manifest['state'], 'interrupted')
        self.assertFalse(result['report']['accounting_complete'])
        self.assertIsNone(receipt['calls'][0]['reported_cost_usd'])
        with self.assertRaisesRegex(ValueError, 'Prior attempt accounting'):
            self.run_task()

    def test_human_decision_must_match_hash_and_cannot_overwrite(self):
        result = self.run_task()
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            tasks.offline_operation(self.repo, result['run'], 'accept', '0' * 64)
        _, manifest, _ = self.load(result)
        expected = manifest['files']['worker.json']
        tasks.offline_operation(self.repo, result['run'], 'reject', expected)
        with self.assertRaises(FileExistsError):
            tasks.offline_operation(self.repo, result['run'], 'accept', expected)

    def test_artifact_tampering_prevents_acceptance(self):
        result = self.run_task()
        run, manifest, _ = self.load(result)
        (run / 'worker.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Artifact hash mismatch'):
            tasks.offline_operation(self.repo, result['run'], 'accept', manifest['files']['worker.json'])
        self.assertFalse(tasks.report(self.repo)['accounting_complete'])

    def test_rejected_and_failed_attempts_stay_in_accepted_result_cost(self):
        rejected = self.run_task()
        _, manifest, _ = self.load(rejected)
        tasks.offline_operation(self.repo, rejected['run'], 'reject', manifest['files']['worker.json'])
        def failed(*args):
            result = self.provider(*args)
            result['text'] = 'not JSON'
            return result
        self.run_task(failed)
        accepted = self.run_task()
        _, manifest, _ = self.load(accepted)
        tasks.offline_operation(self.repo, accepted['run'], 'accept', manifest['files']['worker.json'])
        stats = tasks.report(self.repo)
        self.assertEqual(stats['attempts'], 3)
        self.assertEqual(stats['total_recorded_spend_usd'], '0.005')
        self.assertEqual(stats['cost_per_accepted_result_usd'], '0.005')

    def test_missing_stale_and_expensive_pricing_never_silently_becomes_zero(self):
        self.config['pricing'].clear()
        self.assertIsNone(tasks.plan(self.config, self.packet)['estimated_total_usd'])
        self.assertFalse(tasks.plan(self.config, self.packet)['can_run'])
        for role in ('worker', 'reviewer'):
            self.config['pricing'][self.config[role + '_model']] = {
                'observed_on': (datetime.now(timezone.utc).date() - timedelta(days=8)).isoformat(),
                'source': 'Stale fixture', 'input_usd_per_million': '100', 'output_usd_per_million': '100'}
        self.assertFalse(tasks.plan(self.config, self.packet)['can_run'])
        for price in self.config['pricing'].values():
            price['observed_on'] = datetime.now(timezone.utc).date().isoformat()
        self.assertFalse(tasks.plan(self.config, self.packet)['can_run'])

    def test_dry_run_and_report_do_not_prompt_or_infer(self):
        config = self.repo / 'config.json'
        config.write_text(json.dumps(self.config))
        with patch.object(tasks, 'REPO', self.repo), patch.object(tasks, 'base_commit', return_value='a' * 40), \
                patch.object(tasks.talk, 'obtain_key', side_effect=AssertionError('No key prompt allowed')), \
                patch.object(tasks.talk, 'complete', side_effect=AssertionError('No inference allowed')), \
                patch('sys.stdout', new=io.StringIO()) as output:
            self.assertEqual(tasks.main(['dry-run', '--config', str(config)]), 0)
            result = json.loads(output.getvalue())
        self.assertTrue(result['can_run'])
        self.assertEqual(result['max_calls'], 2)
        self.assertFalse((self.repo / '.task-runs').exists())

    def test_paid_configuration_uses_exact_ids_without_model_fallback_or_tools(self):
        self.config['allow_paid'] = True
        for role in ('worker', 'reviewer'):
            old = self.config[role + '_model']
            new = old.removesuffix(':free')
            self.config[role + '_model'] = new
            self.config['pricing'][new] = self.config['pricing'].pop(old)
        self.run_task()
        self.assertEqual([body['model'] for body in self.requests], ['fixture/worker', 'fixture/reviewer'])
        for body in self.requests:
            self.assertEqual(body['max_tokens'], 1200)
            self.assertFalse(body['provider']['allow_fallbacks'])
            self.assertNotIn('tools', body)
            self.assertNotIn('models', body)
        for router in ('openrouter/free', 'openrouter/auto'):
            self.config['worker_model'] = router
            with self.assertRaisesRegex(ValueError, 'named models'):
                tasks.validate_config(self.config)

    def test_actual_review_reservation_can_block_second_call(self):
        model = self.config['reviewer_model']
        self.config['pricing'][model]['input_usd_per_million'] = '1'
        self.config['budget_usd'] = '0.11'
        self.assertTrue(tasks.plan(self.config, self.packet)['can_run'])
        def expensive_worker(*args):
            result = self.provider(*args)
            result['usage']['cost'] = 0.1099
            return result
        result = self.run_task(expensive_worker)
        self.assertEqual(len(self.requests), 1)
        self.assertIn('budget', self.load(result)[2]['error']['message'])

    def test_declared_input_limits_reject_excessive_selected_sources(self):
        self.config['task']['source_files'] = ['castle/example.py'] * 9
        with self.assertRaises(ValueError):
            self.freeze()
        names = []
        for index in range(4):
            name = f'castle/source{index}.txt'
            (self.repo / name).write_bytes(b'a' * tasks.MAX_FILE_BYTES)
            names.append(name)
        self.config['task']['source_files'] = names
        self.config['task']['allowed_files'] = names
        with self.assertRaisesRegex(ValueError, '96 KiB'):
            self.freeze()

    def test_hard_interruption_leaves_inflight_manifest_and_never_retries(self):
        def terminated(*args):
            runs = list((self.repo / '.task-runs/fixture-task').glob('*/manifest.json'))
            self.assertEqual(len(runs), 1)
            self.assertEqual(json.loads(runs[0].read_text())['state'], 'in_flight')
            raise SystemExit('Simulated process exit after submission')
        with self.assertRaises(SystemExit):
            self.run_task(terminated)
        self.assertFalse(tasks.report(self.repo)['accounting_complete'])
        with self.assertRaisesRegex(ValueError, 'Prior attempt accounting'):
            self.run_task()

    def test_transport_failure_is_one_attempt_without_retry(self):
        def failure(*args):
            result = self.provider(*args)
            result.update(status='error', usage=None,
                          error={'type': 'HTTPError', 'message': 'Fixture unavailable'})
            return result
        result = self.run_task(failure)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['report']['accounting_complete'])

    def test_malformed_tool_output_or_duplicate_fields_never_becomes_ticket(self):
        for error in ('tools', 'duplicate', 'missing_role'):
            self.config['task']['task_id'] = 'malformed-' + error
            self.packet = self.freeze()
            self.requests.clear()
            def malformed(*args):
                result = self.provider(*args)
                if error == 'tools':
                    result['tool_calls'] = [{'function': {'name': 'shell'}}]
                elif error == 'duplicate':
                    result['text'] = '{"problem":"one","problem":"two"}'
                else:
                    del result['message']['role']
                return result
            result = self.run_task(malformed)
            self.assertEqual(len(self.requests), 1)
            self.assertFalse(self.load(result)[2]['schema_valid'])

    def test_task_capitalization_preserves_packet_and_prior_budget(self):
        original_hash = tasks.digest(self.packet)
        self.run_task()
        self.config['task']['task_id'] = 'FIXTURE-TASK'
        self.config['budget_usd'] = '0.0015'
        self.packet = self.freeze()
        self.assertEqual(self.packet['task_id'], 'fixture-task')
        self.assertEqual(tasks.digest(self.packet), original_hash)
        self.assertEqual(tasks.report(self.repo, 'FIXTURE-TASK')['total_recorded_spend_usd'], '0.002')
        self.assertFalse(tasks.plan(self.config, self.packet,
                                   tasks.report(self.repo, 'FIXTURE-TASK'))['can_run'])
        before = len(self.requests)
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.run_task()
        self.assertEqual(len(self.requests), before)

    def test_legacy_mixed_case_directory_reuses_evidence_and_lock(self):
        result = self.run_task()
        run, manifest, _ = self.load(result)
        frozen = {name: (run / name).read_bytes() for name in manifest['files']}
        root = tasks.runs_root(self.repo)
        # Use a temporary name so this works on case-insensitive filesystems too.
        run.parent.rename(root / 'renaming-task')
        (root / 'renaming-task').rename(root / 'Fixture-Task')
        legacy_run = root / 'Fixture-Task' / run.name
        self.assertEqual(tasks.report(self.repo, 'FIXTURE-TASK')['total_recorded_spend_usd'], '0.002')
        self.config['budget_usd'] = '0.0015'
        before = len(self.requests)
        with self.assertRaisesRegex(ValueError, 'budget'):
            self.run_task()
        self.assertEqual(len(self.requests), before)
        self.assertEqual({name: (legacy_run / name).read_bytes() for name in frozen}, frozen)
        self.assertEqual(tasks.task_directory(self.repo, 'FIXTURE-TASK'), legacy_run.parent)
        with tasks.task_lock(legacy_run.parent):
            with self.assertRaisesRegex(ValueError, 'ledger lock'):
                tasks.offline_operation(self.repo, result['run'].upper().split('/')[0] + '/' + run.name,
                                        'accept', manifest['files']['worker.json'])
        accepted = tasks.offline_operation(self.repo, result['run'], 'accept',
                                          manifest['files']['worker.json'])
        self.assertEqual(accepted['report']['accepted_result_count'], 1)
        self.assertFalse((root / 'fixture-task').exists() and
                         (root / 'fixture-task').resolve() != legacy_run.parent.resolve())

    def test_ambiguous_task_directories_block_spending(self):
        self.run_task()
        root = tasks.runs_root(self.repo)
        lower, upper = root / 'fixture-task', root / 'FIXTURE-TASK'
        upper.mkdir(exist_ok=True)
        original_iterdir = Path.iterdir
        def aliases(path):
            # Duplicate case aliases are simulated on Windows, where a real
            # directory listing cannot contain both names as distinct entries.
            return iter([lower, upper]) if path == root else original_iterdir(path)
        before = len(self.requests)
        with patch.object(Path, 'iterdir', aliases):
            with self.assertRaisesRegex(ValueError, 'Ambiguous task directory'):
                tasks.report(self.repo)
            with self.assertRaisesRegex(ValueError, 'Ambiguous task directory'):
                self.run_task()
        self.assertEqual(len(self.requests), before)

    def test_active_run_refuses_offline_writers_without_losing_acceptance(self):
        original_save = tasks.save_state
        checked = False
        def interleave(run, receipt, manifest):
            nonlocal checked
            original_save(run, receipt, manifest)
            if not checked and 'worker.json' in manifest['files'] and len(receipt['calls']) == 1:
                checked = True
                name = run.relative_to(tasks.runs_root(self.repo)).as_posix()
                self.assertFalse(tasks.report(self.repo)['accounting_complete'])
                for operation in ('accept', 'reject', 'export-z'):
                    with self.assertRaisesRegex(ValueError, 'ledger lock'):
                        tasks.offline_operation(self.repo, name, operation,
                                                manifest['files']['worker.json'])
                    self.assertTrue((run.parent / '.active').exists())
                self.assertFalse((run / 'decision.json').exists())
                self.assertFalse((run / 'z-review-packet.json').exists())
        with patch.object(tasks, 'save_state', side_effect=interleave):
            result = self.run_task()
        self.assertTrue(checked)
        run, manifest, receipt = self.load(result)
        self.assertEqual(receipt['human_acceptance'], 'not_recorded')
        accepted = tasks.offline_operation(self.repo, result['run'], 'accept',
                                          manifest['files']['worker.json'])
        self.assertEqual(accepted['report']['accepted_result_count'], 1)
        self.assertEqual(self.load(result)[2]['human_acceptance'], 'accept')

    def test_overlapping_offline_export_cannot_discard_human_decision(self):
        result = self.run_task()
        _, manifest, _ = self.load(result)
        original_read = tasks.read_run
        checked = False
        def interleave(run):
            nonlocal checked
            loaded = original_read(run)
            if not checked:
                checked = True
                with self.assertRaisesRegex(ValueError, 'ledger lock'):
                    tasks.offline_operation(self.repo, result['run'], 'export-z')
            return loaded
        with patch.object(tasks, 'read_run', side_effect=interleave):
            tasks.offline_operation(self.repo, result['run'], 'accept', manifest['files']['worker.json'])
        self.assertTrue(checked)
        tasks.offline_operation(self.repo, result['run'], 'export-z')
        run, manifest, receipt = self.load(result)
        self.assertIn('decision.json', manifest['files'])
        self.assertIn('z-review-packet.json', manifest['files'])
        self.assertEqual(receipt['human_acceptance'], 'accept')
        self.assertEqual(tasks.report(self.repo)['accepted_result_count'], 1)

    def test_crash_after_recorded_response_blocks_spending_and_offline_mutation(self):
        original_save = tasks.save_state
        def crash(run, receipt, manifest):
            original_save(run, receipt, manifest)
            if receipt['status'] == 'response_received':
                raise SystemExit('Simulated exit before artifact validation')
        with patch.object(tasks, 'save_state', side_effect=crash):
            with self.assertRaises(SystemExit):
                self.run_task()
        run = next((tasks.runs_root(self.repo) / 'fixture-task').iterdir())
        name = run.relative_to(tasks.runs_root(self.repo)).as_posix()
        self.assertEqual(tasks.read_run(run)[1]['calls'][0]['reported_cost_usd'], '0.001')
        self.assertFalse(tasks.report(self.repo)['accounting_complete'])
        self.assertEqual(tasks.report(self.repo)['total_recorded_spend_usd'], '0.001')
        with self.assertRaisesRegex(ValueError, 'not terminal'):
            tasks.offline_operation(self.repo, name, 'export-z')
        with self.assertRaisesRegex(ValueError, 'Prior attempt accounting'):
            self.run_task()
        self.assertEqual(len(self.requests), 1)

    def test_incomplete_accounting_never_yields_an_accepted_result_ratio(self):
        def missing_cost(*args):
            result = self.provider(*args)
            del result['usage']['cost']
            return result
        result = self.run_task(missing_cost)
        _, manifest, _ = self.load(result)
        accepted = tasks.offline_operation(self.repo, result['run'], 'accept', manifest['files']['worker.json'])
        self.assertEqual(accepted['report']['accepted_result_count'], 1)
        self.assertIsNone(accepted['report']['cost_per_accepted_result_usd'])
        self.assertEqual(accepted['report']['ratio_reason'], 'Accounting incomplete')

    def test_model_lane_rejects_over_cap_priced_models_before_transport(self):
        config = copy.deepcopy(self.config)
        config.update(model_lane='economy', allow_paid=True, budget_usd='0.05',
                      worker_model='fixture/frontier')
        config['pricing']['fixture/frontier'] = {
            'observed_on': datetime.now(timezone.utc).date().isoformat(),
            'source': 'Synthetic offline fixture, not a market quote',
            'input_usd_per_million': '5', 'output_usd_per_million': '15'}
        prepared = tasks.plan(config, self.packet)
        self.assertFalse(prepared['can_run'])
        self.assertEqual(prepared['blocked_reasons'],
                         ['fixture/frontier exceeds the economy lane cap on input_usd_per_million; '
                          'use a cheaper model or change the lane policy'])
        self.assertEqual(prepared['roles']['worker']['model_lane'], 'economy')
        with patch.object(tasks.talk, 'complete') as transport:
            with self.assertRaisesRegex(ValueError, 'lane cap'):
                tasks.run_task(self.repo, config, self.packet, 'fixture-private-key')
        transport.assert_not_called()
        self.assertFalse(tasks.runs_root(self.repo).exists())

    def test_model_lane_allows_within_cap_pricing_and_records_lane(self):
        config = copy.deepcopy(self.config)
        config.update(model_lane='economy', allow_paid=True, budget_usd='0.05',
                      worker_model='fixture/paid')
        config['pricing']['fixture/paid'] = dict(
            config['pricing']['fixture/worker:free'],
            input_usd_per_million='0.075', output_usd_per_million='0.3')
        prepared = tasks.plan(config, self.packet)
        self.assertTrue(prepared['can_run'])
        self.assertEqual(prepared['blocked_reasons'], [])
        for role in ('worker', 'reviewer'):
            self.assertEqual(prepared['roles'][role]['model_lane'], 'economy')
            self.assertNotIn('z_lane_exemption', prepared['roles'][role])

    def test_z_lane_exemption_is_dated_recorded_and_reenforces_after_expiry(self):
        config = copy.deepcopy(self.config)
        config.update(model_lane='economy', allow_paid=True, budget_usd='0.05',
                      worker_model='mistralai/z-control')
        config['pricing']['mistralai/z-control'] = {
            'observed_on': datetime.now(timezone.utc).date().isoformat(),
            'source': 'Synthetic offline fixture, not a market quote',
            'input_usd_per_million': '5', 'output_usd_per_million': '15'}
        future = datetime(2026, 12, 31, tzinfo=timezone.utc).date()
        past = datetime(2026, 1, 1, tzinfo=timezone.utc).date()
        with patch.object(tasks, 'Z_LANE_EXEMPT_UNTIL', future):
            prepared = tasks.plan(config, self.packet)
            self.assertTrue(prepared['can_run'])
            self.assertEqual(prepared['roles']['worker']['z_lane_exemption'],
                             'mistral-family model exempt through ' + future.isoformat())
            self.assertNotIn('z_lane_exemption', prepared['roles']['reviewer'])
        with patch.object(tasks, 'Z_LANE_EXEMPT_UNTIL', past):
            prepared = tasks.plan(config, self.packet)
            self.assertFalse(prepared['can_run'])
            self.assertIn('economy lane cap', prepared['blocked_reasons'][0])
            self.assertNotIn('z_lane_exemption', prepared['roles']['worker'])

    def test_unknown_model_lane_is_rejected_with_named_lanes(self):
        config = copy.deepcopy(self.config)
        for name in ('premium', 'Economy', 'free'):
            config['model_lane'] = name
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, 'named lane'):
                    tasks.validate_config(config)



if __name__ == '__main__':
    unittest.main()
