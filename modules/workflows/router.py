from fastapi import APIRouter
from typing import List
from .schemas import WorkflowDocument, WorkflowCreate, WorkflowUpdate, WorkflowResponseShort
from .service import WorkflowService

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

@router.get("/", response_model=List[WorkflowResponseShort])
async def list_workflows():
    return await WorkflowService.get_all_workflows()

@router.post("/", response_model=WorkflowDocument)
async def create_workflow(data: WorkflowCreate):
    return await WorkflowService.create_workflow(data)

@router.get("/{workflow_id}", response_model=WorkflowDocument)
async def get_workflow(workflow_id: str):
    return await WorkflowService.get_workflow(workflow_id)

@router.put("/{workflow_id}", response_model=WorkflowDocument)
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    return await WorkflowService.update_workflow(workflow_id, data)

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    return await WorkflowService.delete_workflow(workflow_id)