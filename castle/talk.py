"""Real Groq/OpenRouter conversation. Python 3.10+, standard library only."""
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import uuid
import warnings

PROVIDERS = {
    'groq': ('https://api.groq.com/openai/v1/chat/completions', 'GROQ_API_KEY'),
    'openrouter': ('https://openrouter.ai/api/v1/chat/completions', 'OPENROUTER_API_KEY'),
}
DEFAULT_PREMISE = (
    'Match Game at Lightbringer\'s Castle: The new AI butler was so literal, '
    'when the king asked it to break the ice, it brought a BLANK. '
    'Give one short funny answer, then react to the other panelist when there is one.'
)
SYSTEM = (
    'You are a panelist at a playful, surreal castle comedy table. '
    'Respond to the host and previous panelist, in at most 80 words. '
    'Only write your own turn. Do not invent the other panelist\'s reply. '
    'Stay playful rather than hostile. Do not claim to be a historical model '
    'or a particular named assistant. You have no tools or real-world actions.'
)


def now():
    return datetime.now(timezone.utc).isoformat()


def redact(value, keys):
    text = json.dumps(value, ensure_ascii=False)
    changed = False
    for key in keys:
        if key:
            encoded = json.dumps(key, ensure_ascii=False)[1:-1]
            if encoded in text:
                text = text.replace(encoded, '[REDACTED_API_KEY]')
                changed = True
    return json.loads(text), changed


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect refused', headers, fp)


def request_body(provider, model, messages):
    if provider == 'openrouter' and model != 'openrouter/free' and not model.endswith(':free'):
        raise ValueError('OpenRouter model must be openrouter/free or an explicit :free model')
    body = {'model': model, 'messages': messages, 'stream': False}
    body['max_completion_tokens' if provider == 'groq' else 'max_tokens'] = 1024
    if provider == 'groq' and model in ('openai/gpt-oss-20b', 'openai/gpt-oss-120b'):
        body['reasoning_effort'] = 'low'
    return body


