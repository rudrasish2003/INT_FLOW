from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from beanie import Document
from beanie import Document, PydanticObjectId

# --- Sub-schemas for Nodes and Edges ---

class PositionSchema(BaseModel):
    x: float
    y: float

class NodeDataSchema(BaseModel):
    label: str
    url: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None
    condition: Optional[str] = None

class NodeSchema(BaseModel):
    id: str
    type: Literal["start", "api", "condition", "startNode", "apiNode", "conditionNode"]
    position: PositionSchema
    data: NodeDataSchema

class EdgeSchema(BaseModel):
    id: str
    source: str
    sourceHandle: Optional[Literal["out", "true", "false"]] = None
    target: str
    label: Optional[str] = None

# --- Beanie Database Document ---

class WorkflowDocument(Document):
    name: str
    description: Optional[str] = None
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflows"

# --- API Request/Response Schemas ---

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []

class WorkflowUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]

class WorkflowResponseShort(BaseModel):
    # Change `str` to `PydanticObjectId`
    id: PydanticObjectId = Field(alias="_id") 
    name: str
    updated_at: datetime
    
    class Config:
        populate_by_name = True