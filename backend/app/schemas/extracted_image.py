from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExtractedImageResponse(BaseModel):
    id: str
    file_id: str
    page_number: int
    image_index: int
    image_format: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
