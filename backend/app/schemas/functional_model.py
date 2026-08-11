from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FunctionalModelBase(BaseModel):
    name: str
    functional_type: str
    code: str
    call_type: str = "OpenAI Chat"
    api_key: str
    api_url: Optional[str] = None
    is_active: bool = True


class FunctionalModelCreate(FunctionalModelBase):
    pass


class FunctionalModelUpdate(BaseModel):
    name: Optional[str] = None
    functional_type: Optional[str] = None
    code: Optional[str] = None
    call_type: Optional[str] = None
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    is_active: Optional[bool] = None


class FunctionalModelResponse(FunctionalModelBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
