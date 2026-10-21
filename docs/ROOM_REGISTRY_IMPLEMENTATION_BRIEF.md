<!-- BEGIN FROZEN HOST BRIEF -->
# Host implementation brief: unavailable room eligibility

Identity: `castle-host-room-registry-eligibility-v1-20261021`.
Author: Codex host revision under Mark's explicit authorization of Meraki's packet.
Source commit: `333168088a6db1f7e9ba5ef0991b4b79f7b5b7f1`.
Parent worker SHA-256: `28f025b3bc08154147770577c633299338b72832861321619128e23d0e3e8d49`.
Parent review: `needs_changes`; the model ticket remains unaccepted and unchanged.
Related receipt-only draft: [PR #17](https://github.com/MarkDude-design/lightbringers-castle/pull/17).

## Evidence and identity boundary

Credit the enumeration gap to the **host/Codex synthetic offline probe**.
Codex directly inspected the authoritative private packet, worker, review,
manifest hashes, four-attempt ledger, and unset human-decision state for this
revision. Meraki's prior review covered public receipts/source, not that private
inspection. Prior live execution is retained evidence, not rerun here. Current
verification below is offline. No Z, Opus, Gemini, or extra model participated.
This is a separate host-authored brief, not a runner packet, model-produced
artifact, acceptance decision, or new ledger entry. Original failures remain.

## Behavior, scope, and limits

In `room_paths`, retain room-ID/containment gates and sorted enumeration. Evaluate
`is_file()` and, only on success, the size `stat()` once per candidate per pass.
Catch only `OSError` from those eligibility operations, skip that candidate, and
continue without retries or another existence precheck. Other exceptions escape.
The skipped ID is absent from the catalog and yields existing `unknown_room`
with healthy `available_rooms`. Preserve the 64 KiB bound, symlink restrictions,
successful data/linkage, read-time `room_read_failed`, ID mismatch, and CLI exits.

Authorized files: `castle/room_tools.py`, `tests/test_talk.py`,
`tests/test_project_tasks.py`, plus this single implementation/handoff document.
The host explicitly expands the earlier ticket's test scope; no model artifact
or frozen allowlist is rewritten. Zero new billed inference calls; closed live
batch stays closed. Packet, token, tool-call, and accounting limits are unchanged.

## Source snapshot before repair

Full hashes cover exact original bytes. Full files remain in Git/checkout.
`tests/test_project_tasks.py` exceeds 32 KiB: use these bounded excerpts, never
raise the runner cap, truncate its source, or pretend this brief is a valid packet.

| File | Original bytes / lines | SHA-256 |
| --- | ---: | --- |
| `castle/room_tools.py` | 4842 / 125 | `8ca1f4cbc41992207d8e59219259098f8df2c413a01e1f26fa8d6f5d4d522b7c` |
| `tests/test_project_tasks.py` | 59947 / 1036 | `2780f27644b825b8ec811711843613bf9a0b58bde324d7540f40a25a6ec6b654` |
| `tests/test_talk.py` | 26109 / 446 | `e08bde5bbb6d6b4fa8fe40c5f54f48e76f7d77c928803f59cc067d81616a229a` |

Line numbers below refer to that exact source commit; excerpts are not full-source substitutes.

### castle/room_tools.py:21–30

```text
21: def room_paths(rooms_dir=ROOMS_DIR):
22:     """Return the enumerated room registry as ``room_id -> JSON path``."""
23:     base = Path(rooms_dir).resolve()
24:     paths = {}
25:     for path in sorted(base.glob('*.json')):
26:         resolved = path.resolve()
27:         if (ROOM_ID.fullmatch(path.stem) and resolved.parent == base
28:                 and resolved.is_file() and resolved.stat().st_size <= 64 * 1024):
29:             paths[path.stem] = resolved
30:     return paths
```

### tests/test_talk.py:236–250

```text
236:     def test_room_registry_excludes_escape_symlinks_and_oversized_files(self):
237:         with tempfile.TemporaryDirectory() as tmp:
238:             base = Path(tmp)/'rooms'
239:             base.mkdir()
240:             outside = Path(tmp)/'outside.json'
241:             outside.write_text('{"id":"escape"}')
242:             (base/'escape.json').symlink_to(outside)
243:             (base/'large.json').write_text(' ' * (64 * 1024 + 1))
244:             (base/'broken.json').write_text('{')
245:             (base/'mismatch.json').write_text('{"id":"other"}')
246:             self.assertEqual(set(room_tools.room_paths(base)), {'broken', 'mismatch'})
247:             self.assertEqual(room_tools.read_room({'room_id': 'broken'}, base)['error']['code'],
248:                              'room_read_failed')
249:             self.assertEqual(room_tools.read_room({'room_id': 'mismatch'}, base)['error']['code'],
250:                              'room_id_mismatch')
```

### tests/test_project_tasks.py:638–658

```text
638:                         state['armed'] = result
639:                     return result
640:                 def disappearing(path, *args, **kwargs):
641:                     # Path.resolve may stat on some Python/platform versions.
642:                     # Arm only after the real is_file check has returned true.
643:                     if path == target and state['armed']:
644:                         state['failures'] += 1
645:                         raise error('Synthetic enumeration size-stat failure')
646:                     return original_stat(path, *args, **kwargs)
647:                 with patch.object(Path, 'stat', disappearing), patch.object(Path, 'is_file', existing):
648:                     with self.assertRaisesRegex(error, 'enumeration size-stat'):
649:                         tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)
650:                 self.assertEqual(state['is_file_results'], [True])
651:                 self.assertEqual(state['failures'], 1)
652:                 with patch.object(Path, 'read_text', side_effect=error('Synthetic read-time failure')):
653:                     result = tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)
654:                 self.assertFalse(result['ok'])
655:                 self.assertEqual(result['error']['code'], 'room_read_failed')
656:                 self.assertEqual(result['error']['message'], error.__name__)
657:         self.assertTrue(tasks.talk.room_tools.read_room({'room_id': 'courtyard'}, rooms)['ok'])
658:         self.assertEqual(target.read_bytes(), original_bytes)
```

## Proposed acceptance checks

- Inject `FileNotFoundError`, `PermissionError`, and generic `OSError` after a
  real successful `is_file()` at size-stat; assert injection reached exactly once.
- Inject the same errors at file eligibility; assert one evaluation and no retry.
  Exercise enumeration, catalog, failed-ID read, and healthy read independently.
- Keep healthy IDs/data with the failed candidate sorted first; assert consistent
  skip/catalog/`unknown_room` policy and one eligibility check per candidate.
- Retain host characterization/alias injection as handled-result regression;
  preserve read-time errors, invalid JSON, ID mismatch, containment, 64 KiB
  boundary, sorted IDs, exact successful tool result, call linkage, and CLI exit.
- Non-`OSError` must propagate. Stage files, run `python scripts/verify.py`,
  inspect all summaries/failures and the actual Linux/Windows hosted CI matrix.

## Uncertainties and non-goals

This does not cover base/candidate resolution or directory-iteration failures,
or guarantee atomic filesystem snapshots, stable cross-pass catalogs, or race
safety after enumeration. Some pathlib versions already convert file-check errors
to false; tests inject at explicit operation boundaries to exercise this handler.
Skipping retains the approved `unknown_room` policy; no new error codes, logging,
room messaging, retries, routers, tools, inference, or account changes are added.

<!-- END FROZEN HOST BRIEF -->

Brief SHA-256: `8206cf2e9693ecc18ddb7f9e857bb1d078dacc2f06ae8cb47d51867809391ab1`. Hash the exact UTF-8 bytes strictly between the markers in the committed Git
blob (LF), including adjacent leading/trailing LF, rather than a platform-newline
translated working copy. It excludes this hash line and
following handoff notes; there is no self-referential digest.

## Reviewer seeds

These are partial ideas for review, not established findings or implemented work.

- **Error visibility:** skipped unavailable rooms appear unknown. That could hide
  operational failures. A future review could compare operator needs against
  silent skipping and existing read-time errors; decide whether bounded error
  reporting is warranted without exposing paths or credentials.
- **Room logging/delivery:** no room-level audit message is emitted for skips.
  If continuity requires it, first define recipients, retention, privacy, and
  offline failure behavior; test that proposal separately. No infrastructure or
  delivery is added here.
- **Reviewer quality:** the retained model review restates the bug without
  explaining revisions. A future synthetic review set could check attribution,
  test scope, error coverage, and reason/verdict consistency. Human assessment is
  still needed; another model call is neither performed nor authorized here.

## Current verification and handoff

Local `python scripts/verify.py` passed all eight groups: 108 tests (95 main,
13 runtime probe), zero failures/errors/skips/expected failures; 13 Python files
compiled, 30 JSON files parsed, four JavaScript syntax checks, two CLI help
checks, and three whitespace checks. Linux, Python 3.12.14, Node 24.19.0.
An in-memory original-function negative control failed all 27 injected-error
subcases in three methods; the repaired code passes these same checks.
Hosted CI results and the exact resulting head are recorded in the PR/handback.
All 19 saved ledger files remain byte-identical: four attempts, $0.001293462
recorded spend, complete accounting, no accepted artifacts. Zero new model calls.
Mark owns merge/human acceptance; Meraki handles architecture. Passing checks
do not accept the original model ticket or establish live model acceptance.
