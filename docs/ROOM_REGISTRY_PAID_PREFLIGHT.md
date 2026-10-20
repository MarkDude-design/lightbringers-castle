# First room-registry task: paid-model preflight

Status: **public metadata/pricing preflight passed; live execution not attempted**. Original preparation checked main at
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

Pricing was initially missing because the original environment could not reach
the metadata endpoint. That failure remains recorded below. A later public
metadata read succeeded through the research connection, and the configuration
now contains the component-wise conservative endpoint envelope documented here.
Missing pricing still blocks spending; it has not been converted to zero.

## Successful public metadata follow-through

Observed at **2026-10-20T05:25:31.984934+00:00** from the official
[model endpoint metadata](https://openrouter.ai/api/v1/models/openai/gpt-oss-20b/endpoints).
The normalized observation is retained in
[`evidence/gpt-oss-20b-endpoints-20261020.json`](evidence/gpt-oss-20b-endpoints-20261020.json).

Nine endpoints advertise both `response_format` and `max_tokens`.
OpenRouter's [parameter reference](https://openrouter.ai/docs/api/reference/parameters)
defines `response_format: {"type":"json_object"}` as JSON mode; no narrower
format restriction appears in the returned endpoint entries. Both Amazon
Bedrock entries were excluded because they do not advertise `response_format`.

| Eligible provider | Input USD / million tokens | Output USD / million tokens |
|---|---:|---:|
| Darkbloom | 0.018 | 0.09 |
| AkashML | 0.02 | 0.10 |
| DekaLLM | 0.029 | 0.14 |
| CoreWeave | 0.03 | 0.13 |
| DeepInfra | 0.03 | 0.14 |
| Parasail | 0.03 | 0.15 |
| SiliconFlow | 0.04 | 0.18 |
| Google | 0.07 | 0.25 |
| Groq | 0.075 | 0.30 |

The component-wise maxima are **$0.075 input / $0.30 output per million
tokens**. Prompt/completion fields were converted from USD per token. All
advertised cache-read rates are at or below the corresponding prompt rate;
discount fields are zero. No additional request-fee component appears in these
returned pricing objects. This snapshot is not a guarantee against later rate,
capability, routing, or billing changes. Provider-side key caps remain the
backstop, and missing later usage still blocks further spending.

The configuration's two-call byte-based estimate is **$0.0150969** with an
empty local task ledger, below the authorized **$0.05** local task budget.
That is a conservative local estimate, not an observed charge or live proof
that the model will produce valid ticket/review outputs. No inference call,
key lookup, account-cap lookup, or human acceptance was performed during this
follow-through.

## Official metadata checks and eligibility

Read-only GET requests on October 19, 2026 PDT (October 20 UTC) targeted:

- https://openrouter.ai/api/v1/models/openai/gpt-oss-20b/endpoints
- https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-lightning:free/endpoints

In the original environment, both failed during proxy CONNECT with **HTTP 403
Forbidden**, before an OpenRouter endpoint response. No capabilities or rates
were returned there. The later successful paid-model metadata observation above
supersedes that metadata-access blocker without erasing the original failure.
Do not describe the proxy denial as model incompatibility or lack of credits.

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
them. Missing eligibility or price data is not zero. The observed table above
supplies this check for the dated paid-model snapshot.

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

The original authoring process reported no `OPENROUTER_API_KEY` binding through
the runner's existing environment mechanism. The later metadata follow-through
did not inspect or transfer credentials and made no authenticated provider
call. No other credential route was tried, and no key was requested, printed, copied, or changed. Existing provider-side credit
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

The original dry run correctly exited 1 with null estimates while prices were
missing. After the successful metadata follow-through, the paid configuration's
dry run passes against an empty local ledger with the estimate above. It makes
no provider request and does not prompt for credentials. Independent offline verification of this follow-through passed: **70 tests**
(63 conversation/project-task tests and seven runtime-probe tests), Python
compilation, all **26 repository JSON files**, all **four JavaScript syntax
checks**, CLI help, and `git diff --check`. No new feature or runner change is
needed to represent missing pricing honestly.

The dated endpoint/pricing preflight above has passed. After Mark's local dry
run confirms that estimate plus prior recorded task spending fits $0.05, and
there is no uncertain ledger or active/stale lock, Mark can run this **once** from the
prepared Git checkout on Windows, keeping its existing `.task-runs` history:

```powershell
py -3 castle/project_tasks.py run --config specs/tasks/room-registry-ticket-paid-gpt-oss-20b.json
```

If a valid key is not already in the existing OpenRouter environment binding,
the runner uses hidden terminal entry. Never put a key into the command, config,
packet, note, source, chat, or logs. The configuration now admits the dated
estimate; actual execution still requires Mark's local ledger and secure key
checks. A successful local dry run does not prove the credential or account cap.
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
safe step is Mark's local ledger dry run and secure credential/account-cap
check using the qualified configuration. Preserve the one-attempt limit; do not
invent a live success receipt or run a second copy in another environment.
