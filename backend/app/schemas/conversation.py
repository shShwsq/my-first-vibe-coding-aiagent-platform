from pydantic import BaseModel, field_validator, field_serializer
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestConversationStateBase(BaseModel):
    status: str = "pending"
    agent_names: List[str] = []
    test_case: str = ""
    request_interval: int = 0


class TestConversationStateCreate(TestConversationStateBase):
    pass


class TestConversationStateResponse(TestConversationStateBase):
    id: int
    conversation_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('agent_names', mode='before')
    @classmethod
    def parse_agent_names(cls, v):
        if isinstance(v, str):
            return [name.strip() for name in v.split(',') if name.strip()]
        return v or []

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: str
    api_id: Optional[int] = None
    conversation_mode: Optional[str] = "chat"


class ConversationCreate(ConversationBase):
    messages: List[MessageCreate]


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    api_id: Optional[int] = None


class ConversationResponse(ConversationBase):
    id: int
    user_id: int
    messages: List[MessageResponse] = []
    test_state: Optional[TestConversationStateResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationList(BaseModel):
    id: int
    title: str
    conversation_mode: Optional[str] = "chat"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationPage(BaseModel):
    items: List[ConversationList]
    total: int
    page: int
    page_size: int
    has_more: bool
