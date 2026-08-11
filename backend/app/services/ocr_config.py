import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.services.functional_config import get_functional_config

logger = logging.getLogger(__name__)


def get_ocr_config(db: Session) -> Optional[Tuple[str, str, str, str]]:
    """获取OCR配置"""
    return get_functional_config(db, "ocr")


def check_ocr_available(db: Session) -> bool:
    """检查OCR是否可用"""
    config = get_ocr_config(db)
    return config is not None
