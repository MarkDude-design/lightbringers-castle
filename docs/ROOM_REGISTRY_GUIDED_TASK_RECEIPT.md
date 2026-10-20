# Guided room-registry task: receipt and offline finding

Status: **the guided low-reasoning worker returned JSON but failed the
nonempty acceptance-check contract; no reviewer call or retry**. This records
the third separately authorized attempt. It does not authorize a new request,
change the worker output, implement a repair, accept an artifact, or merge code.
The separate [PR #13](https://github.com/MarkDude-design/lightbringers-castle/pull/13)
records the previous attempt and is not modified or duplicated here.

## Input and limits

Mark merged PR #14 and then supplied a separate “Ready” to proceed. Fresh
read-only admission checked endpoint support, dated conservative prices,
funding/key allowance, the two prior charges, complete accounting, STOP and
locks. The nine endpoints advertising `reasoning`, `response_format`, and
`max_tokens` were covered by the same **$0.075 input / $0.30 output per million
tokens** envelope; eight reported status `0`. No provider was pinned.

Source commit: `cac9162e97cd9b711019fcaca9e95d4afb0da5c2`.
Task ID: `room-registry-error-ticket-v0` (unchanged).
Configuration: `room-registry-ticket-paid-gpt-oss-20b-low-reasoning.json`.
The retained request used `reasoning: {"effort": "low"}`, JSON mode,
`require_parameters: true`, `allow_fallbacks: false`, and the existing 2,048
completion-token cap. Both roles remained configured as `openai/gpt-oss-20b`;
only the worker was called. Separate roles using this model would not be
independent model-family review.

The frozen packet supplied original source text once, with byte hashes and
`splitlines()` counts: `room_tools.py` 125, `test_talk.py` 446, and `TALK.md` 149.
Packet SHA-256:
`4f291b9f5d95db876c72d906fb12d2b92b82641c0c996c9a612bde633b75f621`.

## Native result and strict rejection

Requested and returned model IDs matched exactly: `openai/gpt-oss-20b`.
Generation ID: `gen-1792537229-QM50PaPYmDskAtHabCI3`.
HTTP 200, `finish_reason: stop`, 19.418 seconds.
Reported usage: **10,449 prompt, 403 completion, 10,852 total tokens**;
completion details report **116 reasoning tokens**.

The response included every required field and a reference to valid lines
1–125 of `castle/room_tools.py`. It concluded that no repair was needed because
`read_room` already catches read-time errors. Its **`acceptance_checks` was an
empty list**, which violates the existing minimum of one check. The runner
rejected it without inserting a check, changing another field, invoking the
reviewer, or retrying. This was output-contract failure, not an authentication,
transport, JSON-parsing, identity, citation-range, or completion-cap failure.

No validated `worker.json`, worker artifact hash, reviewer response/verdict,
Z export, human acceptance, or artifact-bound accept/reject command exists.
The raw packet, native response, receipt and manifest remain outside Git.

## Cost and preserved history

| Attempt | Provider-reported cost (USD) |
|---|---:|
| Initial completion-cap failure | 0.000369954 |
| Low-effort missing-field/citation failure | 0.000253908 |
| Guided low-effort empty-checklist failure | 0.000224352 |
| **Cumulative recorded spend** | **0.000848214** |

Accounting is complete; all three charges remain under the original task ID
and **$0.05 cumulative local budget**. The two-call estimate for this latest
attempt was **$0.015178275**, with **$0.015802137** reserved including prior
charges. Estimates, reported actual costs and local admission budgets are
different quantities; the local budget is not a guaranteed provider billing
ceiling. These are provider-reported charges, not an independently reconciled
final bill. Cost per accepted result remains unavailable because none is
accepted. The two earlier attempts are byte-identical. No real ledger was
reset, repaired, accepted or rejected, and no account limit/credit was changed.

## Host offline finding: enumeration is a separate boundary

The worker's read-time observation does not establish that enumeration is safe.
[`read_room`](../castle/room_tools.py#L65) calls `room_paths` **before** the
read-time `try` at line 73. [`room_paths`](../castle/room_tools.py#L25) checks
`is_file()` and then calls `stat()` again for size at line 28. A disappearance
between those calls can propagate an exception before the later read handler.

Codex ran a **synthetic offline probe**, using one temporary room JSON and
mocking `Path.stat` for that file: allow the first call (`is_file`) to succeed,
then raise `FileNotFoundError` on the second call (size check). Calling
`read_room` propagated that error without a structured room envelope. The
probe observed exactly two target stat calls. It made no provider request,
changed no repository source, and is not an implemented repair or proof of all
filesystem failure cases. This is host evidence, not a validated worker ticket.

## Next safe review — proposal only

Before any new experiment, clarify the no-repair/evidence-insufficient outcome:
what nonempty verification checks must it include? The current validator still
requires at least one acceptance check; this receipt does not relax it.
A future reviewed guidance change could expose complete list bounds and target
the demonstrated enumeration boundary. Do not auto-fill a missing/empty check,
clip references, weaken validation, treat the rejected response as a ticket,
or change the logical task ID to bypass charges. No prompt, schema, parameter,
or provider behavior changed as part of this receipt.

Preflight offline verification passed **98 tests** (85 conversation/project/
verification and 13 runtime-probe), with zero failures/errors/skips, plus
compilation, tracked JSON parsing, four JavaScript syntax checks, both CLI help
commands, and whitespace checks. No further inference attempt is authorized.
Mark remains merge and human-acceptance gate; Meraki remains architecture reviewer.
