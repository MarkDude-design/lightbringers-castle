# Budgeted Project Tasks v0

One task, one worker ticket, one reviewer response, then Mark's offline decision.
This is a separate Python 3.10+ standard-library CLI. The existing `talk.py`
runner is unchanged. There is no MCP, new model tool, generated-code execution,
patch application, deployment, dashboard, model ladder, parallel worker, or
Puppy integration. The only subprocess is a fixed read-only Git HEAD lookup,
with no shell. Use a Git checkout, not a ZIP, for this entry point.

From the repository root, the first command is entirely offline:

```sh
python castle/project_tasks.py dry-run --config specs/tasks/room-registry-ticket.json
```

On Windows, substitute `py -3` for `python`. Dry-run reads explicitly selected
sources and the current Git HEAD; it never prompts for a key, requests a model,
or creates a run. It shows source sizes/hashes, packet hash, requested models,
call/token limits, dated pricing, estimates, and prior task accounting. Exit 1
means preflight is blocked, including missing/stale pricing or exhausted budget.

The example proposes a ticket for room-registry read-error handling from
`room_tools.py`, `test_talk.py`, and `TALK.md`. It does not implement that ticket.
It selects the previously observed named free model for both roles: two separate
calls, not two independent model families. Estimated provider cost is $0 using
the explicitly dated historical snapshot; the per-task budget is $0.01. Model
availability and structured-output compatibility are unverified for this feature.
The earlier room-tool live success is not a project-task live certification.
The supplied pricing expires after seven days; do not refresh its date without
refreshing the observation. A missing price is null and blocks spending.

## Configuration and budget

The example JSON is the complete configuration contract. Require explicit
`owner/model` worker/reviewer IDs; `openrouter/free`, `openrouter/auto`, and all
`openrouter/*` router IDs are rejected. Both roles use OpenRouter in v0. There is
no automatic model substitution or retry. Provider fallback is disabled and
required request parameters must be honored. Requests contain no model tools.

A model without `:free` requires `allow_paid: true` and a positive per-task
`budget_usd`. Editing those host configuration fields is the explicit paid
opt-in. **No paid or free project-task live transaction was run during this
implementation. Do not run the paid acceptance transaction yet.**

There are at most two inference calls per attempt, worker then reviewer, each
with 1..2048 completion tokens (example: 1200). STOP in the repository root is
checked before each call. It cannot cancel an in-flight request or ensure a
refund. The reused client has a 45-second socket timeout and 1 MiB success-body
cap; that is not a hard total runtime deadline. There is no automatic repair,
retry, escalation, or resume command.

Pricing is a host-supplied map of model IDs to `observed_on` (UTC date), `source`,
`input_usd_per_million`, and `output_usd_per_million`. Rates must be finite and
nonnegative; observations must be no older than seven days and cannot be future
dated. Estimates reserve one UTF-8 prompt byte per estimated token, plus the
completion cap, with space for the reviewer's worker artifact. This is a byte
heuristic, not a native tokenizer or a billing ceiling. It does not model
provider-specific surcharges or changes after observation.

The host reserves the two-call estimate before starting and checks the remaining
budget again before review. It adds actual provider-reported cost after every
response, including malformed, failed, or rejected attempts. The budget is
shared across every local attempt with the same `task_id`, even if its packet
changes. Do not reuse a task ID for unrelated work. An unexpectedly expensive
worker can exceed the local estimate before the host learns its actual charge;
the reviewer will then be blocked. **Provider-side key credit caps are the
spending backstop.** A local estimate cannot guarantee the final bill. No key
cap is created or changed by this feature.

Usage must include nonnegative integer prompt/completion/total token counts
and finite nonnegative cost. Missing cost or usage makes accounting incomplete
and prevents the next automatic call and later attempts under the same task ID.
A returned model must exactly match that role's requested model. Missing
identity is `unreported`; different identity is `alias_review`; both stop the
attempt without automatic approval. These states describe reported IDs, not
checkpoint attestation. The reviewer may intentionally be a different named
model from the worker; that role choice is not model drift. There is no
within-role model ladder in this two-call workflow.

## Frozen packet and output contracts

The packet records task ID, goal, acceptance criteria, boundaries, current full
Git base commit, allowed files, and the exact selected UTF-8 source contents.
Each source has its repository-relative POSIX path, SHA-256 of original bytes,
and byte length. Sources come from the working tree, so uncommitted edits can
be included: base commit is context, while source hashes define the actual
evidence. Dry-run and run have the same packet hash if HEAD, inputs, and sources
are unchanged. The packet is persisted once before inference and the reviewer
receives that same content and hash, plus the validated worker artifact/hash.

Input bounds:

- 1..8 files; at most 32 KiB per file and 96 KiB source bytes in total.
- At most 128 KiB canonical packet/config and 160 KiB per prompt envelope,
  including a conservative reserved worker envelope for review. Large packets
  can hit the reviewer prompt limit before the source-byte limit.
- Source extensions: `.py`, `.md`, `.json`, `.csv`, `.js`, `.txt`.
- Reject absolute/traversal/noncanonical/Windows-drive paths, escaping symlinks,
  hidden paths (including `.env`, `.git`, `.talk-runs`, `.task-runs`), generated
  dependency/build directories, credential-like filenames, recognizable key or
  private-key material, and already configured key values. An alias symlink to
  a hidden local file is also rejected. Arbitrary unknown embedded secrets
  cannot be reliably detected: select public project source, never local secrets.
- Bound goal/list/text fields as enforced by the local validator. Each output
  is at most 16 KiB, and source references have at most 12 entries with valid
  inclusive line ranges. No generated command is executed, even if present as
  text in a proposal.

