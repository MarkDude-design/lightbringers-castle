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
