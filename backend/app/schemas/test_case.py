from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TestCaseFolderBase(BaseModel):
    name: str
    description: Optional[str] = None


class TestCaseFolderCreate(TestCaseFolderBase):
    pass


class TestCaseFolderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TestCaseFolderResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    user_id: int
    case_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImageInfo(BaseModel):
    id: str
    url: str
    preview_url: str

    class Config:
        from_attributes = True


class TestCaseBase(BaseModel):
    row_order: Optional[int] = None
    question: Optional[str] = None
    image_ids: Optional[List[str]] = None
    file_id: Optional[str] = None
    sample_answer: Optional[str] = None


class TestCaseCreate(TestCaseBase):
    folder_id: str


class TestCaseUpdate(BaseModel):
    question: Optional[str] = None
    image_ids: Optional[List[str]] = None
    file_id: Optional[str] = None
    sample_answer: Optional[str] = None


class TestCaseBatchCreate(BaseModel):
    folder_id: str
    start_row_order: Optional[int] = None
    cases: List[TestCaseBase]


class TestCaseResponse(BaseModel):
    id: str
    folder_id: str
    user_id: int
    question: Optional[str] = None
    file_id: Optional[str] = None
    sample_answer: Optional[str] = None
    row_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    images: List[ImageInfo] = []
    file_name: Optional[str] = None

    class Config:
        from_attributes = True
