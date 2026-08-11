from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BaseFileBase(BaseModel):
    filename: str
    file_type: str
    file_size: str


class BaseFileCreate(BaseModel):
    knowledge_base_id: str


class BaseFileResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: str
    file_path: str
    knowledge_base_id: str
    user_id: int
    chunk_count: int = 0
    image_count: int = 0
    chunk_size: Optional[int] = 1000
    chunk_overlap: Optional[int] = 200
    embedding_status: str = "pending"
    embedding_error: Optional[str] = None
    image_extraction_status: str = "pending"
    image_extraction_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
