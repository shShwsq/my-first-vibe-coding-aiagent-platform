from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentBase(BaseModel):
    name: str
    api_url: str
    api_key: str
    call_params_example: Optional[str] = None
    call_code: Optional[str] = None
    description: Optional[str] = None
    response_type: str = "non_stream"
    response_extract_config: Optional[str] = None
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    call_params_example: Optional[str] = None
    call_code: Optional[str] = None
    description: Optional[str] = None
    response_type: Optional[str] = None
    response_extract_config: Optional[str] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerateCodeRequest(BaseModel):
    api_url: str
    api_key: str
    call_params_example: str


class TestCallRequest(BaseModel):
    call_code: str
    api_key: str
    message: str = "你好"
    response_type: str = "non_stream"
    response_extract_config: Optional[str] = None
    kwargs: Optional[dict] = None
