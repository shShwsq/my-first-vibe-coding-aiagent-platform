import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_client import stream_llm
from app.services.chat_helpers import get_chat_config, prepare_messages, retrieve_file_contexts, create_stream_response, build_system_prompt_with_context
from typing import AsyncGenerator, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = get_chat_config(db, request.config_id, current_user.id)
    
    messages, last_message = prepare_messages(request.messages)
    
    if request.file_paths and len(request.file_paths) > 0:
        file_context = await retrieve_file_contexts(
            db=db,
            user_id=current_user.id,
            file_paths=request.file_paths,
            query=last_message
        )
        
        if file_context:
            system_prompt = build_system_prompt_with_context(
                file_context,
                "以下是用户上传的文件内容，请根据这些内容回答用户的问题："
            )
            messages.insert(0, {"role": "system", "content": system_prompt})
    
    stream_gen = stream_llm(
        messages=messages,
        model=config.model_code,
        api_key=config.api_key,
        url=config.url,
        call_type=config.call_type,
        enable_thinking=request.enable_thinking,
        timeout=60.0,
        enable_search=request.enable_search
    )
    
    return create_stream_response(
        stream_gen=stream_gen,
        db=db,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        user_message=last_message,
        api_id=request.config_id,
        conversation_mode="chat"
    )
