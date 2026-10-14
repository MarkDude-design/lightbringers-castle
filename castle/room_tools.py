"""Small, read-only Castle tools for model-requested local data."""
import json
from pathlib import Path
import re
import time


ROOMS_DIR = Path(__file__).resolve().parent / 'rooms'
ROOM_ID = re.compile(r'^[a-z0-9_]+$')


def unique_fields(pairs):
    arguments = {}
    for name, value in pairs:
        if name in arguments:
            raise ValueError('Duplicate tool argument field')
        arguments[name] = value
    return arguments


def room_paths(rooms_dir=ROOMS_DIR):
    """Return the enumerated room registry as ``room_id -> JSON path``."""
    base = Path(rooms_dir).resolve()
    paths = {}
    for path in sorted(base.glob('*.json')):
        resolved = path.resolve()
        if (ROOM_ID.fullmatch(path.stem) and resolved.parent == base
                and resolved.is_file() and resolved.stat().st_size <= 64 * 1024):
            paths[path.stem] = resolved
    return paths


def tool_catalog(rooms_dir=ROOMS_DIR):
    """Build the OpenAI-compatible catalog from the local room registry."""
    return [{
        'type': 'function',
        'function': {
            'name': 'read_room',
            'description': 'Read one Castle room\'s stored scene data by its exact room ID.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'room_id': {
                        'type': 'string',
                        'enum': list(room_paths(rooms_dir)),
                    },
                },
                'required': ['room_id'],
                'additionalProperties': False,
            },
        },
    }]


def read_room(arguments, rooms_dir=ROOMS_DIR):
    """Return a room envelope without accepting a caller-controlled path."""
    if not isinstance(arguments, dict) or set(arguments) != {'room_id'}:
        return {
            'ok': False,
            'data': None,
            'error': {'code': 'invalid_arguments',
                      'message': 'Expected exactly one string field: room_id.'},
        }
    room_id = arguments.get('room_id')
    paths = room_paths(rooms_dir)
    if not isinstance(room_id, str) or room_id not in paths:
        return {
            'ok': False,
            'data': None,
            'error': {'code': 'unknown_room', 'message': 'Unknown Castle room ID.',
                      'available_rooms': list(paths)},
        }
    try:
        data = json.loads(paths[room_id].read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            'ok': False,
            'data': None,
            'error': {'code': 'room_read_failed', 'message': type(exc).__name__},
        }
    if not isinstance(data, dict) or data.get('id') != room_id:
        return {
            'ok': False,
            'data': None,
            'error': {'code': 'room_id_mismatch',
                      'message': 'Stored room data does not match its registry ID.'},
        }
    return {'ok': True, 'data': data, 'error': None}


def execute_tool_call(tool_call, rooms_dir=ROOMS_DIR):
    """Validate and execute one registered tool call, returning an audit record."""
    start = time.monotonic()
    tool_call_id = tool_call.get('id') if isinstance(tool_call, dict) else None
    function = tool_call.get('function') if isinstance(tool_call, dict) else None
    name = function.get('name') if isinstance(function, dict) else None
    requested_arguments = function.get('arguments') if isinstance(function, dict) else None
    result = None
    if not isinstance(tool_call_id, str) or not tool_call_id:
        result = {'ok': False, 'data': None,
                  'error': {'code': 'invalid_tool_call', 'message': 'Missing tool-call ID.'}}
    elif tool_call.get('type') != 'function' or name != 'read_room':
        result = {'ok': False, 'data': None,
                  'error': {'code': 'unknown_tool', 'message': 'Tool is not registered.'}}
    elif not isinstance(requested_arguments, str):
        result = {'ok': False, 'data': None,
                  'error': {'code': 'invalid_arguments',
                            'message': 'Tool arguments must be a JSON object string.'}}
    else:
        try:
            arguments = json.loads(requested_arguments, object_pairs_hook=unique_fields)
        except (ValueError, RecursionError):
            result = {'ok': False, 'data': None,
                      'error': {'code': 'invalid_json',
                                'message': 'Tool arguments are not valid JSON.'}}
        else:
            result = read_room(arguments, rooms_dir)
    return {
        'tool_call_id': tool_call_id,
        'tool_name': name,
        'requested_arguments': requested_arguments,
        'status': 'ok' if result['ok'] else 'error',
        'result': result,
        'elapsed_seconds': round(time.monotonic() - start, 6),
    }
