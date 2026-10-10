"""Offline validation against installed SDK; no registration or API requests."""
import json
from pathlib import Path
import inspect
from importlib.metadata import version

# worker configures log suppression BEFORE importing the SDK.
import worker
from mistralai.client import models
from mistralai.client.deployments import Deployments
from mistralai.client.workflows import Workflows
from prepare_deployment import prepare


def verify():
    # Synthetic schema test data only. Not deployment targets.
    deployment,execution=prepare('https://github.com/example/probe','a'*40)
    models.CreateDeploymentRequest.model_validate(deployment)
    body={k:v for k,v in execution.items() if k!='workflow_identifier'}
    models.WorkflowExecutionRequest.model_validate(body)
    inspect.signature(Deployments.create_deployment).bind(None,**deployment)
    inspect.signature(Workflows.execute_workflow).bind(None,**execution)
    definition=worker.workflows.get_workflow_definition(worker.RuntimeProbeWorkflow)
    assert definition.name=='historical-runtime-probe-v1'
    root=Path(__file__).resolve().parent
    (root/'deployment.schema.json').write_text(json.dumps(models.CreateDeploymentRequest.model_json_schema(),indent=2)+'\n')
    (root/'execution.schema.json').write_text(json.dumps(models.WorkflowExecutionRequest.model_json_schema(),indent=2)+'\n')
    return {'sdk_import':'ok','workflow_definition':'ok','deployment_schema':'ok',
            'execution_schema':'ok','method_arguments':'ok',
            'mistralai_version':version('mistralai'),
            'workflows_version':version('mistralai-workflows'),
            'network_calls':0,'worker_started':False,'deployed':False}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
