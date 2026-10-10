"""All observable work is in one bounded activity, outside replayed workflow code."""
from datetime import timedelta
import mistralai.workflows as workflows
from runtime_probe import run_probe


@workflows.activity(name='runtime-capability-checks',
                    start_to_close_timeout=timedelta(seconds=45),
                    retry_policy_max_attempts=1)
async def inspect_runtime(probe_id: str) -> dict:
    return run_probe(probe_id,context='mistral_workflow_activity')


@workflows.workflow.define(name='historical-runtime-probe-v1')
class RuntimeProbeWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, probe_id: str) -> dict:
        return await inspect_runtime(probe_id)
