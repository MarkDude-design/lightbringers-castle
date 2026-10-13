# Castle Sensor Trio

Three optional local checkpoints provide cheap, repeatable signals without
turning every comparison into an LLM conversation:

| Sensor | Checkpoint | Use | Not a claim of |
|---|---|---|---|
| `bert_fill_mask` | BERT base uncased | ranked single-token completions | truth or generation |
| `minilm_similarity` | all-MiniLM-L6-v2 | semantic similarity | agreement or authorship |
| `deberta_nli` | DeBERTa-v3-small NLI | bounded label ranking | fact, permission, or diagnosis |

**Sensors estimate. Gates decide.** Their results belong in telemetry and can
raise flags; they never authorize an action.

## Install and bootstrap

Use a separate virtual environment so the zero-dependency Castle talk runner
stays untouched:

```sh
python -m venv .venv-sensors
. .venv-sensors/bin/activate
python -m pip install -r requirements-sensors.txt
```

The default runtime is cache-only. The first execution of each sensor needs the
explicit `--allow-download` switch and downloads only the catalog-pinned model
revision. Subsequent runs omit the switch and work from the local cache.

```sh
python -m castle.sensors --allow-download fill-mask \
  --text "The chamber flight recorder is [MASK]." --top-k 5

python -m castle.sensors --allow-download compare \
  --left "The run completed and passed its checks." \
  --right "Deterministic validation succeeded."

python -m castle.sensors --allow-download classify \
  --template status --text "The tool timed out before returning data." \
  --label completed --label refused --label uncertain --label timed-out
```

Each result is JSON containing the exact model ID and immutable revision,
license, limits, elapsed time, claim ceiling, and result. The loader forces CPU,
disables remote model code, and requests `safetensors` weights. Model IDs,
revisions, operations, templates and output sizes are not caller-controlled.

Approximate checkpoint payload is 1.1 GB total. Installing PyTorch adds its own
disk cost. `requirements-sensors.txt` selects the CPU-only PyTorch build rather
than downloading an unused CUDA runtime. Model cards and licenses are linked in
`catalog.json`.

## Orchestrator boundary

Call `castle.sensors.execute_sensor()` with one of these fixed shapes:

```json
{"sensor":"bert_fill_mask","arguments":{"text":"A [MASK] door.","top_k":5}}
{"sensor":"minilm_similarity","arguments":{"left":"first text","right":"second text"}}
{"sensor":"deberta_nli","arguments":{"text":"input","labels":["a","b"],"template":"topic"}}
```

Unknown sensors, unknown fields, arbitrary model IDs, arbitrary hypothesis
templates, oversized text, duplicate labels and excessive label counts fail
closed before an ML library loads. This is the interface a later OpenRouter tool
adapter can wrap; the checkpoint runtime itself needs no API key and makes no
network request after bootstrap.

## Verification boundary

`tests/test_sensors.py` uses a fake backend. It verifies the allowlist, bounds,
provenance envelope and CLI catalog but is not evidence that checkpoint weights
executed. A real CPU/cache-only smoke run is recorded in
`evidence/smoke-20261013.json`; its timings are evidence for that host, not a
general benchmark. Repeat the smoke run on target hardware before deployment.
