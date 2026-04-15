from pydantic import BaseModel
from typing import List
from modules.workflows.schemas import NodeSchema, EdgeSchema

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]