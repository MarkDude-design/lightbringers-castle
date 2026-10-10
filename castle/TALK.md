# Make the Castle talk

Run from the repository root in a normal terminal with Python 3.10 or newer:

```sh
python castle/talk.py --interactive
```

On Windows, use `py -3 castle/talk.py --interactive` if `python` is unavailable.
No pip install, Docker, paid host, or Mistral deployment is required.

The program prompts for a Groq API key and an OpenRouter API key with hidden
input. Enter skips a provider; one key is enough to start. Both keys produce a
two-provider conversation. Keys remain in process memory and are not saved.
Already-configured `GROQ_API_KEY` / `OPENROUTER_API_KEY` environment variables
also work. Do not paste keys into chat, source code, or command-line arguments.

Create keys if you have accounts but have not created API keys yet:

- Groq: https://console.groq.com/keys
- OpenRouter: https://openrouter.ai/settings/keys

The default starts a Match Game premise. Each provider sees the host and the
previous replies, then contributes its own turn. After two rounds, interactive
mode lets you add another host message. Enter or `/stop` ends the conversation.
Use `Ctrl+C` to interrupt an in-flight request. A `STOP` file in the current
directory is checked between calls; it cannot cancel a request already sent.

For a single automatic conversation:

```sh
python castle/talk.py --prompt "The castle hired an AI chef. What went wrong at breakfast?"
```

Defaults: Groq `openai/gpt-oss-20b`, OpenRouter `openrouter/free`, two rounds,
up to 1,024 completion tokens per call, no retries, at most 12 calls per process.
There is a 45-second socket timeout and a 1 MiB response-size limit. These are
API replies, not local model downloads. No model tool execution is enabled.

OpenRouter's free router can choose a different underlying model each turn.
The console and JSONL record the returned model ID separately from the
requested router. Two provider seats do not guarantee two different models.
For a stable OpenRouter seat, supply an available named `:free` model with
`--openrouter-model`. Paid OpenRouter model IDs are rejected. Groq model access
and charges depend on your account; use your Free plan for this experiment.
No automatic model fallback or account upgrade is performed.

Transcripts are saved under `.talk-runs/` (ignored by Git). They retain the
request messages, actual text, returned identity, native response, usage when
reported, HTTP errors, timings and unique session/call identity. Known supplied
API-key values are redacted if a provider echoes them; records flag any such
redaction. Error bodies are retained, but authorization headers are never saved.
Failed calls do not become invented dialogue. Outputs are labeled `live_api`
and `historical_model: false`; this does not claim any model is frontier-class.
Transcripts are not uploaded or committed by this program. As conversation
history, each successful reply is sent to the other selected provider.

The existing Castle character JSON and overlays remain scripted content. This
runner uses its own experimental comedy prompt and does not present a modern
API model as BERT, GPT-2, Meraki or another named historical/persona slot.

## What is actually verified

The provider protocol and error/provenance behavior are covered by offline
fixture tests (`python -m unittest discover -s tests -p 'test_talk.py' -v`).
Fixture text is not evidence of model execution. No live account call was run
when this feature was authored: neither API key was available to the authoring
session. Your first terminal run supplies that missing live evidence.

The runtime-probe GitHub Actions run succeeded on the probe branch, but it
does not call a model. This runner supplies the missing API connection.

## Provider references checked 2026-10-10

- https://console.groq.com/docs/models
- https://console.groq.com/docs/api-reference
- https://console.groq.com/docs/rate-limits
- https://openrouter.ai/docs/guides/routing/routers/free-router
- https://openrouter.ai/pricing

Free availability and limits can change. OpenRouter advertises 50 requests/day
on the free plan; Groq limits vary by model/account. HTTP 429 and Retry-After
are preserved in the transcript; there is no automatic retry loop.
