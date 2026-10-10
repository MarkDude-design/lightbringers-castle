"""Managed worker entrypoint. Authentication is handled by the SDK."""
import asyncio
import os

# Set a fixed logging level before SDK import: its INFO startup log dumps its
# configuration. Do not read, enumerate, or print environment values here.
os.environ['LOG_LEVEL']='WARNING'

import mistralai.workflows as workflows
from workflow import RuntimeProbeWorkflow

if __name__=='__main__':
    asyncio.run(workflows.run_worker([RuntimeProbeWorkflow]))