Canonical hashing is SHA-256 of UTF-8 JSON with sorted keys, no extra spaces,
literal Unicode, finite numbers, and one trailing newline. There is no
self-referential hash field inside the packet. Artifact files are written in
this canonical form; their recorded hashes are exact file-byte hashes.

The worker JSON has exactly these fields:

```json
{
  "schema_version": "castle-ticket/0.1",
  "packet_sha256": "<packet hash>",
  "problem": "Concrete problem, supported by the cited sources.",
  "source_refs": [{"path": "castle/room_tools.py", "start_line": 1, "end_line": 5}],
  "allowed_files": ["castle/room_tools.py"],
  "proposed_change": "A bounded implementation proposal.",
  "acceptance_checks": ["A specific observable check."],
  "uncertainties": ["What cannot be established from supplied evidence."]
}
```

Allowed files must be a subset of the host's packet allowlist, which is itself
a subset of the selected source paths in v0. References must resolve to supplied
sources and actual line ranges; this verifies reference existence, not whether
the interpretation is correct. The reviewer checks substance. Unknown fields,
duplicate JSON fields, wrong hashes, unregistered source paths, and invalid
line ranges are rejected locally. Markdown-wrapped output is not silently fixed.

The reviewer JSON has exactly `schema_version: "castle-task-review/0.1"`,
`packet_sha256`, `worker_sha256`, `verdict` (`pass`, `needs_changes`, or `blocked`),
`reasons` (1..8 objects containing a `note` and valid `source_refs`), and
`uncertainties`. Both roles require an explicit assistant message. Native
response evidence is retained with redaction even if output validation fails.
Known credential echoes and recognizable key material are redacted, flagged,
and terminate that attempt; they never become accepted artifacts.

Schema validity, reviewer verdict, and human acceptance are distinct states.
The receipt's `schema_valid` concerns the worker ticket; a valid reviewer
artifact supplies its separate verdict. A passing review never accepts the
result. A human may explicitly accept a schema-valid worker despite a critical
or missing review; that decision is recorded as human judgment, not a reviewer
pass. Incomplete accounting still makes cost-per-accepted-result unavailable.

## Local artifacts and offline conveniences

An authorized future `run` uses the same `--config` argument and reads only the
existing OpenRouter environment binding or hidden local key prompt. Never put
keys in configuration, packets, notes, command arguments, or chat.

Runs live under ignored `.task-runs/<task_id>/<unique_attempt_id>/`:

- `packet.json` and `plan.json`: frozen evidence and dated estimates.
- `worker.json`, `review.json`: created only after respective local validation.
- `receipt.json`: calls, native redacted evidence, requested/returned IDs,
  generation IDs, timings, usage, reported costs, errors, STOP reason, packet
  and artifact hashes, and the three independent result states.
- `manifest.json`: current attempt state and file hashes; written before each
  transport call so interrupted/uncertain attempts remain discoverable.
- Optional `decision.json` and `z-review-packet.json`: offline conveniences.

Each explicit run creates a new attempt. Artifacts and decisions are never
overwritten; only the attempt's receipt and manifest advance atomically via
temporary files. These two metadata files are not one database transaction:
an interruption between writes can leave a hash mismatch, which blocks further
spending rather than guessing. Hashes detect corruption, not a malicious editor
who can rewrite both files. Keep the local ledger; deletion loses local spend
history and is not an accounting reset supported by this CLI.

A per-task `.active` file prevents concurrent runs. A killed process can leave
it behind. Inspect its manifest/native evidence and provider account before
manually resolving a stale lock. There is deliberately no automatic lock
removal, resume, uncertain-request replay, or accounting-repair command in v0.

The run summary supplies `run` and the `worker.json` SHA-256. Using those values:

```sh
python castle/project_tasks.py export-z --run TASK_ID/ATTEMPT_ID
python castle/project_tasks.py accept --run TASK_ID/ATTEMPT_ID --artifact-sha256 WORKER_SHA256 --note "Reviewed locally"
python castle/project_tasks.py reject --run TASK_ID/ATTEMPT_ID --artifact-sha256 WORKER_SHA256 --note "Needs a narrower proposal"
python castle/project_tasks.py report
```

Choose **one** accept/reject operation per artifact; the second fails rather
than overwriting the first. Exports are self-contained packet sources, worker
output, hashes, and the review contract; they do not contact Z or claim Z has
reviewed anything. Export, accept/reject, and report never prompt for keys or
call a provider. They validate saved hashes before use. Notes are optional and
bounded to 1000 characters. A changed/tampered artifact cannot be accepted
using its old hash.

The report sums every recorded charge, including failures/rejections, and
counts distinct human-accepted worker hashes. It returns cost per accepted
result only if at least one result is accepted and all accounting is complete.
No acceptance means an explicit null ratio; missing/corrupt/in-flight accounting
means an explicit incomplete state. A failed or rejected result is not free
merely because it was unsuccessful. Provider-reported costs are observations,
not an independently reconciled account bill.

## Verification and design provenance

Run `python -m unittest discover -s tests -v` and the separate existing
`python -m unittest discover -s runtime-probe/tests -v`. Project-task tests use
offline provider fixtures and actual temporary packet/ledger files. No claim
of live compatibility or usefulness follows from these fixtures.

PR #6 (unmerged design commit `e7e19009c346ca25e2aec1ae53944a6ebe41277e`)
supplied reusable ideas: frozen source manifests, packet-hash binding,
bounded evidence references, explicit uncertainty, host-owned provenance,
and reviews bound to the exact artifact. This feature does not import its
20–40-question contract, MCP transport, model ladder, or orchestration design.
Mark remains the final gate. Worker proposals cannot edit repository files.
