import asyncio
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeBase
from app.models.file import BaseFile
from app.models.document_chunk import DocumentChunk
from app.services.embedding import EmbeddingService
from app.services.embedding_config import get_embedding_config
from app.services.text_extractor import TextExtractor
from app.config import settings

logger = logging.getLogger(__name__)


def _sync_db_retrieve_context(
    knowledge_base_id: str,
    user_id: Optional[int],
    query_embedding: list,
) -> str:
    """同步数据库检索，在线程池中执行"""
    db = SessionLocal()
    try:
        embedding_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
        
        sql = text(f"""
            SELECT content
            FROM document_chunks
            WHERE knowledge_base_id = :kb_id
            AND user_id = :user_id
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT 5
        """)
        
        result = db.execute(
            sql,
            {
                "kb_id": knowledge_base_id,
                "user_id": user_id
            }
        )
        
        context_parts = [row[0] for row in result]
        
        if context_parts:
            context = "\n\n".join(context_parts)
            logger.info(f"RAG: Retrieved {len(context_parts)} context chunks")
            return context
        
        return ""
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return ""
    finally:
        db.close()


def _sync_db_retrieve_context_by_file(
    file_id: str,
    user_id: Optional[int],
    query_embedding: list,
) -> str:
    """根据file_id检索特定文件的内容，在线程池中执行"""
    db = SessionLocal()
    try:
        embedding_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
        
        sql = text(f"""
            SELECT content
            FROM document_chunks
            WHERE file_id = :file_id
            AND user_id = :user_id
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT 5
        """)
        
        result = db.execute(
            sql,
            {
                "file_id": file_id,
                "user_id": user_id
            }
        )
        
        context_parts = [row[0] for row in result]
        
        if context_parts:
            context = "\n\n".join(context_parts)
            logger.info(f"RAG: Retrieved {len(context_parts)} context chunks for file_id: {file_id}")
            return context
        
        return ""
    except Exception as e:
        logger.error(f"RAG search error for file_id {file_id}: {e}")
        return ""
    finally:
        db.close()


def _sync_get_knowledge_base_id(
    base_name: str,
    user_id: Optional[int],
) -> Optional[str]:
    """同步查询知识库ID，在线程池中执行"""
    db = SessionLocal()
    try:
        kb = db.query(KnowledgeBase).filter(
            KnowledgeBase.name == base_name,
            KnowledgeBase.user_id == user_id
        ).first()
        return str(kb.id) if kb else None
    finally:
        db.close()


async def retrieve_context_from_knowledge_base(
    db: Session,
    knowledge_base_id: str,
    user_id: Optional[int],
    query: str
) -> str:
    """从知识库检索上下文"""
    if not settings.is_postgresql:
        logger.warning("RAG requires PostgreSQL database")
        return ""
    
    embedding_config = get_embedding_config(db)
    if not embedding_config:
        logger.warning("Embedding API not configured in functional_models")
        return ""
    
    api_key, api_url, embedding_model, call_type = embedding_config
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_base_id,
        KnowledgeBase.user_id == user_id
    ).first()
    
    if not kb:
        logger.warning(f"Knowledge base not found: {knowledge_base_id}")
        return ""
    
    embedding_service = EmbeddingService(
        api_key=api_key,
        url=api_url,
        model=embedding_model,
        call_type=call_type
    )
    
    query_embedding = await embedding_service.get_embedding(query)
    
    if not query_embedding:
        logger.warning("Failed to generate query embedding")
        return ""
    
    loop = asyncio.get_event_loop()
    context = await loop.run_in_executor(
        None,
        _sync_db_retrieve_context,
        knowledge_base_id,
        user_id,
        query_embedding
    )
    
    return context


async def retrieve_context_from_file(
    db: Session,
    file_id: str,
    user_id: Optional[int],
    query: str
) -> str:
    """根据file_id检索特定文件的内容"""
    if not settings.is_postgresql:
        logger.warning("RAG requires PostgreSQL database")
        return ""
    
    embedding_config = get_embedding_config(db)
    if not embedding_config:
        logger.warning("Embedding API not configured in functional_models")
        return ""
    
    api_key, api_url, embedding_model, call_type = embedding_config
    
    embedding_service = EmbeddingService(
        api_key=api_key,
        url=api_url,
        model=embedding_model,
        call_type=call_type
    )
    
    query_embedding = await embedding_service.get_embedding(query)
    
    if not query_embedding:
        logger.warning("Failed to generate query embedding")
        return ""
    
    loop = asyncio.get_event_loop()
    context = await loop.run_in_executor(
        None,
        _sync_db_retrieve_context_by_file,
        file_id,
        user_id,
        query_embedding
    )
    
    return context


