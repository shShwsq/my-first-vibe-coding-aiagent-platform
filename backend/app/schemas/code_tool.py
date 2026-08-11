from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ParameterDefinition(BaseModel):
    name: str
    type: str = Field(default="str", description="参数类型: str, int, float, bool, list, dict, df")
    default: Optional[Any] = None
    required: bool = True
    description: Optional[str] = None


class CodeToolBase(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    code: str
    parameters: Optional[List[ParameterDefinition]] = None
    return_type: Optional[str] = "dict"
    is_active: bool = True


class CodeToolCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    code: str
    parameters: Optional[List[ParameterDefinition]] = None
    return_type: Optional[str] = "dict"


class CodeToolUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    parameters: Optional[List[ParameterDefinition]] = None
    return_type: Optional[str] = None
    is_active: Optional[bool] = None


class CodeToolResponse(CodeToolBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CodeToolExecuteRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


class CodeToolExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
