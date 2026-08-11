import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.services.functional_config import get_functional_config

logger = logging.getLogger(__name__)


def get_embedding_config(db: Session) -> Optional[Tuple[str, str, str, str]]:
    """获取Embedding配置"""
    return get_functional_config(db, "embedding")


def check_embedding_available(db: Session) -> bool:
    """检查Embedding是否可用"""
    config = get_embedding_config(db)
    return config is not None
