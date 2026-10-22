# Team workflow pilot: Puppy P0

The deliverable is a repeatable delegation workflow, with measurable efficiency by Christmas 2026. Puppy P0 is its first real build task. One implementation worker; no orchestration service before HELLO.

## Authority and routing

- Mark: final scope, authorization, and merge gate.
- Z / Mistral Vibe: coordinator, reviewer, spec compressor, and assignment tie-break. No claim that Z has already reviewed this packet.
- Meraki: technical assistance, bounded packets, evidence verification; does not replace Z as coordinator.
- Suggested cheaper GPT: `gpt-6-luna`, subject to account availability and Z's assignments. Use fresh context and only the named task inputs.

| Candidate lane | Why it fits | Escalation |
| --- | --- | --- |
| Bounded file inventory and exact constraint extraction | Read-only, checkable against named files | Missing/conflicting authority goes to Z |
| Documentation and receipt updates from verified output | Mechanical; narrow diff | No new design or unverified success claims |
| Build-log triage | Return first failure, evidence line, one proposed next check | Stop after two failed repair attempts or scope change |
| Small mechanical code/config change | Only after Z names files and tests | Boot architecture, ABI, and ambiguous failures stay with stronger worker/reviewer |
| Packet completeness review | Missing fields and inconsistencies are independently checkable | Cannot accept its own implementation or authorize merge |

Keep ordinary compilation, hashing, boot timing, log matching, and size measurement in scripts. Do not ask models to re-derive successful checks.

## First work order

`packets/PUPPY-P0A-001.json` is the self-contained worker input. Its companion `.sha256` hashes exact UTF-8 file bytes, including final newline. Verify before dispatch. Change the packet => create a new version/hash and new receipt; no silent edits during a run. A hash binds content, not authorship, truth, or authorization.

This work-order JSON is not a replacement for the existing 20–40-question networked schema on branch `codex/openrouter-mcp-team-spec-20261013`. That schema serves another purpose; do not import its MCP dependency into offline boot.

The first worker returns a patch/commit, build manifest, captured serial log, test results, image byte sizes/hashes, and a completed receipt. No success is accepted from prose alone. Z assesses routing and review; Mark gates merge. Results remain files in the shared repo; chat carries packet ID, commit, and hash only.

## Cost per accepted result

Record every attempt, including rejected attempts, retries, coordinator compression, review, repair, and paid tools/compute. One accepted P0a result means the complete acceptance suite passes and reviewer acceptance is recorded. Do not count separate HELLO lines or internal subtasks as separate accepted builds.

`cost_per_accepted_result = total_attributable_cost_usd / accepted_result_count` for a completed cohort of comparable work. Before any acceptance it is undefined, not zero. If any necessary cost is unknown, report null and list coverage; optionally report a clearly labeled observed-cost subtotal, never complete cost. No cost-savings claim without a comparable baseline.

For API runs retain provider usage evidence, input/cached-input/output/reasoning token fields as reported (do not double-count reasoning included in output), prices and their effective date, currency, and any tool charges. For subscription/hosted subagents without exposed usage, use null, record `unavailable`, and keep elapsed time, input/output bytes, repair count, and human intervention minutes separately. Bytes are not tokens. Missing usage is not free usage.

Each receipt binds task ID + exact packet SHA-256 + source base commit + requested/observed model + artifact hashes + test evidence + review decision. Time records are UTC observations; human minutes are self-reported, never inferred from elapsed time. Do not put secrets or workplace records in this workflow.

## December comparison

By 2026-12-25 compare like-for-like accepted tasks using cost coverage, total cost where measurable, elapsed time, human minutes, first-pass acceptance, repair attempts, and premium-model involvement. Use naturally occurring comparable tasks; do not spend extra money recreating a baseline merely to claim savings. P0a supplies the first observation, not proof of improvement.

## Current status

Packet preparation and one cheaper-GPT read-only review are the current workflow exercise. The actual image has not been built or booted by this change. Worker allocation and numeric spending cap remain Z/Mark decisions; the packet exposes those gates instead of silently assuming them. There is no merge, deployment, or physical-device writing in this packet preparation.
