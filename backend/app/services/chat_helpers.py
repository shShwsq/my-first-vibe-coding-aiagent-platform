import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.api_config import ApiConfig
from app.models.user import User
from app.services.conversation_saver import stream_and_save
from app.services.rag_service import retrieve_file_contexts as rag_retrieve_file_contexts

logger = logging.getLogger(__name__)


class ChatConfig:
    """聊天配置数据类"""
    def __init__(
        self,
        config_id: int,
        call_type: str,
        api_url: Optional[str],
        model_code: str,
        api_key: str,
        config_name: str = ""
    ):
        self.config_id = config_id
        self.call_type = call_type
        self.api_url = api_url
        self.model_code = model_code
        self.api_key = api_key
        self.config_name = config_name
    
    @property
    def url(self) -> str:
        return self.api_url or "https://api.anthropic.com"


def get_chat_config(
    db: Session,
    config_id: int,
    user_id: int
) -> ChatConfig:
    """
    获取并验证聊天模型配置
    
    Args:
        db: 数据库会话
        config_id: 配置ID
        user_id: 用户ID
    
    Returns:
        ChatConfig: 聊天配置对象
    
    Raises:
        HTTPException: 当配置不存在时抛出404异常
    """
    config = db.query(ApiConfig).filter(
        ApiConfig.id == config_id,
        ApiConfig.user_id == user_id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    call_type = config.call_type or "OpenAI Chat"
    api_url = config.api_url
    model_code = config.code
    api_key = config.api_key
    
    logger.info("=" * 60)
    logger.info("使用模型配置:")
    logger.info(f"  config_id: {config.id}")
    logger.info(f"  name: {config.name}")
    logger.info(f"  code: {model_code}")
    logger.info(f"  call_type: {call_type}")
    logger.info(f"  api_url: {api_url}")
    logger.info(f"  api_key: {api_key[:8]}..." if api_key else "  api_key: None")
    logger.info("=" * 60)
    
    return ChatConfig(
        config_id=config.id,
        call_type=call_type,
        api_url=api_url,
        model_code=model_code,
        api_key=api_key,
        config_name=config.name
    )


def prepare_messages(request_messages: List[Any]) -> tuple:
    """
    准备消息列表并提取最后一条消息
    
    Args:
        request_messages: 请求消息列表，可以是Pydantic模型或字典
    
    Returns:
        tuple: (messages列表, 最后一条消息内容)
    """
    if not request_messages:
        return [], ""
    
    if hasattr(request_messages[0], 'role'):
        messages = [{"role": msg.role, "content": msg.content} for msg in request_messages]
        last_message = request_messages[-1].content
    else:
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in request_messages]
        last_message = request_messages[-1]["content"]
    
    return messages, last_message


async def retrieve_file_contexts(
    db: Session,
    user_id: int,
    file_paths: List[str],
    query: str
) -> str:
    """
    根据文件路径从知识库检索文件内容
    
    Args:
        db: 数据库会话
        user_id: 用户ID
        file_paths: 文件路径列表
        query: 查询内容
    
    Returns:
        str: 合并后的文件上下文内容
    """
    return await rag_retrieve_file_contexts(db, user_id, file_paths, query)


def create_stream_response(
    stream_gen,
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
    api_id: int,
    conversation_mode: str = "chat"
) -> StreamingResponse:
    """
    创建流式响应并自动保存对话
    
    Args:
        stream_gen: 流式生成器
        db: 数据库会话
        user_id: 用户ID
        conversation_id: 对话ID（可选）
        user_message: 用户消息
        api_id: API配置ID
        conversation_mode: 对话模式（chat/rag/test）
    
    Returns:
        StreamingResponse: 流式响应对象
    """
    return StreamingResponse(
        stream_and_save(
            stream_generator=stream_gen,
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            api_id=api_id,
            conversation_mode=conversation_mode
        ),
        media_type="text/event-stream"
    )


def build_system_prompt_with_context(context: str, prefix: str = "以下是相关内容：") -> str:
    """
    构建包含检索上下文的系统提示
    
    Args:
        context: 检索到的上下文内容
        prefix: 前缀文本
    
    Returns:
        str: 完整的系统提示
    """
    return f"{prefix}\n\n{context}"
