import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.file import BaseFile
from app.auth import get_current_user
from app.schemas.chat import RAGChatRequest
from app.services.rag_service import retrieve_context_from_knowledge_base, retrieve_context_from_file
from app.services.llm_client import stream_llm
from app.services.chat_helpers import get_chat_config, prepare_messages, create_stream_response, build_system_prompt_with_context
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag-chat", tags=["RAG对话"])


@router.post("/stream")
async def rag_chat_stream(
    request: RAGChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = get_chat_config(db, request.config_id, current_user.id)
    
    messages, user_query = prepare_messages(request.messages)
    
    logger.info("=" * 60)
    logger.info("RAG Chat Request:")
    logger.info(f"  config_id: {config.config_id}")
    logger.info(f"  knowledge_base_id: {request.knowledge_base_id}")
    logger.info(f"  model: {config.model_code}")
    logger.info("=" * 60)
    
    context_parts = []
    
    context = await retrieve_context_from_knowledge_base(
        db=db,
        knowledge_base_id=request.knowledge_base_id,
        user_id=current_user.id,
        query=user_query
    )
    
    if context:
        context_parts.append(f"【知识库内容】\n{context}")
    
    if request.file_paths and len(request.file_paths) > 0:
        logger.info(f"RAG: file_paths received: {request.file_paths}")
        for file_path in request.file_paths:
            logger.info(f"RAG: Searching for file_path: {file_path}")
            test_file = db.query(BaseFile).filter(
                BaseFile.file_path == file_path,
                BaseFile.user_id == current_user.id
            ).first()
            
            if test_file:
                logger.info(f"RAG: Found test_file: {test_file.filename}, file_id: {test_file.id}, embedding_status: {test_file.embedding_status}")
            else:
                logger.warning(f"RAG: No test_file found for file_path: {file_path}")
                test_file_no_user = db.query(BaseFile).filter(
                    BaseFile.file_path == file_path
                ).first()
                if test_file_no_user:
                    logger.warning(f"RAG: Found test_file without user filter: {test_file_no_user.filename}, user_id: {test_file_no_user.user_id}, current_user.id: {current_user.id}")
                else:
                    logger.warning(f"RAG: No test_file found at all for file_path: {file_path}")
            
            if test_file:
                if test_file.embedding_status != "completed":
                    logger.warning(f"RAG: File {test_file.filename} embedding status: {test_file.embedding_status}, may not have content yet")
                
                file_context = await retrieve_context_from_file(
                    db=db,
                    file_id=test_file.id,
                    user_id=current_user.id,
                    query=user_query
                )
                if file_context:
                    context_parts.append(f"【上传文件: {test_file.filename}】\n{file_context}")
                    logger.info(f"RAG: Added file context from {test_file.filename} ({len(file_context)} chars)")
                else:
                    logger.warning(f"RAG: No context retrieved for file {test_file.filename}")
    
    if context_parts:
        combined_context = "\n\n".join(context_parts)
        system_message = {
            "role": "system",
            "content": build_system_prompt_with_context(
                combined_context,
                "以下是检索到的相关内容，请基于这些内容回答用户问题："
            )
        }
        messages = [system_message] + messages
        logger.info(f"RAG: Added context to messages ({len(combined_context)} chars)")
    
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
        user_message=user_query,
        api_id=request.config_id,
        conversation_mode="chat"
    )
