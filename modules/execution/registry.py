from .engine import WorkflowEngine

_engines: dict[str, WorkflowEngine] = {}

def get_engine(workflow_id: str) -> WorkflowEngine | None:
    return _engines.get(workflow_id)

def set_engine(workflow_id: str, engine: WorkflowEngine):
    _engines[workflow_id] = engine

def remove_engine(workflow_id: str):
    _engines.pop(workflow_id, None)

def list_engines() -> dict[str, str]:
    return {wid: eng.status for wid, eng in _engines.items()}