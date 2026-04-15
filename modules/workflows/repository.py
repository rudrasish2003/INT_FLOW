from typing import List
from beanie import PydanticObjectId
from .schemas import WorkflowDocument, WorkflowCreate, WorkflowUpdate
from datetime import datetime, timezone

class WorkflowRepository:
    @staticmethod
    async def get_all() -> List[WorkflowDocument]:
        return await WorkflowDocument.find_all().to_list()

    @staticmethod
    async def get_by_id(workflow_id: str) -> WorkflowDocument | None:
        return await WorkflowDocument.get(PydanticObjectId(workflow_id))

    @staticmethod
    async def create(data: WorkflowCreate) -> WorkflowDocument:
        workflow = WorkflowDocument(**data.model_dump())
        return await workflow.insert()

    @staticmethod
    async def update(workflow: WorkflowDocument, data: WorkflowUpdate) -> WorkflowDocument:
        await workflow.update({"$set": {
            **data.model_dump(),
            "updated_at": datetime.now(timezone.utc)
        }})
        return workflow

    @staticmethod
    async def delete(workflow: WorkflowDocument) -> None:
        await workflow.delete()