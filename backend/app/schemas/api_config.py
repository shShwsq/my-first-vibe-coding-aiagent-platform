from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApiConfigBase(BaseModel):
    name: str
    code: str
    call_type: str = "OpenAI Chat"
    api_key: str
    api_url: Optional[str] = None
    is_default: bool = False


class ApiConfigCreate(ApiConfigBase):
    pass


class ApiConfigUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    call_type: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    is_default: Optional[bool] = None


class ApiConfigResponse(ApiConfigBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