async def retrieve_context_by_name(
    base_name: str,
    user_id: Optional[int],
    query: str,
    db: Optional[Session] = None,
) -> str:
    """通过知识库名称检索上下文，所有数据库操作都在线程池中执行"""
    if not settings.is_postgresql:
        logger.warning("RAG requires PostgreSQL database")
        return ""
    
    embedding_config = None
    if db:
        embedding_config = get_embedding_config(db)
    
    if not embedding_config:
        db_temp = SessionLocal()
        try:
            embedding_config = get_embedding_config(db_temp)
        finally:
            db_temp.close()
    
    if not embedding_config:
        logger.warning("Embedding API not configured")
        return ""
    
    api_key, api_url, embedding_model, call_type = embedding_config
    
    loop = asyncio.get_event_loop()
    
    knowledge_base_id = await loop.run_in_executor(
        None,
        _sync_get_knowledge_base_id,
        base_name,
        user_id
    )
    
    if not knowledge_base_id:
        logger.warning(f"Knowledge base not found: {base_name}")
        return ""
    
    embedding_service = EmbeddingService(
        api_key=api_key,
        url=api_url,
        model=embedding_model,
        call_type=call_type
    )
    
    query_embedding = await embedding_service.get_embedding(query)
    
    if not query_embedding:
        logger.warning("Failed to generate query embedding")
        return ""
    
    context = await loop.run_in_executor(
        None,
        _sync_db_retrieve_context,
        knowledge_base_id,
        user_id,
        query_embedding
    )
    
    return context


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
    if not file_paths:
        return ""
    
    context_parts = []
    
    for file_path in file_paths:
        test_file = db.query(BaseFile).filter(
            BaseFile.file_path == file_path,
            BaseFile.user_id == user_id
        ).first()
        
        if test_file:
            context = await retrieve_context_from_file(
                db=db,
                file_id=test_file.id,
                user_id=user_id,
                query=query
            )
            if context:
                context_parts.append(context)
    
    return "\n\n".join(context_parts)


