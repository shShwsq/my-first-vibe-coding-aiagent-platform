import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.functional_model import FunctionalModel

logger = logging.getLogger(__name__)


def get_functional_config(db: Session, functional_type: str) -> Optional[Tuple[str, str, str, str]]:
    """获取功能模型配置"""
    model = db.query(FunctionalModel).filter(
        FunctionalModel.functional_type == functional_type,
        FunctionalModel.is_active == True
    ).first()
    
    if not model:
        logger.warning(f"No active {functional_type} configuration found in functional_models")
        return None
    
    if not model.api_key:
        logger.warning(f"{functional_type.capitalize()} configuration has no API key")
        return None
    
    api_url = model.api_url or "https://api.openai.com/v1"
    model_name = model.code or ("text-embedding-ada-002" if functional_type == "embedding" else "gpt-4o")
    call_type = model.call_type or "OpenAI Chat"
    
    return (model.api_key, api_url, model_name, call_type)


def get_functional_config_dict(db: Session, functional_type: str) -> Optional[dict]:
    """获取功能模型配置（字典格式）"""
    model = db.query(FunctionalModel).filter(
        FunctionalModel.functional_type == functional_type,
        FunctionalModel.is_active == True
    ).first()
    
    if not model:
        return None
    
    return {
        "model": model.code,
        "api_key": model.api_key,
        "url": model.api_url or "https://api.openai.com/v1",
        "call_type": model.call_type or "OpenAI Chat"
    }


def check_functional_available(db: Session, functional_type: str) -> bool:
    """检查功能模型是否可用"""
    config = get_functional_config(db, functional_type)
    return config is not None


def get_embedding_config(db: Session) -> Optional[Tuple[str, str, str, str]]:
    """获取Embedding配置（向后兼容）"""
    return get_functional_config(db, "embedding")


def check_embedding_available(db: Session) -> bool:
    """检查Embedding是否可用（向后兼容）"""
    return check_functional_available(db, "embedding")


def get_ocr_config(db: Session) -> Optional[Tuple[str, str, str, str]]:
    """获取OCR配置（向后兼容）"""
    return get_functional_config(db, "ocr")


def check_ocr_available(db: Session) -> bool:
    """检查OCR是否可用（向后兼容）"""
    return check_functional_available(db, "ocr")


def get_intent_model_config(db: Session) -> Optional[dict]:
    """获取意图识别模型配置（向后兼容）"""
    return get_functional_config_dict(db, "intent_recognition")


def get_code_gen_config(db: Session) -> Optional[dict]:
    """获取代码生成模型配置"""
    return get_functional_config_dict(db, "code_generation")
