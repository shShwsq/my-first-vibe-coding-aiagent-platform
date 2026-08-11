from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        UniqueConstraint('folder_id', 'row_order', name='uq_test_case_folder_row_order'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().hex)
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_case_folders.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    question: Mapped[Optional[str]] = mapped_column(Text)
    file_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("files.id", ondelete="SET NULL"))
    sample_answer: Mapped[Optional[str]] = mapped_column(Text)
    row_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=func.now())
