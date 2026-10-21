# Room-registry bounded batch: validated pair, changes required

## Outcome and evidence boundary

On 2026-10-20 UTC, Mark authorized up to three new proposal-only attempts,
at most six inference calls total, within the original cumulative $0.05 local
budget for `room-registry-error-ticket-v0`. The batch stopped after **attempt 1,
two calls**: a schema-valid worker ticket and valid reviewer response were
retained. Reviewer verdict: **`needs_changes`**. This is a completed proposal
transaction, not an accepted artifact or implemented repair. The remaining two
attempts were not used; reaching a valid pair closes this authorized batch.

Source main: `333168088a6db1f7e9ba5ef0991b4b79f7b5b7f1` (PR #16 merged).
Configuration: `specs/tasks/room-registry-enumeration-ticket-paid-gpt-oss-20b-low-reasoning.json`.
Merged prompts, source bytes, task ID, configuration, models, and validation
were unchanged throughout the attempt. Both roles requested
`openai/gpt-oss-20b`, low reasoning, and at most 2,048 completion tokens per call.
These are separate calls to the same model, not independent model-family review.
Required-parameter enforcement and disabled provider fallback remained enabled.

The earlier three failures and all 12 of their saved files were verified before
and after this batch. No costs, unknowns, locks, or prior receipts were reset.
The separate Astra offline proposal was not sent to either model or inserted
into the ledger. Its external inference usage/cost is unavailable here; it is
not a zero-cost or accepted live result. Raw/private runs remain outside Git;
this document summarizes inspected local receipts, not Meraki's independent
inspection of private evidence.

## Proposal and review

The worker identified the `room_paths` enumeration race before `read_room`'s
read-time handler. It proposed catching `FileNotFoundError` around the size
`stat()` and skipping that candidate, preserving the existing symlink/size
eligibility and return type. Proposed checks cover disappearance after
`is_file()` and the already handled disappearance after enumeration at read time.
These checks were proposed, not executed against a repair. Worker scope lists
only `castle/room_tools.py`; its citation spans that whole source, lines 1..125;
its `uncertainties` is empty.

The review returned `needs_changes`. Its sole reason restates that the unguarded
size-stat can raise after `is_file()`; it does **not** identify what revision to
the worker proposal is needed. Both artifacts satisfy their existing schemas,
exact packet/artifact hashes, assistant-role, identity, and citation bounds.
Schema validity does not establish substantive acceptance.

Host findings for architecture/human review, separate from the model artifacts:

- The worker omitted the requested explicit credit to the **host finding**.
  It did not independently discover or execute the host's synthetic probe.
- Catching only `FileNotFoundError` leaves other enumeration `OSError` failures,
  such as `PermissionError`, unaddressed. Coverage and skip/`unknown_room` policy
  need explicit implementation review; no policy or validator was changed here.
- Tests are proposed but the worker's `allowed_files` contains only production
  code. Do not implement outside that artifact's scope without an explicit revision.
- The current host-finding characterization in `tests/test_project_tasks.py`
  asserts that the enumeration exception escapes. A repair needs it transitioned
  to the chosen handled-result regression while preserving historical evidence.
  **Proposed implementation-scope amendment, not applied:** explicitly include
  that file as well as the relevant room-tool tests before implementing a ticket.
  It is outside the frozen packet's current two-file allowlist.
- The review's reason does not explain the `needs_changes` verdict or resolve
  these gaps. No reviewer pass, human acceptance, or repair readiness is claimed.

## Reported usage, identities, and costs

Both HTTP responses were 200, assistant messages were explicit, identities were
exact, native accounting was complete, and no credential echo was detected.

| Role | Prompt tokens | Completion tokens | Of completion: reasoning | Total tokens | Reported USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Worker | 10,749 | 352 | 29 | 11,101 | 0.000225162 |
| Reviewer | 11,017 | 242 | 57 | 11,259 | 0.000220086 |

Requested and returned model for **each** call: `openai/gpt-oss-20b`.
Generation IDs:

- Worker: `gen-1792539979-eXOE82qyyI1wardi0O7C` (37.845 seconds).
- Reviewer: `gen-1792540017-ydqVyyyYGICoiBwhYYhW` (20.866 seconds).

Actual provider-reported batch cost: **$0.000445248**.
Prior failed-attempt cost: **$0.000848214**.
Cumulative task cost: **$0.001293462**, four attempts, complete accounting.
Remaining local budget: **$0.048706538**. Accepted results: **0**;
cost per accepted result remains unavailable. Human acceptance: `not_recorded`.

The conservative two-call admission estimate was **$0.01539420**, not actual
spend. Three such estimates plus prior spend would have reserved $0.047030814;
only one attempt occurred. The $0.05 local admission/accounting budget is not
a guaranteed provider billing ceiling. Read-only postflight observed the existing
**$50 weekly key limit**, $49.998706538 key allowance remaining, and $10 total
credits with $0.001293462 account usage. Both key/account usage match the ledger.
No credential, account limit, credit, or billing configuration was changed.

## Preflight and offline verification

Fresh official endpoint metadata advertised nine compatible endpoints (eight
status 0); each eligible endpoint advertised `reasoning`, `response_format`,
and `max_tokens` with sufficient advertised completion capacity. The fresh model
catalog explicitly listed `low` among supported efforts. The official reasoning
guide was successfully retrieved. Advertisement is not a guarantee of valid
output or uniform provider behavior.

Component-wise conservative prices across all eligible advertisements, including
the status -2 endpoint, remained $0.075/M input and $0.30/M output. The existing
2026-10-20 configuration observation and rates were preserved, not date-refreshed.
Funding, the secure domain-bound key, original ledger, no STOP/lock, and the
remaining two-call reserve passed before dispatch. Receipts retain the
requested low reasoning and unchanged provider controls as request evidence.

Before inference, `python scripts/verify.py` passed all eight groups on Linux,
Python 3.12.14, Node v24.19.0: 91 conversation/project/verifier tests plus 13
runtime-probe tests (**104 total**), no failures/errors/skips/expected failures;
13 Python files compiled, 30 JSON files parsed, four JavaScript syntax checks,
two CLI help checks, and three diff-whitespace checks passed. Receipt-only
verification and hosted CI results are recorded in the draft PR after inspection.
Offline checks and hosted CI do not establish live model acceptance.

## Preserved artifacts and next gate

Run: `.task-runs/room-registry-error-ticket-v0/7ed26377d68841899d68ad0d8923464a/`.

- Packet SHA-256: `bd03f4c828119910546fc8c27cae61ef8460dcd2a59cbe5ec0ea985120e4131d`.
- Worker SHA-256: `28f025b3bc08154147770577c633299338b72832861321619128e23d0e3e8d49`.
- Review SHA-256: `9f1b0edf2239ed72d394cd275f2ec78c161779f9d65c51d05e374bc8f93e46f2`.
- Offline Z packet SHA-256: `93e8c75b8796f1c43f74eb9b8893e6295b0a48a36d9d171c3943b8762aec3297`.

`export-z` completed offline with the existing validated worker; it contacted no
reviewer and is not proof of Z participation. Packet/worker/review bytes and all
prior files were unchanged by export. No human decision file exists. No further
attempt, repair, merge, deployment, or automatic acceptance was performed.

Next gate: Meraki reviews substance and implementation-scope proposals; Mark
owns human artifact acceptance and merge. Do not implement or accept this ticket
as-is merely because schemas and CI pass. Any revised implementation scope or
new inference attempt needs separate authorization.
