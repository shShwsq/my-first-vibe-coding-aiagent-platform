from pydantic import BaseModel
from typing import List, Optional


class MessageBase(BaseModel):
    role: str
    content: str


class FileItem(BaseModel):
    name: str


class ChatRequest(BaseModel):
    config_id: int
    messages: List[MessageBase]
    conversation_id: Optional[int] = None
    enable_thinking: bool = False
    enable_search: bool = False
    file_paths: Optional[List[str]] = []
    file_items: Optional[List[FileItem]] = []


class RAGChatRequest(BaseModel):
    config_id: int
    messages: List[MessageBase]
    knowledge_base_id: str
    conversation_id: Optional[int] = None
    enable_thinking: bool = False
    enable_search: bool = False
    file_paths: Optional[List[str]] = []
    file_items: Optional[List[FileItem]] = []


class ChatResponse(BaseModel):
    content: str
