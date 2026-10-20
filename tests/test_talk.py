"""Offline fixtures only: these tests do not demonstrate live model replies."""
import argparse
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'castle'))
import talk
import room_tools


class TalkTests(unittest.TestCase):
    def run_tool_fixture(self, responses, *, on_call=None, cap=None):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(output=Path(tmp), prompt='Read courtyard.',
                groq_model='openai/gpt-oss-20b', openrouter_model='fixture/tool-model:free',
                room_tools=True, stop_file=Path(tmp)/'STOP', rounds=1, interactive=False)
            requests = []
            def complete(provider, key, body):
                requests.append(copy.deepcopy(body))
                if on_call:
                    on_call(args, len(requests))
                return copy.deepcopy(responses[len(requests)-1])
            with patch('talk.complete', side_effect=complete), patch('talk.time.sleep'), \
                    patch('talk.MAX_CALLS', cap or talk.MAX_CALLS), \
                    patch('sys.stdout', new=io.StringIO()), \
                    patch('room_tools.execute_tool_call', wraps=room_tools.execute_tool_call) as execute:
                code = talk.run(args, {'openrouter': 'fixture-key'})
            rows = [json.loads(line) for line in next(Path(tmp).glob('*.jsonl')).read_text().splitlines()]
            return code, requests, rows, execute.call_count

    def tool_response(self, ids=('call-one',), model='fixture/tool-model:free'):
        calls = [{'id': tool_id, 'type': 'function', 'function': {
            'name': 'read_room', 'arguments': '{"room_id":"courtyard"}'}} for tool_id in ids]
        message = {'role': 'assistant', 'content': None, 'tool_calls': calls,
                   'reasoning_details': [{'type': 'reasoning.encrypted', 'data': 'opaque-signature'}]}
        return {'status': 'ok', 'text': None, 'returned_model': model,
                'inference_id': 'gen-one', 'message': message, 'tool_calls': calls,
                'raw': {'id': 'gen-one'}, 'error': None}

    def final_response(self):
        message = {'role': 'assistant', 'content': 'Armor squeaks in iambic pentameter.'}
        return {'status': 'ok', 'text': message['content'],
                'returned_model': 'fixture/tool-model:free', 'inference_id': 'gen-final',
                'message': message, 'tool_calls': [], 'error': None, 'raw': {}}

    def test_duplicate_or_nonstring_ids_stop_before_execution(self):
        for ids in [('same', 'same'), (123,), ('',), (None,)]:
            with self.subTest(ids=ids):
                code, requests, rows, executions = self.run_tool_fixture([
                    self.tool_response(ids), self.final_response()])
                self.assertEqual(code, 1)
                self.assertEqual(len(requests), 1)
                self.assertEqual(executions, 0)
                self.assertTrue(any(row['event'] == 'tool_loop_stopped' for row in rows))

    def test_reused_id_in_continuation_is_not_executed_twice(self):
        code, requests, rows, executions = self.run_tool_fixture([
            self.tool_response(), self.tool_response(), self.final_response()])
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (2, 1))

    def test_stop_after_tool_response_prevents_local_execution(self):
        def stop(args, count):
            args.stop_file.touch()
        code, requests, rows, executions = self.run_tool_fixture([
            self.tool_response(), self.final_response()], on_call=stop)
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (1, 0))
        self.assertTrue(any(row['event'] == 'session_stopped' for row in rows))

    def test_model_drift_is_detected_before_another_tool_execution(self):
        code, requests, rows, executions = self.run_tool_fixture([
            self.tool_response(), self.tool_response(('call-two',), 'fixture/other:free'),
            self.final_response()])
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (2, 1))
        self.assertTrue(any(row['event'] == 'tool_model_mismatch' for row in rows))

    def test_provenance_links_tool_result_to_inference_and_preserves_metadata(self):
        first = self.tool_response()
        code, requests, rows, executions = self.run_tool_fixture([first, self.final_response()])
        self.assertEqual(code, 0)
        self.assertEqual(requests[1]['messages'][-2], first['message'])
        executed = next(row for row in rows if row['event'] == 'tool_executed')
        self.assertEqual(executed['call_index'], 1)
        self.assertEqual(executed['inference_id'], 'gen-one')
        self.assertEqual(executed['returned_model'], first['returned_model'])
        initial = next(row for row in rows if row['event'] == 'call_finished')
        self.assertFalse(any(message['role'] == 'tool' for message in initial['request']['messages']))

    def test_missing_role_final_tool_response_is_rejected_and_never_replayed(self):
        first = self.tool_response()
        malformed_message = {'content': 'Malformed final answer must not be replayed.'}
        natives = [
            {'id': 'gen-tool', 'model': first['returned_model'],
             'choices': [{'message': first['message'], 'finish_reason': 'tool_calls'}]},
            {'id': 'gen-malformed', 'model': first['returned_model'],
             'choices': [{'message': malformed_message, 'finish_reason': 'stop'}]},
            {'id': 'gen-next-round', 'model': first['returned_model'],
             'choices': [{'message': self.final_response()['message'], 'finish_reason': 'stop'}]},
        ]
        requests = []
        def open_response(request, **kwargs):
            requests.append(json.loads(request.data))
            response = io.BytesIO(json.dumps(natives[len(requests)-1]).encode())
            response.status = 200
            return response
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(output=Path(tmp), prompt='Read courtyard.',
                groq_model='openai/gpt-oss-20b', openrouter_model=first['returned_model'],
                room_tools=True, stop_file=Path(tmp)/'STOP', rounds=2, interactive=False)
            with patch('talk.urllib.request.build_opener') as factory, \
                    patch('talk.time.sleep'), patch('sys.stdout', new=io.StringIO()):
                factory.return_value.open.side_effect = open_response
                code = talk.run(args, {'openrouter': 'fixture-key'})
            rows = [json.loads(line) for line in next(Path(tmp).glob('*.jsonl')).read_text().splitlines()]
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 3)
        finished = [row for row in rows if row['event'] == 'call_finished']
        self.assertEqual([row['status'] for row in finished], ['ok', 'error', 'ok'])
        self.assertEqual(finished[1]['raw'], natives[1])
        self.assertEqual(finished[1]['error']['type'], 'ValueError')
        self.assertIsNone(finished[1]['message'])
        self.assertIsNone(finished[1]['text'])
        self.assertNotIn(malformed_message['content'], json.dumps(requests[2]['messages']))
        self.assertTrue(all('role' in message for message in requests[2]['messages']))
        self.assertEqual(rows[-1]['replies'], 1)
        self.assertEqual(rows[-1]['counts'], {'ok': 2, 'error': 1, 'stopped': 0})

    def test_malformed_tool_calls_are_not_ignored_when_text_is_present(self):
        for tool_calls in ['invalid', {}, 42]:
            native = {'model': 'fixture/tool-model:free', 'choices': [{'message': {
                'role': 'assistant', 'content': 'Text does not repair malformed calls.',
                'tool_calls': tool_calls}}]}
            response = io.BytesIO(json.dumps(native).encode())
            response.status = 200
            with patch('talk.urllib.request.build_opener') as factory:
                factory.return_value.open.return_value = response
                result = talk.complete('openrouter', 'fixture-key', {})
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['raw'], native)

    def test_malformed_identity_and_tool_message_shapes_are_errors(self):
        for bad_field in ('model', 'role', 'content'):
            fixture = self.tool_response()
            native = {'model': fixture['returned_model'], 'choices': [{'message': fixture['message']}]}
            if bad_field == 'model':
                native['model'] = ['not-a-model-id']
            elif bad_field == 'role':
                del native['choices'][0]['message']['role']
            else:
                native['choices'][0]['message']['content'] = {'not': 'text'}
            response = io.BytesIO(json.dumps(native).encode())
            response.status = 200
            with patch('talk.urllib.request.build_opener') as factory:
                factory.return_value.open.return_value = response
                result = talk.complete('openrouter', 'fixture-key', {})
            self.assertEqual(result['status'], 'error', bad_field)
            self.assertEqual(result['raw'], native)

    def test_duplicate_argument_fields_are_rejected(self):
        call = self.tool_response()['tool_calls'][0]
        call['function']['arguments'] = '{"room_id":"garden","room_id":"courtyard"}'
        result = room_tools.execute_tool_call(call)
        self.assertEqual(result['status'], 'error')

    def test_api_cap_prevents_continuation(self):
        code, requests, rows, executions = self.run_tool_fixture([
            self.tool_response(), self.final_response()], cap=1)
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (1, 1))
        self.assertTrue(any(row.get('reason') == 'API call cap reached before continuation'
                            for row in rows))

    def test_repeated_reads_with_new_ids_reach_tool_cap(self):
        responses = [self.tool_response((f'call-{i}',)) for i in range(5)]
        code, requests, rows, executions = self.run_tool_fixture(responses)
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (5, 4))
        self.assertTrue(any(row.get('reason') == 'Tool execution cap reached' for row in rows))
        self.assertEqual(rows[-1]['tool_executions'], 4)

    def test_multiple_distinct_calls_have_matching_results(self):
        code, requests, rows, executions = self.run_tool_fixture([
            self.tool_response(('one', 'two')), self.final_response()])
        self.assertEqual(code, 0)
        self.assertEqual(executions, 2)
        results = [message for message in requests[1]['messages'] if message['role'] == 'tool']
        self.assertEqual([message['tool_call_id'] for message in results], ['one', 'two'])

    def test_interrupt_during_continuation_stops_next_round(self):
        stopped = {'status': 'stopped', 'text': None, 'returned_model': None,
                   'error': {'message': 'Host stopped this call'}, 'tool_calls': []}
        code, requests, rows, executions = self.run_tool_fixture([self.tool_response(), stopped])
        self.assertEqual(code, 1)
        self.assertEqual((len(requests), executions), (2, 1))
        self.assertEqual(rows[-1]['counts']['stopped'], 1)

    def test_stop_during_spacing_prevents_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(output=Path(tmp), prompt='Read courtyard.',
                groq_model='openai/gpt-oss-20b', openrouter_model='fixture/tool-model:free',
                room_tools=True, stop_file=Path(tmp)/'STOP', rounds=1, interactive=False)
            with patch('talk.complete', return_value=self.tool_response()) as call, \
                    patch('talk.time.sleep', side_effect=lambda _: args.stop_file.touch()), \
                    patch('sys.stdout', new=io.StringIO()):
                self.assertEqual(talk.run(args, {'openrouter': 'fixture-key'}), 1)
            self.assertEqual(call.call_count, 1)

    def test_unknown_tool_and_bad_arguments_return_structured_errors(self):
        for name, arguments, error in [
                ('shell', '{}', 'unknown_tool'),
                ('read_room', '{', 'invalid_json'),
                ('read_room', '[]', 'invalid_arguments'),
                ('read_room', '{"room_id":"../courtyard"}', 'unknown_room'),
                ('read_room', '{"room_id":"courtyard","extra":true}', 'invalid_arguments')]:
            with self.subTest(name=name, arguments=arguments[:40]):
                call = self.tool_response()['tool_calls'][0]
                call['function'] = {'name': name, 'arguments': arguments}
                result = room_tools.execute_tool_call(call)
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['result']['error']['code'], error)

    def test_argument_decoder_recursion_failure_is_structured(self):
        with patch('room_tools.json.loads', side_effect=RecursionError('nested input')):
            result = room_tools.execute_tool_call(self.tool_response()['tool_calls'][0])
        self.assertEqual(result['result']['error']['code'], 'invalid_json')

    def test_room_registry_excludes_escape_symlinks_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)/'rooms'
            base.mkdir()
            outside = Path(tmp)/'outside.json'
            outside.write_text('{"id":"escape"}')
            (base/'escape.json').symlink_to(outside)
            (base/'large.json').write_text(' ' * (64 * 1024 + 1))
            (base/'broken.json').write_text('{')
            (base/'mismatch.json').write_text('{"id":"other"}')
            self.assertEqual(set(room_tools.room_paths(base)), {'broken', 'mismatch'})
            self.assertEqual(room_tools.read_room({'room_id': 'broken'}, base)['error']['code'],
                             'room_read_failed')
            self.assertEqual(room_tools.read_room({'room_id': 'mismatch'}, base)['error']['code'],
                             'room_id_mismatch')

    def test_key_echoes_are_redacted_from_console_and_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = 'secret-test-key'
            args = argparse.Namespace(output=Path(tmp), prompt=f'Host accidentally includes {key}',
                groq_model='openai/gpt-oss-20b', openrouter_model='openrouter/free',
                stop_file=Path(tmp)/'STOP', rounds=1, interactive=False)
            result = self.final_response()
            result.update(text=f'Provider echoed {key}', raw={'echo': key})
            with patch('talk.complete', return_value=result), \
                    patch('sys.stdout', new=io.StringIO()) as console:
                talk.run(args, {'openrouter': key})
            self.assertNotIn(key, console.getvalue())
            transcript = next(Path(tmp).glob('*.jsonl')).read_text()
            self.assertNotIn(key, transcript)
            self.assertIn('"credential_redacted": true', transcript)

    def test_hidden_prompt_fails_closed_and_redirects_are_refused(self):
        with patch.dict('talk.os.environ', {}, clear=True), \
                patch('talk.sys.stdin.isatty', return_value=True), \
                patch('talk.getpass.getpass', side_effect=talk.getpass.GetPassWarning('hidden input unavailable')):
            with self.assertRaises(talk.getpass.GetPassWarning):
                talk.obtain_key('openrouter')
        with self.assertRaises(urllib.error.HTTPError):
            request = talk.urllib.request.Request('https://openrouter.ai/api/v1/chat/completions')
            talk.NoRedirect().redirect_request(request, None, 302, 'Redirect', {}, 'https://other.invalid')

    def test_credentials_only_enter_authorization_header(self):
        native = {'model': 'fixture/model', 'choices': [{'message': {'content': 'Fixture'}}]}
        response = io.BytesIO(json.dumps(native).encode())
        response.status = 200
        with patch('talk.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = response
            talk.complete('openrouter', 'secret-header-key', {'model': 'fixture/model'})
            request = factory.return_value.open.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer secret-header-key')
        self.assertNotIn(b'secret-header-key', request.data)
        self.assertEqual(request.full_url, talk.PROVIDERS['openrouter'][0])

    def test_free_only_and_provider_parameters(self):
        with self.assertRaises(ValueError):
            talk.request_body('openrouter', 'paid/model', [])
        groq = talk.request_body('groq', 'openai/gpt-oss-20b', [])
        self.assertEqual(groq['reasoning_effort'], 'low')
        self.assertIn('max_completion_tokens', groq)
        self.assertNotIn('tools', groq)

    def test_other_provider_is_labeled_as_external_contribution(self):
        messages = talk.messages_for('groq', [
            {'speaker': 'host', 'text': 'Premise'},
            {'speaker': 'openrouter', 'model': 'fixture/model', 'text': 'Fixture peer reply'},
            {'speaker': 'groq', 'model': 'fixture/self', 'text': 'Fixture own reply'},
        ])
        self.assertEqual(messages[2]['role'], 'user')
        self.assertIn('fixture/model', messages[2]['content'])
        self.assertEqual(messages[3]['role'], 'assistant')

    def test_raw_response_and_actual_model_survive(self):
        native = {'model': 'fixture/actual-model', 'choices': [
            {'message': {'content': 'Fixture only'}, 'finish_reason': 'stop'}],
            'unexpected_native_field': {'keep': True}}
        response = io.BytesIO(json.dumps(native).encode())
        response.status = 200
        with patch('talk.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = response
            result = talk.complete('openrouter', 'fixture-key', {'model': 'openrouter/free'})
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['returned_model'], 'fixture/actual-model')
        self.assertEqual(result['raw'], native)
        self.assertIsNone(result['usage'])

    def test_tools_only_response_and_native_message_survive(self):
        message = {'role': 'assistant', 'content': None,
                   'tool_calls': [{'id': 'call-fixture', 'type': 'function',
                                   'function': {'name': 'read_room',
                                                'arguments': '{"room_id":"courtyard"}'}}],
                   'provider_metadata': {'preserve': True}}
        native = {'id': 'gen-fixture', 'model': 'fixture/tool-model:free',
                  'choices': [{'message': message, 'finish_reason': 'tool_calls'}]}
        response = io.BytesIO(json.dumps(native).encode())
        response.status = 200
        with patch('talk.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = response
            result = talk.complete('openrouter', 'fixture-key', {'model': 'fixture/model'})
        self.assertEqual(result['status'], 'ok')
        self.assertIsNone(result['text'])
        self.assertEqual(result['message'], message)
        self.assertEqual(result['tool_calls'], message['tool_calls'])
        self.assertEqual(result['inference_id'], 'gen-fixture')

    def test_room_tool_is_enumerated_and_rejects_paths(self):
        catalog = room_tools.tool_catalog()
        room_ids = catalog[0]['function']['parameters']['properties']['room_id']['enum']
        self.assertIn('courtyard', room_ids)
        result = room_tools.read_room({'room_id': '../courtyard'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'unknown_room')
        result = room_tools.read_room({'room_id': 'courtyard', 'path': '/etc/passwd'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'invalid_arguments')

    def test_openrouter_room_tool_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(output=Path(tmp), prompt='Read the courtyard room.',
                groq_model='openai/gpt-oss-20b',
                openrouter_model='fixture/tool-model:free', room_tools=True,
                stop_file=Path(tmp)/'STOP', rounds=1, interactive=False)
            tool_message = {
                'role': 'assistant', 'content': None,
                'tool_calls': [{
                    'id': 'call-courtyard', 'type': 'function',
                    'function': {'name': 'read_room',
                                 'arguments': '{"room_id":"courtyard"}'},
                }],
                'provider_metadata': {'preserved': True},
            }
            first = {'status': 'ok', 'text': None,
                     'returned_model': 'fixture/tool-model:free',
                     'message': tool_message, 'tool_calls': tool_message['tool_calls'],
                     'raw': {'id': 'gen-one'}, 'error': None}
            final_message = {'role': 'assistant',
                             'content': 'The armor squeaks in iambic pentameter.'}
            second = {'status': 'ok', 'text': final_message['content'],
                      'returned_model': 'fixture/tool-model:free',
                      'message': final_message, 'tool_calls': [],
                      'raw': {'id': 'gen-two'}, 'error': None}
            with patch('talk.complete', side_effect=[first, second]) as call, \
                    patch('talk.time.sleep'), patch('sys.stdout', new=io.StringIO()):
                code = talk.run(args, {'openrouter': 'fixture-key'})
            self.assertEqual(code, 0)
            self.assertEqual(call.call_count, 2)
            initial = call.call_args_list[0].args[2]
            self.assertEqual(initial['tool_choice']['function']['name'], 'read_room')
            continuation = call.call_args_list[1].args[2]
            self.assertIn('tools', continuation)
            self.assertEqual(continuation['tool_choice'], 'auto')
            self.assertEqual(continuation['messages'][-2], tool_message)
            tool_result = continuation['messages'][-1]
            self.assertEqual(tool_result['role'], 'tool')
            self.assertEqual(tool_result['tool_call_id'], 'call-courtyard')
            self.assertTrue(json.loads(tool_result['content'])['ok'])
            rows = [json.loads(line) for line in next(Path(tmp).glob('*.jsonl')).read_text().splitlines()]
            executed = [row for row in rows if row['event'] == 'tool_executed']
            self.assertEqual(len(executed), 1)
            self.assertEqual(executed[0]['result']['data']['id'], 'courtyard')
            finished = [row for row in rows if row['event'] == 'session_finished'][0]
            self.assertEqual((finished['api_calls'], finished['tool_executions'], finished['replies']),
                             (2, 1, 1))

    def test_http_error_preserved_without_retry(self):
        error = urllib.error.HTTPError('https://api.groq.com', 429, 'Rate limited',
                                      {'Retry-After': '30'}, io.BytesIO(b'{"error":"fixture limit"}'))
        with patch('talk.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = error
            result = talk.complete('groq', 'fixture-key', {})
            self.assertEqual(factory.return_value.open.call_count, 1)
        self.assertEqual(result['http_status'], 429)
        self.assertEqual(result['retry_after'], '30')
        self.assertIn('fixture limit', result['raw'])

    def test_failure_isolated_and_success_relayed_with_redaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(output=Path(tmp), prompt='Fixture host',
                groq_model='openai/gpt-oss-20b', openrouter_model='openrouter/free',
                stop_file=Path(tmp)/'STOP', rounds=2, interactive=False)
            success = {'status': 'ok', 'text': 'Fixture reply echoed secret-test-key',
                       'returned_model': 'fixture/model', 'raw': {'echo': 'secret-test-key'},
                       'error': None}
            failure = {'status': 'error', 'text': None, 'returned_model': None,
                       'raw': {'error': 'fixture'}, 'error': {'message': 'Fixture failure'}}
            with patch('talk.complete', side_effect=[failure, success, success, success]) as call, \
                    patch('talk.time.sleep'), patch('sys.stdout', new=io.StringIO()):
                self.assertEqual(talk.run(args, {'groq': 'secret-test-key', 'openrouter': 'other-test-key'}), 1)
            transcript = next(Path(tmp).glob('*.jsonl')).read_text()
            self.assertNotIn('secret-test-key', transcript)
            rows = [json.loads(line) for line in transcript.splitlines()]
            finished = [r for r in rows if r['event'] == 'call_finished']
            self.assertEqual([r['status'] for r in finished], ['error', 'ok', 'ok', 'ok'])
            third_messages = call.call_args_list[2].args[2]['messages']
            self.assertIn('Fixture reply', json.dumps(third_messages))
            self.assertNotIn('Fixture failure', json.dumps(third_messages))

    def test_stop_before_call_makes_no_api_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            stop = Path(tmp)/'STOP'
            stop.touch()
            args = argparse.Namespace(output=Path(tmp), prompt='Fixture host',
                groq_model='openai/gpt-oss-20b', openrouter_model='openrouter/free',
                stop_file=stop, rounds=2, interactive=False)
            with patch('talk.complete') as call, patch('sys.stdout', new=io.StringIO()):
                talk.run(args, {'groq': 'fixture-key'})
            call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
