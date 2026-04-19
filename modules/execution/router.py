import asyncio
import json
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from modules.workflows.service import WorkflowService
from .engine import WorkflowEngine
from .registry import get_engine, set_engine, remove_engine, list_engines

router = APIRouter(prefix="/api/execute", tags=["Execution"])


class RunRequest(BaseModel):
    payload: Optional[Any] = None


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, request: RunRequest = RunRequest()):
    doc = await WorkflowService.get_workflow(workflow_id)

    nodes = [n.model_dump() for n in doc.nodes]
    edges = [e.model_dump() for e in doc.edges]

    engine = WorkflowEngine(workflow_id, nodes, edges)
    set_engine(workflow_id, engine)
    engine.start(request.payload)

    return {"status": "started", "workflow_id": workflow_id}


@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    engine = get_engine(workflow_id)
    if not engine:
        raise HTTPException(status_code=404, detail="No running workflow found")
    engine.stop()
    remove_engine(workflow_id)
    return {"status": "stopped", "workflow_id": workflow_id}


@router.get("/{workflow_id}/status")
async def get_status(workflow_id: str):
    engine = get_engine(workflow_id)
    if not engine:
        raise HTTPException(status_code=404, detail="No execution found for this workflow")
    return engine.get_state()


@router.get("/{workflow_id}/stream")
async def stream_status(workflow_id: str):
    engine = get_engine(workflow_id)
    if not engine:
        raise HTTPException(status_code=404, detail="No execution found for this workflow")

    async def event_generator():
        sent = 0
        while True:
            state = engine.get_state()
            logs = state["logs"]

            while sent < len(logs):
                entry = logs[sent]
                yield f"data: {json.dumps(entry)}\n\n"
                sent += 1

            if state["status"] in ("completed", "error", "stopped"):
                yield f"data: {json.dumps({'event': 'done', 'status': state['status']})}\n\n"
                break

            await asyncio.sleep(0.2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/")
async def list_running():
    return {"engines": list_engines()}