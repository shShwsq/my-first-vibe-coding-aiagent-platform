from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.user import User
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from app.auth import get_current_user
from app.services.embedding import EmbeddingService
from app.services.embedding_config import get_embedding_config, check_embedding_available
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG检索"])


class SearchRequest(BaseModel):
    query: str
    knowledge_base_id: str
    top_k: int = 5


class SearchResult(BaseModel):
    chunk_id: str
    content: str
    file_id: str
    similarity: float


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str


@router.post("/search", response_model=SearchResponse)
async def search_knowledge_base(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not settings.is_postgresql:
        raise HTTPException(status_code=400, detail="RAG功能需要PostgreSQL数据库")
    
    embedding_config = get_embedding_config(db)
    if not embedding_config:
        raise HTTPException(status_code=400, detail="未配置Embedding API，请在功能模型中配置类型为embedding的模型")
    
    api_key, api_url, embedding_model, call_type = embedding_config
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == request.knowledge_base_id,
        KnowledgeBase.user_id == current_user.id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    embedding_service = EmbeddingService(
        api_key=api_key,
        url=api_url,
        model=embedding_model,
        call_type=call_type
    )
    
    query_embedding = await embedding_service.get_embedding(request.query)
    
    if not query_embedding:
        raise HTTPException(status_code=500, detail="生成查询向量失败")
    
    try:
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        sql = text(f"""
            SELECT 
                id as chunk_id,
                content,
                file_id,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM document_chunks
            WHERE knowledge_base_id = :kb_id
            AND user_id = :user_id
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)
        
        result = db.execute(
            sql,
            {
                "kb_id": request.knowledge_base_id,
                "user_id": str(current_user.id),
                "limit": request.top_k
            }
        )
        
        results = []
        for row in result:
            results.append(SearchResult(
                chunk_id=row.chunk_id,
                content=row.content,
                file_id=row.file_id,
                similarity=float(row.similarity)
            ))
        
        return SearchResponse(results=results, query=request.query)
        
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/status")
def get_rag_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    embedding_available = check_embedding_available(db)
    return {
        "enabled": settings.is_postgresql and embedding_available,
        "database_type": settings.database_type,
        "embedding_configured": embedding_available
    }
