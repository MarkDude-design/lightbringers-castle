"""Offline fixtures only: these tests do not demonstrate live model replies."""
import argparse
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
