from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from beanie import Document, PydanticObjectId


class PositionSchema(BaseModel):
    x: float
    y: float


class NodeDataSchema(BaseModel):
    label: str

    # API node fields
    url: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[dict] = None
    body: Optional[dict] = None

    # Condition node fields
    condition: Optional[str] = None
    conditionVariable: Optional[str] = None
    conditionOperator: Optional[str] = None
    conditionValue: Optional[str] = None

    # LLM node fields
    llmModel: Optional[str] = None          # e.g. "gpt-4o"
    systemPrompt: Optional[str] = None
    userPrompt: Optional[str] = None
    outputMode: Optional[str] = None        # "text" | "json" | "decision"
    outputSchema: Optional[str] = None      # JSON schema hint string
    temperature: Optional[float] = None
    maxTokens: Optional[int] = None

    # Legacy / misc
    pynode_type: Optional[str] = None
    pynode_config: Optional[dict] = None
    code: Optional[str] = None             # functionNode
    timeout: Optional[float] = None        # delayNode


class NodeSchema(BaseModel):
    id: str
    type: Literal[
        "start", "api", "condition",
        "startNode", "apiNode", "conditionNode",
        "endNode", "functionNode", "debugNode", "delayNode",
        "webhookNode", "splitNode", "joinNode",
        "llmNode",          # ← NEW
    ]
    position: PositionSchema
    data: NodeDataSchema


class EdgeSchema(BaseModel):
    id: str
    source: str
    sourceHandle: Optional[Literal["out", "true", "false"]] = None
    target: str
    label: Optional[str] = None


# ── Beanie document ───────────────────────────────────────────────────────────

class WorkflowDocument(Document):
    name: str
    description: Optional[str] = None
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "workflows"


# ── Request / response schemas ────────────────────────────────────────────────

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
    id: PydanticObjectId = Field(alias="_id")
    name: str
    updated_at: datetime

    class Config:
        populate_by_name = True