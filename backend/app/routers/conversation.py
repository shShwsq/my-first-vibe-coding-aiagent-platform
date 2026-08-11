from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from pathlib import Path
from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, ChatMessage
from app.auth import get_current_user
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationList,
    ConversationPage,
    MessageCreate
)

router = APIRouter(prefix="/conversations", tags=["对话管理"])

WORKFLOW_FILES_DIR = Path(__file__).parent.parent.parent / "workflow_files"


def delete_workflow_files(file_paths: List[str]):
    for file_path in file_paths:
        try:
            full_path = WORKFLOW_FILES_DIR / file_path
            if full_path.exists():
                full_path.unlink()
        except Exception as e:
            pass


@router.get("", response_model=ConversationPage)
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    offset = (page - 1) * page_size
    
    total = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == current_user.id
    ).scalar()
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(offset).limit(page_size).all()
    
    items = [ConversationList.model_validate(c) for c in conversations]
    
    return ConversationPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(conversations)) < total
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return conversation


@router.post("", response_model=ConversationResponse)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
        api_id=data.api_id,
        conversation_mode=data.conversation_mode or "chat"
    )
    
    db.add(conversation)
    db.flush()
    
    for msg in data.messages:
        message = ChatMessage(
            conversation_id=conversation.id,
            role=msg.role,
            content=msg.content
        )
        db.add(message)
    
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(conversation, key, value)
    
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.post("/{conversation_id}/messages", response_model=ConversationResponse)
def add_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    message = ChatMessage(
        conversation_id=conversation_id,
        role=data.role,
        content=data.content
    )
    
    db.add(message)
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.put("/{conversation_id}/messages", response_model=ConversationResponse)
def replace_messages(
    conversation_id: int,
    messages: List[MessageCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.sql import func
    from app.models.workflow_ui import WorkflowUI
    from app.models.workflow_file import WorkflowFile
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    existing_messages = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id
    ).order_by(ChatMessage.id).all()
    
    existing_count = len(existing_messages)
    new_count = len(messages)
    
    if new_count < existing_count:
        messages_to_delete = existing_messages[new_count:]
        message_ids_to_delete = [m.id for m in messages_to_delete]
        
        workflow_files_to_delete = db.query(WorkflowFile).filter(
            WorkflowFile.message_id.in_(message_ids_to_delete)
        ).all()
        file_paths_to_delete = [f.file_path for f in workflow_files_to_delete]
        
        db.query(WorkflowUI).filter(
            WorkflowUI.message_id.in_(message_ids_to_delete)
        ).delete(synchronize_session=False)
        
        db.query(WorkflowFile).filter(
            WorkflowFile.message_id.in_(message_ids_to_delete)
        ).delete(synchronize_session=False)
        
        delete_workflow_files(file_paths_to_delete)
        
        for msg in messages_to_delete:
            db.delete(msg)
    
    for i, msg_data in enumerate(messages):
        if i < existing_count:
            existing_messages[i].role = msg_data.role
            existing_messages[i].content = msg_data.content
        else:
            new_message = ChatMessage(
                conversation_id=conversation_id,
                role=msg_data.role,
                content=msg_data.content
            )
            db.add(new_message)
    
    conversation.updated_at = func.now()
    
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.workflow_ui import WorkflowUI
    from app.models.workflow_memory import WorkflowMemory
    from app.models.workflow_file import WorkflowFile
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    workflow_files = db.query(WorkflowFile).filter(
        WorkflowFile.conversation_id == conversation_id
    ).all()
    file_paths_to_delete = [f.file_path for f in workflow_files]
    
    db.query(WorkflowUI).filter(WorkflowUI.conversation_id == conversation_id).delete()
    db.query(WorkflowMemory).filter(WorkflowMemory.conversation_id == conversation_id).delete()
    db.query(WorkflowFile).filter(WorkflowFile.conversation_id == conversation_id).delete()
    
    delete_workflow_files(file_paths_to_delete)
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "删除成功"}
