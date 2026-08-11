from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.models.knowledge_base import KnowledgeBase
from app.models.file import BaseFile
from app.models.user import User
from app.auth import get_current_user
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["知识库管理"])


@router.get("", response_model=List[KnowledgeBaseResponse])
def get_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id
    ).order_by(KnowledgeBase.created_at.desc()).all()
    return knowledge_bases


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', kb_id):
        raise HTTPException(status_code=400, detail="无效的知识库ID")
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    return kb


@router.post("", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not kb_data.name or not kb_data.name.strip():
        raise HTTPException(status_code=400, detail="知识库名称不能为空")
    
    existing_kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id,
        KnowledgeBase.name == kb_data.name.strip()
    ).first()
    
    if existing_kb:
        raise HTTPException(status_code=400, detail=f"知识库名称 '{kb_data.name}' 已存在")
    
    new_kb = KnowledgeBase(
        name=kb_data.name.strip(),
        description=kb_data.description.strip() if kb_data.description else None,
        user_id=current_user.id
    )
    
    db.add(new_kb)
    db.commit()
    db.refresh(new_kb)
    
    logger.info(f"知识库创建成功: {new_kb.name} (ID: {new_kb.id}, user={current_user.id})")
    
    return new_kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: str,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', kb_id):
        raise HTTPException(status_code=400, detail="无效的知识库ID")
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if kb_data.name:
        existing_kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == current_user.id,
            KnowledgeBase.name == kb_data.name.strip(),
            KnowledgeBase.id != kb_id
        ).first()
        
        if existing_kb:
            raise HTTPException(status_code=400, detail=f"知识库名称 '{kb_data.name}' 已存在")
    
    update_data = kb_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(kb, key, value)
    
    db.commit()
    db.refresh(kb)
    
    logger.info(f"知识库更新成功: {kb.name} (ID: {kb_id})")
    
    return kb


@router.delete("/{kb_id}")
def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', kb_id):
        raise HTTPException(status_code=400, detail="无效的知识库ID")
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == kb_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    from app.models.document_chunk import DocumentChunk
    from app.models.extracted_image import ExtractedImage
    from app.services.file_storage import file_storage
    
    files = db.query(BaseFile).filter(
        BaseFile.knowledge_base_id == kb_id
    ).all()
    
    file_count = len(files)
    
    for file_record in files:
        images = db.query(ExtractedImage).filter(ExtractedImage.file_id == str(file_record.id)).all()
        for image in images:
            try:
                file_storage.delete_image(image.image_path)
            except Exception as e:
                logger.warning(f"Failed to delete image file {image.image_path}: {e}")
        
        db.query(DocumentChunk).filter(DocumentChunk.file_id == str(file_record.id)).delete()
        db.query(ExtractedImage).filter(ExtractedImage.file_id == str(file_record.id)).delete()
        
        try:
            file_storage.delete_file(file_record.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file from filesystem: {e}")
        
        db.delete(file_record)
    
    db.delete(kb)
    db.commit()
    
    logger.info(f"知识库删除成功: {kb.name} (ID: {kb_id}, 删除文件数: {file_count})")
    
    return {"message": "删除成功", "deleted_files": file_count}