def complete(provider, key, body):
    """One request; no retry, paid fallback, redirects, or model tool execution."""
    record = {'status': 'error', 'text': None, 'returned_model': None,
              'usage': None, 'raw': None, 'error': None, 'http_status': None,
              'retry_after': None, 'finish_reason': None}
    start = time.monotonic()
    try:
        req = urllib.request.Request(
            PROVIDERS[provider][0], data=json.dumps(body).encode(),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                     'User-Agent': 'LightbringersCastle/0.2'}, method='POST')
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(req, timeout=45) as response:
            record['http_status'] = response.status
            payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise ValueError('Response exceeds 1 MiB limit')
        record['raw'] = payload.decode('utf-8', errors='replace')
        native = json.loads(record['raw'])
        record['raw'] = native
        if not isinstance(native, dict):
            raise ValueError('Provider returned a non-object response')
        record['returned_model'] = native.get('model')
        record['usage'] = native.get('usage')
        if native.get('error'):
            raise ValueError('Provider returned an error; see raw.error')
        choice = native['choices'][0]
        record['finish_reason'] = choice.get('finish_reason')
        text = choice['message'].get('content')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('No text answer returned; native response preserved')
        record.update(status='ok', text=text)
    except urllib.error.HTTPError as exc:
        record.update(http_status=exc.code, retry_after=exc.headers.get('Retry-After'))
        record['error'] = {'type': 'HTTPError', 'message': str(exc)}
        try:
            record['raw'] = exc.read(1024 * 1024).decode('utf-8', errors='replace')
        except Exception as read_error:
            record['error']['body_read_error'] = type(read_error).__name__
    except KeyboardInterrupt:
        record.update(status='stopped', error={'type': 'KeyboardInterrupt', 'message': 'Host stopped this call'})
    except Exception as exc:
        record['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    record['elapsed_seconds'] = round(time.monotonic() - start, 3)
    return record


def messages_for(provider, events):
    """Peer replies are labeled external contributions, not fabricated own turns."""
    messages = [{'role': 'system', 'content': SYSTEM}]
    for event in events:
        if event['speaker'] == provider:
            messages.append({'role': 'assistant', 'content': event['text']})
        else:
            label = event.get('model') or event['speaker']
            messages.append({'role': 'user', 'content': f"[{event['speaker']} / {label}] {event['text']}"})
    messages.append({'role': 'user', 'content': 'Your turn. Give just your own short reply.'})
    return messages


def obtain_key(provider):
    env_name = PROVIDERS[provider][1]
    key = os.environ.get(env_name, '').strip()
    if key:
        return key
    if not sys.stdin.isatty():
        return ''
    # Fail closed rather than falling back to a visible password prompt.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        return getpass.getpass(f'{provider} API key (hidden; Enter skips this provider): ').strip()


def run(args, keys):
    session_id = 'talk-' + uuid.uuid4().hex
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.output / (session_id + '.jsonl')
    events = [{'speaker': 'host', 'text': args.prompt}]
    models = {'groq': args.groq_model, 'openrouter': args.openrouter_model}
    providers = [p for p in PROVIDERS if keys.get(p)]
    print(f'\n{session_id}\nTranscript: {path}\nHost: {args.prompt}\n', flush=True)
    print('Ctrl+C stops. STOP file is checked between calls. Maximum 12 calls.\n', flush=True)
    counts = {'ok': 0, 'error': 0, 'stopped': 0}
    call_index = 0
    last_openrouter = None
    stop = False
    with path.open('x', encoding='utf-8') as log:
        def write(value):
            clean, changed = redact(value, keys.values())
            clean['credential_redacted'] = changed
            log.write(json.dumps(clean, ensure_ascii=False) + '\n')
            log.flush()
            return clean

        write({'event': 'session_started', 'session_id': session_id, 'at': now(),
               'prompt': args.prompt, 'providers': providers, 'max_calls': 12,
               'source_kind': 'live_api', 'historical_model': False})
        try:
            while call_index < 12 and not stop:
                for _ in range(args.rounds):
                    for provider in providers:
                        if call_index >= 12:
                            break
                        if args.stop_file.exists():
                            stop = True
                            write({'event': 'session_stopped', 'session_id': session_id,
                                   'reason': 'STOP file present', 'at': now()})
                            break
                        if provider == 'openrouter' and last_openrouter is not None:
                            time.sleep(max(0, 4 - (time.monotonic() - last_openrouter)))
                        if args.stop_file.exists():
                            stop = True
                            write({'event': 'session_stopped', 'session_id': session_id,
                                   'reason': 'STOP file present', 'at': now()})
                            break
                        body = request_body(provider, models[provider], messages_for(provider, events))
                        call_index += 1
                        if provider == 'openrouter':
                            last_openrouter = time.monotonic()
                        identity = {'session_id': session_id, 'call_index': call_index,
                                    'provider': provider, 'requested_model': models[provider]}
                        write({'event': 'call_started', **identity, 'at': now()})
                        print(f'{provider}: requesting reply...', flush=True)
                        result = complete(provider, keys[provider], body)
                        result = write({'event': 'call_finished', **identity, 'at': now(),
                                        'source_kind': 'live_api', 'historical_model': False,
                                        'request': body, **result})
                        counts[result['status']] += 1
                        if result['status'] == 'ok':
                            print(f"\n[{provider} / {result['returned_model'] or 'unreported model'}]\n{result['text']}\n", flush=True)
                            events.append({'speaker': provider, 'model': result['returned_model'],
                                           'text': result['text']})
                        else:
                            print(f"[{provider}: {result['status']}] {result['error']['message']}", flush=True)
                            if result['status'] == 'stopped':
                                stop = True
                                break
                    if stop or call_index >= 12:
                        break
                if stop or not args.interactive or call_index >= 12:
                    break
                prompt = input('Host (Enter or /stop ends): ').strip()
                if not prompt or prompt.lower() == '/stop':
                    break
                events.append({'speaker': 'host', 'text': prompt})
                write({'event': 'host_turn', 'session_id': session_id, 'at': now(), 'text': prompt})
        except KeyboardInterrupt:
            write({'event': 'session_stopped', 'session_id': session_id, 'at': now(), 'reason': 'Ctrl+C'})
        write({'event': 'session_finished', 'session_id': session_id, 'at': now(), 'counts': counts})
    print(f"Finished: {counts['ok']} real replies, {counts['error']} errors. {path}")
    return 0 if counts['ok'] and not counts['error'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', default=DEFAULT_PREMISE)
    parser.add_argument('--rounds', type=int, choices=(1, 2, 3), default=2)
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--groq-model', default='openai/gpt-oss-20b')
    parser.add_argument('--openrouter-model', default='openrouter/free')
    parser.add_argument('--output', type=Path, default=Path('.talk-runs'))
    parser.add_argument('--stop-file', type=Path, default=Path('STOP'))
    args = parser.parse_args(argv)
    request_body('openrouter', args.openrouter_model, [])
    try:
        keys = {p: obtain_key(p) for p in PROVIDERS}
    except (KeyboardInterrupt, EOFError, getpass.GetPassWarning):
        print('Key entry cancelled or hidden input unavailable. Use a normal terminal.', file=sys.stderr)
        return 2
    if not any(keys.values()):
        print('No API keys supplied. Create a provider API key, then rerun in a terminal.', file=sys.stderr)
        return 2
    return run(args, keys)


if __name__ == '__main__':
    raise SystemExit(main())
