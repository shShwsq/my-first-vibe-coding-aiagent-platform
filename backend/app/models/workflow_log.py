from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("workflow_agents.id"), nullable=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    node_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    node_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
