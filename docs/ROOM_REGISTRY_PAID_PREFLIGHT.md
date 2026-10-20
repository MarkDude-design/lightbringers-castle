# First room-registry task: paid-model preflight

Status: **one funded live attempt failed at the completion cap; evidence and
reported cost preserved; no retry authorized**. The earlier funding blocker was
resolved before this attempt. No runtime or generated repair code changed.

The host authorized exactly one attempt, at most two inference calls, and a
$0.05 local task budget. That authorization has now been used by the single
attempt below. Its second call was never sent; it is not permission to retry
the worker. No additional attempt, automatic human acceptance, implementing
the proposed repair, merge, deployment, account upgrade, or adding credits is
authorized by this handback.

## Funded live attempt — 2026-10-20 UTC

After Mark independently funded the account, read-only preflight at
`2026-10-20T21:00:27Z` confirmed usable credit, the existing key allowance,
fresh paid endpoint metadata, and a complete empty local task ledger without
STOP or active/stale locks. No key value was inspected or copied. The fresh
component-wise pricing envelope remained $0.075 input / $0.30 output per
million tokens across all nine advertised-compatible endpoints, including
the nonzero-status entry. No provider was pinned or fallback enabled.

Source commit: `ff355ac1e1ce27c85dc898935c6c4710f1c2a97c`.
Task ID: `room-registry-error-ticket-v0` (unchanged).
Packet SHA-256:
`9d0432e5c77edd281132c5035d0c926cd72e1c3481e9f94f74f7c1e100da4de8`.

The single worker call requested and returned **`openai/gpt-oss-20b`** (exact
identity). It returned HTTP 200 but no final content and `finish_reason: length`.
Reported usage: **10,313 prompt tokens, 2,048 completion tokens, 12,361 total**;
completion details report **2,045 reasoning tokens**. Elapsed transport time was
108.998 seconds. The existing 45-second socket timeout is not a total runtime
limit. Native evidence was retained and output acceptance correctly failed.

The provider-reported cost was **$0.000369954** for one call, versus the
**$0.015096900 two-call estimate** and **$0.05 local accounting budget**.
These are different quantities; none is a guaranteed provider billing ceiling.
The recorded charge remains attached to this failed attempt. Accounting is
complete, but no worker ticket was validated; therefore no reviewer call,
reviewer verdict, worker hash, Z export, or artifact-bound human decision command
exists. Cost per accepted result remains unavailable. Human acceptance is unset.
The raw receipt, native response, source packet, and selected account evidence
remain outside Git. No request was retried and no ledger was repaired/reset.

**Next safe check:** Meraki/Mark review the preserved failed response and usage.
A separate authorization is needed for any new attempt. **Spec-change proposal,
not implemented:** consider an explicitly supported lower reasoning effort for a
future attempt while retaining the 2,048 completion cap, strict JSON validation,
identity checks, original task ID/ledger, and disabled fallback. Confirm endpoint
support first. This may reserve more completion capacity for final JSON but is
not proof it will succeed. Do not silently add a provider parameter, increase
the cap, substitute a model, or submit another request.

## Earlier cloud follow-through — 2026-10-20 UTC (historical funding blocker)

After PRs #9 and #10 merged, this checkout was based on
`127e257a418b958d018c9c1b56dc0d2a8e094539`. The platform reported the
OpenRouter network-secret binding ready and its network policy enforced.
Official paid/free endpoint metadata GETs now succeed; the prior proxy failure
below is historical evidence, not the current access state.

The [fresh public observation](evidence/room-registry-endpoint-preflight-20261020-followup.json)
retains retrieval timestamps, original response hashes, supported parameters,
endpoint statuses, and prices. Nine paid endpoints advertise `response_format`
and `max_tokens` with sufficient completion capacity. Eight report status `0`;
SiliconFlow reports `-2`. The conservative envelope still covers all nine,
including the nonzero-status entry, so its exclusion is not used to lower the
quote. Both Bedrock entries lack `response_format`. Rates remain **$0.075 input
and $0.30 output per million tokens**, based on a fresh observation rather than
a date-only refresh. No additional request-fee component appears in these
returned pricing objects.
This establishes advertised compatibility, not successful structured output.
The fresh parameter-document page fetch was denied (HTTP 403); the earlier
referenced JSON-mode contract was not newly reverified from that page.

The original free model's sole advertised endpoint supports tools and
`max_tokens`, but **does not advertise `response_format`**. It therefore does
not currently qualify for this runner's enforced JSON-mode contract. The
runner, model identity checks, provider fallback setting, and validators remain
unchanged; a free-model substitution is not an authorized compatibility repair.

Read-only authenticated key/balance preflight succeeded but found **no
available prepaid credit**, blocking the paid task. A key's spending allowance
is distinct from funded account balance; the **$0.05 local budget** is admission
and accounting, not a guaranteed provider billing ceiling. Private selected
balance/cap evidence is preserved outside Git with the handback. No credentials,
private run artifacts, or raw account responses are committed. No credits were
added, limits changed, or inference requests sent. The one-attempt authorization
remains unused; no worker ticket, reviewer response, Z export, or human decision
exists from this preflight.

The original task ID and task content are preserved. The local ledger is empty,
with complete accounting, zero accepted results, and no STOP or task lock. This
observation does not replace any separate local history. Offline checks passed
**87 tests** (74 conversation/project/verification tests and 13 runtime-probe
tests), with no skips, plus compilation, tracked JSON, four JavaScript syntax
checks, CLI help, and whitespace checks. The paid dry-run passes its local
estimate; it does not query funding or grant spending permission. Resolve the
funding prerequisite only through a separately authorized account decision,
then repeat read-only preflight against the original preserved ledger before
using the existing one-attempt command. Do not change task IDs or retry an
uncertain attempt.

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
contract. Its metadata was blocked at the original preparation, but the current
cloud follow-through above obtained it and found no advertised `response_format`
support. The original free example is retained as historical material; its
validation must not be weakened to turn it into a qualified transaction.

## Original credential and local ledger checks (historical)

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

## Offline preparation and original Windows command (historical)

**Do not execute the original run command under the spent authorization.** It
is retained below as the earlier handoff, not permission for another attempt.


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

No worker or review artifact exists from the failed live attempt. Consequently
there is no Z export or accept/reject command tied to a validated artifact. The
funded-attempt section above supersedes the original credential/funding blockers
and records the single used authorization. Preserve its charge and failure;
do not run another copy in this or a different environment.
