# First room-registry task: paid-model preflight

Status: **blocked before inference**. Preparation checked current main at
`2ee59ec13a8344f85960a87499f374b62237e379`, including PR #8's shared ledger-lock
and canonical task-identity repairs. No runner or generated repair code changed.

The host authorized exactly one attempt, at most two inference calls, and a
$0.05 local task budget. This does not authorize retries, another attempt,
automatic human acceptance, implementing the proposed ticket, merge, deployment,
an account upgrade, or adding credits. No live attempt has started here; its
authorization has not been used to send a request.

## Prepared configuration

`specs/tasks/room-registry-ticket-paid-gpt-oss-20b.json` preserves the original
task in full, including logical task ID `room-registry-error-ticket-v0`, source
files, allowed files, goal, criteria, and boundaries. Both worker and reviewer
explicitly request `openai/gpt-oss-20b`, with paid opt-in, a $0.05 shared local
task budget, and 2,048 completion tokens per call. These are two roles calling
the same model, not independent model-family review.

The runner continues to send `response_format: {"type": "json_object"}`,
`provider.require_parameters: true`, and `provider.allow_fallbacks: false`.
No provider endpoint is pinned. No JSON/output validation, identity check,
ledger check, STOP behavior, or accounting rule has been weakened.

**Pricing is intentionally `{}`.** Missing prices remain null and dry-run/run
fail closed. There is no current supported-endpoint set from which to compute
an honest conservative price envelope. Do not substitute historical free-route
costs, the cheapest paid endpoint, a guessed rate, or zero. The $0.05 budget is
not a price estimate and does not establish that the task fits the budget.

## Official metadata checks and eligibility

Read-only GET requests on October 19, 2026 PDT (October 20 UTC) targeted:

- https://openrouter.ai/api/v1/models/openai/gpt-oss-20b/endpoints
- https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints

Both failed during proxy CONNECT with **HTTP 403 Forbidden**, before an
OpenRouter endpoint response. No official endpoint capabilities or current
rates were returned, so neither model was freshly qualified. Do not describe
this network denial as model incompatibility or lack of account credits.

Before admission, retrieve current official endpoint metadata and retain its
retrieval timestamp and source URL. Inspect the active endpoints' advertised
supported parameters for `response_format` and `max_tokens`, including any
more specific advertised response-format restrictions. The requested format
is `json_object`; evidence for tool calling or JSON Schema alone does not
establish compatibility with this exact request. `model`, `messages`, and
`stream: false` are the standard chat envelope; the provider routing controls
remain enforced by OpenRouter. Do not silently change them for compatibility.

Across **all eligible endpoints**, convert prompt/completion prices from their
documented units to USD per million tokens. Use the maximum eligible prompt
rate and maximum eligible completion rate as the component-wise conservative
envelope, even if those maxima come from different providers. Record the
eligible provider set, rates, source, and observation date. Consider any other
advertised request/fee components: if they cannot be bounded honestly by the
runner's existing two-rate estimate, keep preflight blocked rather than hide
them. Missing eligibility or price data is not zero. No endpoint-price table
is supplied here because none could be observed.

Only after that check passes should the configuration's one pricing entry for
`openai/gpt-oss-20b` be populated with `observed_on`, a source description naming
the endpoint envelope, `input_usd_per_million`, and `output_usd_per_million`.
Keep endpoint observations no older than seven days; rerun dry-run against the
existing task ledger. A local byte-based estimate is not a native tokenizer
or a guaranteed provider bill. An unexpectedly expensive completed request
can exceed the local estimate before the host sees its reported cost.
**Existing provider-side key caps are the spending backstop.**

## Why the original free example is unqualified

The original configuration used `nvidia/nemotron-3.5-lightning:free` after a
successful room-tool transaction. That transaction requested a tool call and
grounded prose, not `response_format: {"type": "json_object"}`. Its zero cost
and tool-call success do not qualify the project-task structured-response
contract. Current free-model endpoint metadata was blocked as described above.
We therefore have no fresh confirmation of compatible endpoints. This is an
evidence gap, not an assertion that its endpoints definitively lack the
parameter. The original free example is retained as historical material; its
validation must not be weakened to turn it into a qualified transaction.

## Credential and local ledger checks

This process has no `OPENROUTER_API_KEY` binding available through the runner's
existing environment mechanism. No other credential route was tried, and no
key was requested, printed, copied, or changed. Existing provider-side credit
caps are **unobservable here** without that approved credential; no account or
key limit was inspected or changed. A previously discussed personal key/limit
is not evidence of this process's current credential or spending backstop.

This checkout has no `.task-runs` directory, STOP file, or active/stale task
lock. Its read-only task report shows zero local attempts, $0 recorded spend,
complete empty-ledger accounting, zero accepted results, and no cost-per-accepted
result. That describes this checkout only, not Mark's Windows ledger or an
independently reconciled provider account. Preserve the existing task ID and
any local ledger; do not use a new task ID, new empty checkout, case alias,
or deleted history to bypass prior costs or unresolved attempts.

## Offline preparation and conditional Windows command

Dry-run uses the paid configuration and deliberately exits 1 with null
estimates and `can_run: false` while prices are missing. It makes no provider
request and does not prompt for credentials. The existing regression suites,
Python compilation, JSON/JavaScript checks, CLI help, and diff checks are run
before this preparation is handed back. No new feature or runner change is
needed to represent missing pricing honestly.

After official endpoint/pricing preflight has actually passed, dry-run confirms
the estimate plus prior recorded task spending fits $0.05, and there is no
uncertain ledger or active/stale lock, Mark can run this **once** from the
prepared Git checkout on Windows, keeping its existing `.task-runs` history:

```powershell
py -3 castle/project_tasks.py run --config specs/tasks/room-registry-ticket-paid-gpt-oss-20b.json
```

If a valid key is not already in the existing OpenRouter environment binding,
the runner uses hidden terminal entry. Never put a key into the command, config,
packet, note, source, chat, or logs. The command is not currently ready to spend:
with this checked-in empty pricing map it stops before key entry/inference.
Do not rerun it after an uncertain, failed, timed-out, incomplete-accounting,
or malformed-output attempt. Preserve the receipt and inspect the failed
attempt, known charges, hashes, and account evidence before proposing any
separate recovery or new authorization. Do not automatically clear a lock or
repair the ledger.

On a permitted terminal attempt with a validated worker, export the
self-contained Z packet offline, without contacting Z. Keep human acceptance
unset. Provide the ticket, reviewer verdict/reasons, packet/worker hashes,
requested/returned identities, generation IDs, reported usage/cost versus the
estimate, run path, and the artifact-bound offline accept/reject commands.

No worker or review artifact exists from this preparation. Consequently there
is no Z export or accept/reject command tied to a real artifact yet. The next
safe check is official endpoint metadata access and compatible conservative
pricing, followed by secure local credential availability—not another model
request or an invented live success receipt.
