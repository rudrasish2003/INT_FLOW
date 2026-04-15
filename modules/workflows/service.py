from fastapi import HTTPException
from typing import List
from .schemas import WorkflowDocument, WorkflowCreate, WorkflowUpdate
from .repository import WorkflowRepository

class WorkflowService:
    @staticmethod
    async def get_all_workflows() -> List[WorkflowDocument]:
        return await WorkflowRepository.get_all()

    @staticmethod
    async def get_workflow(workflow_id: str) -> WorkflowDocument:
        workflow = await WorkflowRepository.get_by_id(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow

    @staticmethod
    async def create_workflow(data: WorkflowCreate) -> WorkflowDocument:
        return await WorkflowRepository.create(data)

    @staticmethod
    async def update_workflow(workflow_id: str, data: WorkflowUpdate) -> WorkflowDocument:
        workflow = await WorkflowService.get_workflow(workflow_id)
        return await WorkflowRepository.update(workflow, data)

    @staticmethod
    async def delete_workflow(workflow_id: str) -> dict:
        workflow = await WorkflowService.get_workflow(workflow_id)
        await WorkflowRepository.delete(workflow)
        return {"deleted": True}