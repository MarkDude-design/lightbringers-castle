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

if __package__:
    from . import room_tools
else:
    import room_tools

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
TOOL_SYSTEM = (
    'You are a panelist at a playful, surreal castle comedy table. '
    'Respond to the host in at most 80 words. Stay playful rather than hostile. '
    'Do not claim to be a historical model or a particular named assistant. '
    'You may use the read_room tool when the host asks about a Castle room. '
    'Use stored room data rather than inventing room details, and mention at least '
    'one concrete detail from the tool result in your answer.'
)
MAX_CALLS = 12
MAX_TOOL_EXECUTIONS = 4


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


def request_body(provider, model, messages, tools=None, tool_choice='auto'):
    if provider == 'openrouter' and model != 'openrouter/free' and not model.endswith(':free'):
        raise ValueError('OpenRouter model must be openrouter/free or an explicit :free model')
    body = {'model': model, 'messages': messages, 'stream': False}
    body['max_completion_tokens' if provider == 'groq' else 'max_tokens'] = 1024
    if provider == 'groq' and model in ('openai/gpt-oss-20b', 'openai/gpt-oss-120b'):
        body['reasoning_effort'] = 'low'
    if tools is not None:
        if provider != 'openrouter':
            raise ValueError('Local Castle tools are currently OpenRouter-only')
        body['tools'] = tools
        body['tool_choice'] = tool_choice
        body['parallel_tool_calls'] = False
    return body


def complete(provider, key, body):
    """Make one request; local tool execution, when enabled, happens elsewhere."""
    record = {'status': 'error', 'text': None, 'returned_model': None,
              'usage': None, 'raw': None, 'error': None, 'http_status': None,
              'retry_after': None, 'finish_reason': None, 'message': None,
              'tool_calls': None, 'inference_id': None}
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
        message = choice.get('message')
        if not isinstance(message, dict):
            raise ValueError('Provider returned no assistant message')
        text = message.get('content')
        tool_calls = message.get('tool_calls')
        has_text = isinstance(text, str) and bool(text.strip())
        has_tools = isinstance(tool_calls, list) and bool(tool_calls)
        if not has_text and not has_tools:
            raise ValueError('No text or tool call returned; native response preserved')
        record.update(status='ok', text=text if has_text else None,
                      message=message, tool_calls=tool_calls if has_tools else [],
                      inference_id=native.get('id'))
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


