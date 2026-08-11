from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class TestCaseImage(Base):
    __tablename__ = "test_case_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().hex)
    test_case_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    image_id: Mapped[str] = mapped_column(String(36), ForeignKey("extracted_images.id", ondelete="CASCADE"), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(server_default=func.now())
