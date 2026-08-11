from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    api_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("api_configs.id"))
    conversation_mode: Mapped[str] = mapped_column(String(50), default="chat")
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.id")
    test_state: Mapped[Optional["TestConversationState"]] = relationship(back_populates="conversation", uselist=False, cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class TestConversationState(Base):
    __tablename__ = "test_conversation_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    agent_names: Mapped[str] = mapped_column(Text, default="")
    test_case: Mapped[str] = mapped_column(String(200), default="")
    request_interval: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    conversation: Mapped["Conversation"] = relationship(back_populates="test_state")


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_type: Mapped[str] = mapped_column(String(20), default="agent")
    test_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    test_folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_case_folders.id", ondelete="CASCADE"), nullable=False)
    conversation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    question: Mapped[Optional[str]] = mapped_column(Text)
    image_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    request_time: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