def _extract_text_from_file(
    file_data: bytes,
    file_type: str,
    db: Session,
    file_id: str,
    file_record,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> Optional[str]:
    """
    从文件中提取文本（支持图片和普通文件）
    
    Args:
        file_data: 文件二进制数据
        file_type: 文件类型
        db: 数据库会话
        file_id: 文件ID
        file_record: 文件记录对象
        chunk_size: 可选，自定义分块大小，默认使用 settings.CHUNK_SIZE
        chunk_overlap: 可选，自定义分块重叠大小，默认使用 settings.CHUNK_OVERLAP
    
    Returns:
        str: 提取的文本内容，失败返回None
    """
    image_types = ["png", "jpg", "jpeg", "gif", "webp", "bmp"]
    
    if file_type.lower() in image_types:
        from app.services.ocr_config import get_ocr_config
        from app.services.ocr import OCRService
        
        ocr_config = get_ocr_config(db)
        if not ocr_config:
            logger.warning(f"Skipping OCR processing: OCR API not configured (file_id={file_id})")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "未配置OCR模型"
                db.commit()
            return None
        
        ocr_api_key, ocr_url, ocr_model, ocr_call_type = ocr_config
        ocr_service = OCRService(
            api_key=ocr_api_key,
            url=ocr_url,
            model=ocr_model,
            call_type=ocr_call_type
        )
        
        text = asyncio.run(ocr_service.extract_text_from_image(file_data, file_type))
        
        if not text or text == "图片中无文字内容":
            logger.warning(f"No text extracted from image by OCR (file_id={file_id})")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "OCR未能提取到文字内容"
                db.commit()
            return None
        
        logger.info(f"OCR extracted {len(text)} characters from image (file_id={file_id})")
        return text
    else:
        effective_chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
        effective_chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP
        
        extractor = TextExtractor(
            chunk_size=effective_chunk_size,
            chunk_overlap=effective_chunk_overlap
        )
        
        text = extractor.extract_text(file_data, file_type)
        if not text:
            logger.warning(f"No text extracted from file (file_id={file_id})")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "无法从文件中提取文本"
                db.commit()
            return None
        
        logger.info(f"Extracted {len(text)} characters from file (file_id={file_id})")
        return text


def _generate_embeddings_and_save(
    file_id: str,
    knowledge_base_id: str,
    user_id: int,
    chunks: List[Tuple[str, int]],
    api_key: str,
    api_url: str,
    embedding_model: str,
    call_type: str,
    db: Session,
    file_record
) -> bool:
    """
    为文本块生成向量并保存到数据库
    
    Returns:
        bool: 是否成功
    """
    embedding_service = EmbeddingService(
        api_key=api_key,
        url=api_url,
        model=embedding_model,
        call_type=call_type
    )
    
    async def _process_chunks():
        for chunk_text, chunk_index in chunks:
            try:
                logger.info(f"Generating embedding for chunk {chunk_index} (file_id={file_id})")
                embedding = await embedding_service.get_embedding(chunk_text)
                
                chunk = DocumentChunk(
                    file_id=file_id,
                    knowledge_base_id=knowledge_base_id,
                    user_id=user_id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    embedding=embedding
                )
                db.add(chunk)
                logger.info(f"Created chunk {chunk_index} with embedding dimension {len(embedding) if embedding else 0}")
            except Exception as e:
                logger.error(f"Error creating chunk {chunk_index}: {e}")
    
    try:
        asyncio.run(_process_chunks())
        
        db.commit()
        
        if file_record:
            file_record.embedding_status = "completed"
            file_record.embedding_error = None
            db.commit()
        
        logger.info(f"RAG processing completed: {len(chunks)} chunks created (file_id={file_id})")
        return True
    except Exception as e:
        logger.error(f"Error saving embeddings: {e}")
        db.rollback()
        return False


def process_file_for_rag(
    file_id: str,
    file_data: bytes,
    file_type: str,
    knowledge_base_id: str,
    user_id: int,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
):
    """
    处理文件用于RAG：提取文本、分块、生成向量
    
    Args:
        file_id: 文件ID
        file_data: 文件二进制数据
        file_type: 文件类型
        knowledge_base_id: 知识库ID
        user_id: 用户ID
        chunk_size: 可选，自定义分块大小，默认使用 settings.CHUNK_SIZE
        chunk_overlap: 可选，自定义分块重叠大小，默认使用 settings.CHUNK_OVERLAP
    """
    effective_chunk_size = chunk_size or settings.CHUNK_SIZE
    effective_chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    logger.info(f"Starting RAG processing for file_id={file_id} with chunk_size={effective_chunk_size}, chunk_overlap={effective_chunk_overlap}")
    
    db = SessionLocal()
    try:
        file_record = db.query(BaseFile).filter(BaseFile.id == file_id).first()
        if file_record:
            file_record.embedding_status = "processing"
            file_record.embedding_error = None
            db.commit()
        
        if not settings.is_postgresql:
            logger.info(f"Skipping RAG processing: PostgreSQL required for vector storage (file_id={file_id}), current: {settings.database_type}")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "需要PostgreSQL数据库支持向量存储"
                db.commit()
            return
        
        embedding_config = get_embedding_config(db)
        if not embedding_config:
            logger.warning(f"Skipping RAG processing: Embedding API not configured (file_id={file_id}). Please add a functional_model with functional_type='embedding'")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "未配置Embedding API"
                db.commit()
            return
        
        api_key, api_url, embedding_model, call_type = embedding_config
        logger.info(f"Using embedding model: {embedding_model} with call_type: {call_type}")
        
        text = _extract_text_from_file(
            file_data, file_type, db, file_id, file_record,
            chunk_size=effective_chunk_size,
            chunk_overlap=effective_chunk_overlap
        )
        if not text:
            return
        
        extractor = TextExtractor(
            chunk_size=effective_chunk_size,
            chunk_overlap=effective_chunk_overlap
        )
        chunks = extractor.split_text_into_chunks(text)
        
        if not chunks:
            logger.warning(f"No chunks created from file (file_id={file_id})")
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = "无法创建文本块"
                db.commit()
            return
        
        logger.info(f"Created {len(chunks)} chunks from file (file_id={file_id})")
        
        _generate_embeddings_and_save(
            file_id=file_id,
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            chunks=chunks,
            api_key=api_key,
            api_url=api_url,
            embedding_model=embedding_model,
            call_type=call_type,
            db=db,
            file_record=file_record
        )
        
    except Exception as e:
        logger.error(f"Error processing file for RAG: {e}")
        db.rollback()
        
        try:
            file_record = db.query(BaseFile).filter(BaseFile.id == file_id).first()
            if file_record:
                file_record.embedding_status = "failed"
                file_record.embedding_error = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def process_file_for_rag_with_settings(
    file_id: str,
    file_data: bytes,
    file_type: str,
    knowledge_base_id: str,
    user_id: int,
    chunk_size: int,
    chunk_overlap: int
):
    """
    使用自定义设置处理文件用于RAG（已废弃，请使用 process_file_for_rag）
    
    此函数保留仅为向后兼容，实际调用 process_file_for_rag
    """
    process_file_for_rag(
        file_id=file_id,
        file_data=file_data,
        file_type=file_type,
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
