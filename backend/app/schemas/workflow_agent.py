from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WorkflowAgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_code: Optional[str] = None
    is_active: bool = True


class WorkflowAgentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkflowAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_code: Optional[str] = None
    is_active: Optional[bool] = None


class WorkflowAgentResponse(WorkflowAgentBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
