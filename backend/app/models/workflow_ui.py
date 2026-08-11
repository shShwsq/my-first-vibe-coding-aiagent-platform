from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation, ChatMessage


class WorkflowUI(Base):
    __tablename__ = "workflow_uis"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    ui_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    
    conversation: Mapped["Conversation"] = relationship("Conversation")
    message: Mapped["ChatMessage"] = relationship("ChatMessage", backref="workflow_uis")
