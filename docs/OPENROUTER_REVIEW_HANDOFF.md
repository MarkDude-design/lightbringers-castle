# Castle / OpenRouter review handoff for 5.6 Sol and Z
Prepared 2026-10-13. This document supplies the context needed to review the project without prior conversation.

## Mission and immediate objective
Mark is building Lightbringer's Castle: a human-hosted conversation/comedy space and a model council. Match Game-style premises let models contribute short answers, react, and expose both humor and misfires. Preserve genuine model output, including awkward or unsuccessful results. Do not impersonate an unavailable old model with a modern one.

Longer-term target: 100 inputs in a pool, more than half intended to come from frontier models, plus actual older-model outputs and separately labeled symbolic programs. This is a target, not a current count. Provider seats, calls, unique model IDs, and model families are different counts. Do not automatically label free/open-weight models as frontier models.

Immediate objective: get genuine OpenRouter/Groq conversation, then one real tool call with an auditable result. Mark has OpenRouter and Groq accounts. Credentials are supplied locally; never ask for keys in a chat or commit them. Hosting and Mistral deployment must not block this route.

## Repository and exact review baseline
- Repository: https://github.com/MarkDude-design/lightbringers-castle
- Current main inspected: `2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37`.
- PR #1 (runtime probe) and PR #2 (live chat) were merged.
- [PR #1](https://github.com/MarkDude-design/lightbringers-castle/pull/1), [PR #2](https://github.com/MarkDude-design/lightbringers-castle/pull/2).
- This handoff is documentation only; it does not introduce a tool runtime.
- Full source checkout:
```sh
git clone https://github.com/MarkDude-design/lightbringers-castle.git
cd lightbringers-castle
git checkout 2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37
```
The SHA is here for reviewers to reproduce the baseline; Mark does not need to manage it manually.

## All source and specification locations

### Live chat: read these first
- [castle/talk.py](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/talk.py) — complete standard-library API client, conversation loop, key entry, logging, STOP handling.
- [castle/TALK.md](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/TALK.md) — execution instructions and behavior.
- [tests/test_talk.py](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/tests/test_talk.py) — six offline fixture tests.
- [README.md](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/README.md), [.gitignore](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/.gitignore), [CONTRIBUTING.md](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/CONTRIBUTING.md).

### Runtime probe: separate subsystem
[Complete runtime-probe directory](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/runtime-probe):
- runtime_probe.py: Python/platform, temporary file lifecycle, child output/termination, package discovery and memory/disk observations.
- workflow.py: Mistral workflow/activity definition.
- worker.py: managed-worker startup.
- Dockerfile, .dockerignore, .gitignore, pyproject.toml, requirements.lock.
- prepare_deployment.py: offline argument generator.
- verify_sdk.py: installed SDK import/schema/signature validation.
- deployment.schema.json and execution.schema.json: generated installed-SDK schemas.
- deployment-review.json and README.md: deployment proposal and limitations.
- tests/test_probe.py.
- evidence/local-probe.json, local-probe.events.jsonl, sdk-verification.json, test-results.txt.

### Existing Castle content
- [castle/scripts](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/scripts): castle_engine.js, joke_mapper.js, personality_map.js, q_switch.js. Scripted content/overlays, not inference backends.
- [castle/bots](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/bots): character JSON and template; a BERT-named character file does not load BERT weights.
- [castle/rooms](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/rooms): room scenes, jokes and interactions.
- [registry](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/registry): bots.csv, bots_expanded.csv, rooms.csv, rooms_expanded.csv, assets.json. Entries do not establish live model availability.
- [castle/model_orchestration](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/castle/model_orchestration): constraints.md, lineage_map.md, orchestrator.md, routing_logic.md, safety_modes.md.
- [docs/repo_expansion.md](https://github.com/MarkDude-design/lightbringers-castle/blob/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/docs/repo_expansion.md); [prompts](https://github.com/MarkDude-design/lightbringers-castle/tree/2e8a039a9a0ad2d7087cf32415dbbf0a99f26a37/prompts): kickoff.md, generate_md.md.

### Workflow currently only on a separate branch
[.github/workflows/runtime-probe-test.yml](https://github.com/MarkDude-design/lightbringers-castle/blob/9ef817a294c197190649dcbdb7e14689b45c2b0a/.github/workflows/runtime-probe-test.yml)
is on codex/mistral-runtime-probe, not current main.
It runs tests, SDK validation and the runtime probe; it does not call language models.
Its fixed probe ID should become unique per run if this workflow is maintained.

## Current execution and API contract
Python 3.10+; standard library only. From repository root:
```sh
python castle/talk.py --interactive
```
Windows: `py -3 castle/talk.py --interactive`.

Inputs:
- --prompt: host text; default is a Match Game AI-butler premise.
- --rounds: 1, 2 or 3, default 2 per host cycle.
- --interactive: prompts for another human host turn after each cycle.
- --groq-model: default openai/gpt-oss-20b.
- --openrouter-model: default openrouter/free; explicit :free IDs also allowed.
- --output: default .talk-runs.
- --stop-file: default STOP in current directory.
- Hidden terminal key prompts, or GROQ_API_KEY / OPENROUTER_API_KEY. Enter skips a provider. At least one key required.
- No config file, REST server, browser frontend, streaming, images/audio or MCP listener in this runner.

Provider requests:
- POST https://api.groq.com/openai/v1/chat/completions
- POST https://openrouter.ai/api/v1/chat/completions
- Bearer credential in the authorization header only.
- JSON model/messages/stream:false.
- Groq: max_completion_tokens:1024; low reasoning effort for configured GPT-OSS models.
- OpenRouter: max_tokens:1024.
- No tools parameter and no tool execution.
- Hardcoded provider endpoints; redirects refused.
- One HTTP attempt per turn; no transport retries or paid OpenRouter fallback.
- A failing provider can still be called on its next scheduled turn.
- 45-second socket timeout, not a hard end-to-end deadline; 1 MiB success-body limit.
- OpenRouter call starts spaced at least four seconds apart.
- At most 12 API calls per process.
- Default two providers x two rounds = four calls, including two OpenRouter calls.

Conversation:
A shared list stores host messages and successful provider replies. For each receiving provider, its own prior seat replies become assistant messages; peer replies become labeled user messages. Failures are logged but not fabricated into dialogue.
The system prompt requests playful short panelist replies and explicitly says the model has no tools. Interactive Enter or /stop ends the session.

## Current result contract
Console displays actual replies and returned model IDs.
JSONL is written and flushed after each event under .talk-runs/<session_id>.jsonl; this folder is ignored by Git.

Events: session_started, call_started, call_finished, host_turn, session_stopped, session_finished.
A call_finished record contains:
```text
event, session_id, call_index, at,
provider, requested_model, returned_model,
source_kind="live_api", historical_model=false,
request={model,messages,stream,...},
status="ok"|"error"|"stopped",
text, usage, raw, error, http_status, retry_after,
finish_reason, elapsed_seconds, credential_redacted
```
- Native successful JSON is retained under raw. HTTP error bodies are retained as text.
- Missing usage/model metadata remains null.
- Known supplied credential values are replaced if echoed, and the record flags that replacement; therefore raw is not promised byte-identical.
- Actual model identity is the provider-reported ID, not a checkpoint attestation.
- The free router can return a different model on every turn. Two seats do not establish two unique models.
- Socket timeouts currently become status:error with exception details, not a separate timeout status.
- STOP file is checked between calls; Ctrl+C interrupts locally. Neither guarantees remote cancellation/refund.
- Exit 0 requires at least one successful reply and no errors; 1 otherwise; 2 for missing/cancelled key entry. STOP after success can still exit 0.
- Partial streamed generation is unavailable because streaming is disabled.

## Evidence, with its limits
- Six live-chat fixture tests passed during implementation on October 10. They cover free-ID restrictions/request parameters, peer attribution, native result identity, HTTP 429 without automatic retry, error isolation/key redaction, STOP-before-call.
- These are offline fixtures, not evidence that Groq/OpenRouter answered.
- Seven runtime-probe tests passed during implementation; ten local inspection checks completed.
- The local probe found torch/transformers/mcp absent. Successful package inspection does not mean installed/usable.
- [GitHub Actions run 38063390775](https://github.com/MarkDude-design/lightbringers-castle/actions/runs/38063390775) currently reports success on the probe branch.
- No live chat transcript or successful Mistral-managed execution has been verified in this conversation. Do not imply either.
- This handoff refreshed main, branch inventory, Actions status, and fully reread talk.py, TALK.md, test_talk.py, runtime-probe README, workflow.py and deployment-review.json. It did not freshly re-audit every file or rerun all tests.

## Mistral probe contract and authorization correction
Workflow name: historical-runtime-probe-v1.
Input: {"probe_id":"unique-per-execution-id"}.
One runtime-capability-checks activity, 45-second start-to-close limit, maximum one attempt.
Result: structured checks with actual errors and matching probe ID in logs.
SDK pair verified previously: mistralai-workflows==3.10.0 and mistralai==2.10.1.
Deployment build context: runtime-probe; Dockerfile: Dockerfile.
prepare_deployment.py requires an actual GitHub URL and full immutable commit SHA.
The exact SDK deployment/execution schemas are committed. Z's specific Mistral MCP argument schema was not available to this authoring session.

IMPORTANT: README/deployment-review still say human deployment approval is missing. Mark subsequently explicitly authorized deploying and running this probe. That item is stale; do not ask again merely because the old document says pending. Account access/tool availability and actual deployment evidence remain unresolved. Authorization did not include downloading checkpoints or connecting the historical server.
Managed historical inference remains a candidate conditional on observed capabilities.

## Historical council context: do not confuse it with this repo
Earlier project work discussed council.py, match_game.py, council_batch.py, mcp_server.py, registry.json and checkpoints.lock.json, with native historical inference, STOP fixes and a normalization wrapper.
Those files are NOT in the inspected Castle tree. That implementation and its reported checkpoint runs are separate prior artifacts, not evidence reproduced here. Recover and inspect them before integrating.
Do not treat the CLI's JSONL as the full historical batch envelope: it lacks the historical statuses and unattempted-row accounting.
Symbolic programs must keep their own provenance; old model checkpoints must remain actual checkpoints.

## Next feature: proposed OpenRouter tool loop, not implemented
Start with one local read-only tool, rather than a deployment project.
Proposed tool catalog:
1. list_rooms({}) -> room IDs from castle/rooms/*.json.
2. read_room({"room_id":"courtyard"}) -> the existing room JSON.
3. Later: list_bots({}) and read_bot({"bot_id":"..."}) -> registry/character metadata labeled as descriptions, not model output.

Example PROPOSED function specification:
```json
{
  "type": "function",
  "function": {
    "name": "read_room",
    "description": "Read a Castle room's stored scene data.",
    "parameters": {
      "type": "object",
      "properties": {"room_id": {"type": "string"}},
      "required": ["room_id"],
      "additionalProperties": false
    }
  }
}
```
Validate room_id against the enumerated room registry, not arbitrary filesystem paths.
Suggested tool result: {"ok":true,"data":{...},"error":null}; preserve structured errors on failure.

Required client behavior:
- Opt-in tool mode; change the current no-tools system prompt only in that mode.
- Select a currently available free model that supports tools. For attributable evaluation, prefer a named model over random routing.
- Send JSON tool schemas in every tool-enabled request.
- Preserve the assistant's complete tool-call message, IDs and model-specific metadata needed for continuation.
- Accept tool_calls with null content; current complete() rejects those.
- Validate tool names and arguments; execute only registered local handlers.
- Append role:tool results using matching tool_call_id, then request the model's answer.
- Keep each tool transaction with the same named model; don't route its continuation randomly to another model.
- Count every inference continuation toward the existing call cap; add a separate small tool-execution cap.
- Log requested arguments, actual handler result, status, elapsed time and IDs separately from generated text.
- No arbitrary Python/shell execution, user-controlled URLs, filesystem writes or model-invented handler names for this first increment.

Current OpenRouter reference:
https://openrouter.ai/docs/guides/features/tool-calling
It documents client-side execution and tool_call_id-linked responses. OpenRouter routes model requests; our client must execute the local functions. An MCP bridge is a later transport option, not a prerequisite for this first tool.

## Review priorities and acceptance
5.6 Sol: inspect the Python client and implement the smallest tool-loop change after review. Check tools-only results, response shapes, bounded calls, credential handling and error isolation.
Z: review API/tool schemas, actual-vs-requested identity, STOP/error semantics, and decide whether a Mistral workflow adds value later.
These are proposed reviewer assignments; no agent has been contacted or review completed by this handoff.

Concrete concerns to assess:
- Provider-seat history treats prior OpenRouter output as the same assistant even if the free router changes models.
- Adding tools must preserve native assistant messages rather than rebuilding history from text alone.
- Context length grows with host input; the 12-call cap is not a token-budget guarantee.
- Errors/HTTP 429 currently repeat on later scheduled turns; decide whether to suspend that provider for the session.
- Raw preservation has limits: oversized successful bodies are rejected without retaining their body, HTTP error bodies are capped, and credential redaction changes bytes.
- CLI invalid-input/EOF/log-write failures are not uniformly normalized.
- Live account/model compatibility still needs a real call.

Smallest success receipt:
One real OpenRouter answer, one model-requested read_room call, one actual local room JSON result, and one follow-up model answer referencing that result. Capture selected/returned model, inference ID, tool-call ID, usage if supplied, and actual errors. A tools-only fixture test can support this, but cannot replace the live receipt.
Mark should need at most one local command and hidden key entry. Do not send him another chain of provider/deployment handoffs.