def messages_for(provider, events, tool_enabled=False):
    """Peer replies are labeled external contributions, not fabricated own turns."""
    messages = [{'role': 'system', 'content': TOOL_SYSTEM if tool_enabled else SYSTEM}]
    for event in events:
        if event['speaker'] == provider:
            if event.get('native_messages'):
                messages.extend(event['native_messages'])
            else:
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
    room_tool_mode = bool(getattr(args, 'room_tools', False))
    catalog = room_tools.tool_catalog() if room_tool_mode else None
    print(f'\n{session_id}\nTranscript: {path}\nHost: {args.prompt}\n', flush=True)
    print(f'Ctrl+C stops. STOP file is checked between calls. Maximum {MAX_CALLS} calls.\n',
          flush=True)
    counts = {'ok': 0, 'error': 0, 'stopped': 0}
    replies = 0
    call_index = 0
    tool_executions = 0
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
               'prompt': args.prompt, 'providers': providers, 'max_calls': MAX_CALLS,
               'room_tools': room_tool_mode,
               'max_tool_executions': MAX_TOOL_EXECUTIONS if room_tool_mode else 0,
               'source_kind': 'live_api', 'historical_model': False})

        def call_provider(provider, body, phase='reply'):
            nonlocal call_index, last_openrouter, stop
            if call_index >= MAX_CALLS:
                return None
            if args.stop_file.exists():
                stop = True
                write({'event': 'session_stopped', 'session_id': session_id,
                       'reason': 'STOP file present', 'at': now()})
                return None
            if provider == 'openrouter' and last_openrouter is not None:
                time.sleep(max(0, 4 - (time.monotonic() - last_openrouter)))
            if args.stop_file.exists():
                stop = True
                write({'event': 'session_stopped', 'session_id': session_id,
                       'reason': 'STOP file present', 'at': now()})
                return None
            call_index += 1
            if provider == 'openrouter':
                last_openrouter = time.monotonic()
            identity = {'session_id': session_id, 'call_index': call_index,
                        'provider': provider, 'requested_model': models[provider],
                        'phase': phase}
            write({'event': 'call_started', **identity, 'at': now()})
            print(f'{provider}: requesting {phase}...', flush=True)
            result = complete(provider, keys[provider], body)
            result = write({'event': 'call_finished', **identity, 'at': now(),
                            'source_kind': 'live_api', 'historical_model': False,
                            'request': body, **result})
            counts[result['status']] += 1
            return result

        try:
            while call_index < MAX_CALLS and not stop:
                for _ in range(args.rounds):
                    for provider in providers:
                        if call_index >= MAX_CALLS:
                            break
                        tool_enabled = room_tool_mode and provider == 'openrouter'
                        messages = messages_for(provider, events, tool_enabled)
                        forced_choice = ({'type': 'function',
                                          'function': {'name': 'read_room'}}
                                         if tool_enabled else 'auto')
                        body = request_body(provider, models[provider], messages,
                                            catalog if tool_enabled else None, forced_choice)
                        result = call_provider(provider, body)
                        if result is None:
                            break
                        transaction_models = set()
                        if result.get('returned_model'):
                            transaction_models.add(result['returned_model'])
                        native_messages = []
                        tool_failed = False
                        while result['status'] == 'ok' and result.get('tool_calls'):
                            if not tool_enabled:
                                counts['error'] += 1
                                tool_failed = True
                                write({'event': 'tool_loop_stopped', 'session_id': session_id,
                                       'at': now(), 'reason': 'Tools were not enabled'})
                                break
                            calls = result['tool_calls']
                            if tool_executions + len(calls) > MAX_TOOL_EXECUTIONS:
                                counts['error'] += 1
                                tool_failed = True
                                write({'event': 'tool_loop_stopped', 'session_id': session_id,
                                       'at': now(), 'reason': 'Tool execution cap reached',
                                       'max_tool_executions': MAX_TOOL_EXECUTIONS})
                                break
                            assistant_message = result.get('message')
                            if not isinstance(assistant_message, dict):
                                counts['error'] += 1
                                tool_failed = True
                                write({'event': 'tool_loop_stopped', 'session_id': session_id,
                                       'at': now(), 'reason': 'Missing assistant tool-call message'})
                                break
                            messages.append(assistant_message)
                            native_messages.append(assistant_message)
                            for tool_call in calls:
                                execution = room_tools.execute_tool_call(tool_call)
                                tool_executions += 1
                                write({'event': 'tool_executed', 'session_id': session_id,
                                       'at': now(), 'provider': provider,
                                       'requested_model': models[provider], **execution})
                                if not execution['tool_call_id']:
                                    counts['error'] += 1
                                    tool_failed = True
                                    break
                                tool_message = {
                                    'role': 'tool',
                                    'tool_call_id': execution['tool_call_id'],
                                    'content': json.dumps(execution['result'], ensure_ascii=False),
                                }
                                if isinstance(execution['tool_name'], str):
                                    tool_message['name'] = execution['tool_name']
                                messages.append(tool_message)
                                native_messages.append(tool_message)
                            if tool_failed:
                                break
                            if call_index >= MAX_CALLS:
                                counts['error'] += 1
                                tool_failed = True
                                write({'event': 'tool_loop_stopped', 'session_id': session_id,
                                       'at': now(), 'reason': 'API call cap reached before continuation'})
                                break
                            continuation = request_body(provider, models[provider], messages, catalog)
                            result = call_provider(provider, continuation, phase='tool_continuation')
                            if result is None:
                                tool_failed = True
                                break
                            if result.get('returned_model'):
                                transaction_models.add(result['returned_model'])
                        if tool_enabled and len(transaction_models) > 1:
                            counts['error'] += 1
                            tool_failed = True
                            write({'event': 'tool_model_mismatch', 'session_id': session_id,
                                   'at': now(), 'requested_model': models[provider],
                                   'returned_models': sorted(transaction_models)})
                        if tool_failed:
                            print(f'[{provider}: error] Tool loop stopped; see transcript.', flush=True)
                            continue
                        if result['status'] == 'ok' and result.get('text'):
                            print(f"\n[{provider} / {result['returned_model'] or 'unreported model'}]\n{result['text']}\n", flush=True)
                            replies += 1
                            if native_messages:
                                native_messages.append(result['message'])
                            events.append({
                                'speaker': provider,
                                'model': result['returned_model'],
                                'text': result['text'],
                                'native_messages': native_messages or None,
                            })
                        else:
                            error = result.get('error') or {'message': 'No final text answer returned'}
                            print(f"[{provider}: {result['status']}] {error['message']}", flush=True)
                            if result['status'] == 'stopped':
                                stop = True
                                break
                    if stop or call_index >= MAX_CALLS:
                        break
                if stop or not args.interactive or call_index >= MAX_CALLS:
                    break
                prompt = input('Host (Enter or /stop ends): ').strip()
                if not prompt or prompt.lower() == '/stop':
                    break
                events.append({'speaker': 'host', 'text': prompt})
                write({'event': 'host_turn', 'session_id': session_id, 'at': now(), 'text': prompt})
        except KeyboardInterrupt:
            write({'event': 'session_stopped', 'session_id': session_id, 'at': now(), 'reason': 'Ctrl+C'})
        write({'event': 'session_finished', 'session_id': session_id, 'at': now(),
               'counts': counts, 'replies': replies, 'api_calls': call_index,
               'tool_executions': tool_executions})
    print(f"Finished: {replies} real replies, {counts['error']} errors, "
          f"{call_index} API calls, {tool_executions} tool executions. {path}")
    return 0 if replies and not counts['error'] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt', default=DEFAULT_PREMISE)
    parser.add_argument('--rounds', type=int, choices=(1, 2, 3), default=2)
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--groq-model', default='openai/gpt-oss-20b')
    parser.add_argument('--openrouter-model', default='openrouter/free')
    parser.add_argument('--room-tools', action='store_true',
                        help='Allow OpenRouter to read enumerated Castle room JSON')
    parser.add_argument('--output', type=Path, default=Path('.talk-runs'))
    parser.add_argument('--stop-file', type=Path, default=Path('STOP'))
    args = parser.parse_args(argv)
    request_body('openrouter', args.openrouter_model, [])
    if args.room_tools and args.openrouter_model == 'openrouter/free':
        parser.error('--room-tools requires an explicit named :free OpenRouter model so '
                     'the tool call and continuation use the same model')
    try:
        keys = {p: obtain_key(p) for p in PROVIDERS}
    except (KeyboardInterrupt, EOFError, getpass.GetPassWarning):
        print('Key entry cancelled or hidden input unavailable. Use a normal terminal.', file=sys.stderr)
        return 2
    if not any(keys.values()):
        print('No API keys supplied. Create a provider API key, then rerun in a terminal.', file=sys.stderr)
        return 2
    if args.room_tools and not keys.get('openrouter'):
        print('--room-tools requires an OpenRouter API key.', file=sys.stderr)
        return 2
    return run(args, keys)


if __name__ == '__main__':
    raise SystemExit(main())
