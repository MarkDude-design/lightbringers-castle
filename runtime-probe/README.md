# Historical runtime probe

A small, separate Mistral managed-workflow project. The probe uses only the
Python standard library. The worker image installs the pinned workflow SDK at
build time; the probe itself installs nothing, downloads no checkpoints, and
does not connect to the historical council or any external service.

## What is ready

- `runtime_probe.py`: Python/platform, temporary-file lifecycle, child launch /
  output / termination, package discovery, and available memory/disk observations.
- `workflow.py`: one 45-second activity, maximum one attempt, with real work kept
  outside the replayed workflow. Workflow: `historical-runtime-probe-v1`.
- `worker.py`: managed-worker startup. The SDK handles platform authentication.
  Application code does not read credentials or environment-variable values.
  A fixed WARNING logging level suppresses the SDK's startup configuration dump;
  the probe still emits its own JSON events with the probe ID.
- `Dockerfile`, `pyproject.toml`, `requirements.lock`: build/dependency configuration.
- `prepare_deployment.py`: emits exact SDK keyword arguments without deploying.
- `deployment.schema.json`, `execution.schema.json`: actual installed SDK models.
- `tests/`, `evidence/`: seven passing tests, an actual local probe, offline SDK
  import/definition/schema/signature validation. No managed execution claimed.

`status: ok` on a package check means inspection succeeded; read
`module_discoverable` to see whether the package exists. Package import and model
inference are deliberately untested. Host-visible memory is not a container
quota. The separate cgroup check reports the visible mount-root limit, which
is not asserted to be this process's effective limit. Disk persistence is unknown.

## Run locally

Requires Python 3.12+. The probe alone needs no dependency installation:

```sh
python runtime_probe.py --output local-result.json
python -m unittest discover -s tests -v
```

The JSON result goes to stdout; probe-ID-tagged events go to stderr. Failed
capabilities remain individual records. Unsupported resource observations are
null with their actual error. A failed check does not discard other checks.
Subprocess code is fixed, bounded, and launched with an empty child environment.

To repeat SDK validation, install the pinned dependencies in a fresh virtual
environment, then run `python verify_sdk.py`. That command makes no API calls
and starts no worker. Do not run `worker.py` for an offline check: it is the
actual worker entrypoint and would attempt registration.

## Put these files in GitHub

This project lives in `runtime-probe/` in
`https://github.com/MarkDude-design/lightbringers-castle`. Use that directory as
the managed build context. Do not upload the temporary local test environment.
Deployment remains pending review.

Managed deployment can use a public or private github.com repository through
the Mistral GitHub App. The repository must be accessible to that App and the
selected Mistral account. There is no need to expose the entire historical
project. The repository URL is selected. Use the full commit SHA from the probe pull
request; Mistral GitHub App access still needs verification.

## Prepare exact deployment arguments

After the files are committed, run this with the real GitHub URL and full commit
SHA. Branches/tags are rejected. The example placeholders below are not values:

```sh
python prepare_deployment.py --repo https://github.com/MarkDude-design/lightbringers-castle --sha FULL_40_CHARACTER_COMMIT_SHA --build-directory runtime-probe
```

The build-directory argument above is required for this repository layout.
The command generates `deployment.args.json` and `execution.args.json`, including
a new probe ID. It performs no network calls and cannot deploy anything.
The deployment name defaults to `historical-runtime-probe`; choose a different
name with `--name` if it is already in use. The generator validates syntax;
it cannot verify that a SHA exists remotely or that the App can access it.

The arguments correspond to these actual SDK calls, after human review and
with an already authenticated client supplied by the caller:

```python
deployment = client.workflows.deployments.create_deployment(**deployment_args)
# Wait for this deployment/revision to become active and register the workflow.
execution = client.workflows.execute_workflow(**execution_args)
```

Create endpoint: `POST /v1/workflows/deployments`.
Execute endpoint: `POST /v1/workflows/historical-runtime-probe-v1/execute`.
SDK argument `workflow_identifier` is the execute path parameter; remaining
execution arguments are body fields. Retrieve the returned execution ID's
result and logs; match their probe ID to `execution.args.json`.

Z's `mistral_mcp.deploy_workflow_deployment` tool schema was not exposed in this
session. Its exact MCP argument mapping is therefore NOT claimed. The provided
arguments are checked against the real Mistral SDK, not guessed MCP parameters.

## Current evidence and limits

2026-10-10 local run: all ten inspection checks completed successfully; torch,
transformers and MCP were not discoverable in the isolated test environment.
Seven tests passed, including error isolation and real child cleanup. The real
workflow SDK accepted the workflow definition and deployment/execute argument
shapes offline. `evidence/` contains these receipts with `context: local`.

Docker is unavailable in this test environment, so an image build/start and a
managed workflow execution remain untested. The Docker base image is a version
tag rather than a digest; Python dependencies are version-pinned, not hash-locked.
The source deployment must be pinned to its actual Git commit. No claim of a
bit-identical container rebuild is made.

Read `deployment-review.json` for the unresolved inputs. Deployment remains
pending human review. There are no schedules, model downloads, API keys in code,
credential-printing commands, or changes to the existing model council.

## Sources and schema provenance

Checked against `mistralai-workflows==3.10.0` and `mistralai==2.10.1` installed
from PyPI. Their dependencies are frozen in `requirements.lock`. The workflow
package constrains its client dependency to <3; this tested pair is used even
though current website examples mention a newer client major version.

- https://docs.mistral.ai/studio/workflows/getting-started/your_first_workflow
- https://docs.mistral.ai/studio/workflows/building-workflows/activities/basics
- https://docs.mistral.ai/studio/workflows/managing-workflows-in-production/managed-deployments/getting-started
- https://docs.mistral.ai/studio/workflows/managing-workflows-in-production/managed-deployments/how-it-works
- https://pypi.org/project/mistralai-workflows/3.10.0/

Managed workers require workflow SDK 3.10+ for platform service-account token
support. The SDK reads those credentials for transport; the probe does not.
