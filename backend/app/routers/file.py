from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Form, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db, SessionLocal
from app.schemas.file import BaseFileResponse
from app.schemas.extracted_image import ExtractedImageResponse
from app.models.file import BaseFile
from app.models.knowledge_base import KnowledgeBase
from app.models.document_chunk import DocumentChunk
from app.models.extracted_image import ExtractedImage
from app.models.user import User
from app.auth import get_current_user
from app.services.text_extractor import TextExtractor
from app.services.file_storage import file_storage
from app.config import settings
from app.services.rag_service import process_file_for_rag, process_file_for_rag_with_settings
from urllib.parse import quote
import logging
import re
import time
import uuid
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-case-files", tags=["知识库文件"])


def get_file_or_404(db: Session, file_id: str, user_id: Optional[int] = None) -> BaseFile:
    query = db.query(BaseFile).filter(BaseFile.id == file_id)
    if user_id:
        query = query.filter(BaseFile.user_id == user_id)
    file_record = query.first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    return file_record


def validate_file_id(file_id: str) -> None:
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', file_id):
        raise HTTPException(status_code=400, detail="无效的文件ID")

ALLOWED_EXTENSIONS = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/msword': '.doc',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/bmp': '.bmp',
    'image/heic': '.heic',
    'image/heif': '.heif'
}

MAX_FILE_SIZE = 50 * 1024 * 1024

upload_rate_limit = {}
UPLOAD_RATE_LIMIT_SECONDS = 5
UPLOAD_RATE_LIMIT_COUNT = 10


def detect_file_type(content: bytes) -> str:
    if content.startswith(b'%PDF'):
        return 'PDF'
    elif content.startswith(b'PK\x03\x04'):
        return 'ZIP'
    elif content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
        return 'OLE'
    elif content.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'PNG'
    elif content.startswith(b'\xff\xd8\xff'):
        return 'JPEG'
    elif content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
        return 'GIF'
    elif content.startswith(b'RIFF') and content[8:12] == b'WEBP':
        return 'WEBP'
    elif content.startswith(b'BM'):
        return 'BMP'
    elif b'ftypheic' in content[:32] or b'ftypheix' in content[:32] or b'ftyphevc' in content[:32] or b'ftypheim' in content[:32]:
        return 'HEIC'
    elif b'ftypmif1' in content[:32] or b'ftypmsf1' in content[:32] or b'ftypheif' in content[:32]:
        return 'HEIF'
    return 'Unknown'


def validate_file_content(content: bytes, declared_type: str) -> tuple[bool, str]:
    actual_type = detect_file_type(content)
    
    if actual_type == 'Unknown':
        return False, "无法识别文件类型"
    
    if declared_type == 'application/pdf':
        if actual_type != 'PDF':
            return False, "文件内容与声明的PDF类型不匹配"
        return True, 'pdf'
    
    if declared_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        if actual_type == 'ZIP':
            return True, 'xlsx'
        return False, "文件内容与声明的Excel类型不匹配"
    
    if declared_type == 'application/vnd.ms-excel':
        if actual_type == 'OLE':
            return True, 'xls'
        elif actual_type == 'ZIP':
            return True, 'xlsx'
        return False, "文件内容与声明的Excel类型不匹配"
    
    if declared_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        if actual_type == 'ZIP':
            return True, 'docx'
        return False, "文件内容与声明的Word类型不匹配"
    
    if declared_type == 'application/msword':
        if actual_type == 'OLE':
            return True, 'doc'
        elif actual_type == 'ZIP':
            return True, 'docx'
        return False, "文件内容与声明的Word类型不匹配"
    
    if declared_type == 'application/vnd.ms-powerpoint':
        if actual_type == 'OLE':
            return True, 'ppt'
        elif actual_type == 'ZIP':
            return True, 'pptx'
        return False, "文件内容与声明的PPT类型不匹配"
    
    if declared_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
        if actual_type == 'ZIP':
            return True, 'pptx'
        return False, "文件内容与声明的PPTX类型不匹配"
    
    if declared_type == 'image/png':
        if actual_type == 'PNG':
            return True, 'png'
        return False, "文件内容与声明的PNG类型不匹配"
    
    if declared_type == 'image/jpeg':
        if actual_type == 'JPEG':
            return True, 'jpg'
        return False, "文件内容与声明的JPEG类型不匹配"
    
    if declared_type == 'image/jpg':
        if actual_type == 'JPEG':
            return True, 'jpg'
        return False, "文件内容与声明的JPG类型不匹配"
    
    if declared_type == 'image/gif':
        if actual_type == 'GIF':
            return True, 'gif'
        return False, "文件内容与声明的GIF类型不匹配"
    
    if declared_type == 'image/webp':
        if actual_type == 'WEBP':
            return True, 'webp'
        return False, "文件内容与声明的WEBP类型不匹配"
    
    if declared_type == 'image/bmp':
        if actual_type == 'BMP':
            return True, 'bmp'
        return False, "文件内容与声明的BMP类型不匹配"
    
    if declared_type == 'image/heic':
        if actual_type == 'HEIC':
            return True, 'heic'
        return False, "文件内容与声明的HEIC类型不匹配"
    
    if declared_type == 'image/heif':
        if actual_type == 'HEIF':
            return True, 'heif'
        return False, "文件内容与声明的HEIF类型不匹配"
    
    return False, "不支持的文件类型"


def sanitize_filename(filename: str) -> str:
    if not filename:
        return f"unnamed_{uuid.uuid4().hex[:8]}"
    
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    filename = re.sub(r'\.{2,}', '.', filename)
    filename = filename.strip('. ')
    
    if not filename:
        return f"unnamed_{uuid.uuid4().hex[:8]}"
    
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            filename = name[:max_length - len(ext) - 1] + '.' + ext
        else:
            filename = filename[:max_length]
    
    return filename


def check_rate_limit(user_id: int) -> tuple[bool, int]:
    current_time = time.time()
    
    if user_id not in upload_rate_limit:
        upload_rate_limit[user_id] = []
    
    upload_rate_limit[user_id] = [
        t for t in upload_rate_limit[user_id] 
        if current_time - t < UPLOAD_RATE_LIMIT_SECONDS
    ]
    
    if len(upload_rate_limit[user_id]) >= UPLOAD_RATE_LIMIT_COUNT:
        return False, UPLOAD_RATE_LIMIT_SECONDS - int(current_time - upload_rate_limit[user_id][0])
    
    upload_rate_limit[user_id].append(current_time)
    return True, 0


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


@router.get("", response_model=List[BaseFileResponse])
def get_files(
    knowledge_base_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(BaseFile).filter(
        BaseFile.user_id == current_user.id
    )
    
    if knowledge_base_id:
        if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', knowledge_base_id):
            raise HTTPException(status_code=400, detail="无效的知识库ID")
        query = query.filter(BaseFile.knowledge_base_id == knowledge_base_id)
    
    files = query.order_by(BaseFile.created_at.desc()).all()
    
    result = []
    for file in files:
        chunk_count = db.query(DocumentChunk).filter(
            DocumentChunk.file_id == str(file.id)
        ).count()
        
        image_count = db.query(ExtractedImage).filter(
            ExtractedImage.file_id == str(file.id)
        ).count()
        
        file_dict = {
            "id": str(file.id),
            "filename": file.filename,
            "file_type": file.file_type,
            "file_size": file.file_size,
            "file_path": file.file_path,
            "knowledge_base_id": str(file.knowledge_base_id),
            "user_id": file.user_id,
            "chunk_count": chunk_count,
            "image_count": image_count,
            "chunk_size": file.chunk_size,
            "chunk_overlap": file.chunk_overlap,
            "embedding_status": file.embedding_status or "pending",
            "embedding_error": file.embedding_error,
            "image_extraction_status": file.image_extraction_status or "pending",
            "image_extraction_error": file.image_extraction_error,
            "created_at": file.created_at,
            "updated_at": file.updated_at
        }
        result.append(BaseFileResponse(**file_dict))
    
    return result


@router.get("/uploaded")
def list_uploaded_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from pathlib import Path as StdPath
    
    files_dir = StdPath(file_storage.base_dir) / "files"
    uploaded_files = []
    
    if not files_dir.exists():
        return {"files": []}
    
    for date_dir in sorted(files_dir.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        for month_dir in sorted(date_dir.iterdir(), reverse=True):
            if not month_dir.is_dir():
                continue
            for day_dir in sorted(month_dir.iterdir(), reverse=True):
                if not day_dir.is_dir():
                    continue
                for file_path in sorted(day_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if file_path.is_file():
                        rel_path = str(file_path.relative_to(file_storage.base_dir))
                        file_record = db.query(BaseFile).filter(
                            BaseFile.file_path == rel_path,
                            BaseFile.user_id == current_user.id
                        ).first()
                        
                        uploaded_files.append({
                            "filename": file_path.stem if not file_record else file_record.filename,
                            "file_path": rel_path,
                            "file_size": file_storage.get_file_size(rel_path),
                            "file_type": file_record.file_type if file_record else file_path.suffix[1:].upper(),
                            "embedding_status": file_record.embedding_status if file_record else "unknown",
                            "id": file_record.id if file_record else None
                        })
    
    return {"files": uploaded_files}


def extract_images_from_file(file_data: bytes, file_id: str, user_id: int, knowledge_base_id: str, file_type: str) -> int:
    from app.database import SessionLocal
    
    logger.info(f"Starting image extraction for file_id={file_id}, file_type={file_type}")
    
    db = SessionLocal()
    try:
        file_record = db.query(BaseFile).filter(BaseFile.id == file_id).first()
        if file_record:
            file_record.image_extraction_status = "processing"
            db.commit()
        
        db.query(ExtractedImage).filter(ExtractedImage.file_id == file_id).delete()
        db.commit()
        
        extracted_count = 0
        
        if file_type.lower() == "pdf":
            extracted_count = _extract_images_from_pdf(db, file_data, file_id, user_id, knowledge_base_id)
        elif file_type.lower() in ["xlsx", "xls"]:
            extracted_count = _extract_images_from_excel(db, file_data, file_id, user_id, knowledge_base_id)
        elif file_type.lower() in ["docx", "doc"]:
            extracted_count = _extract_images_from_word(db, file_data, file_id, user_id, knowledge_base_id)
        else:
            logger.warning(f"Unsupported file type for image extraction: {file_type}")
            if file_record:
                file_record.image_extraction_status = "failed"
                file_record.image_extraction_error = f"不支持的文件类型: {file_type}"
                db.commit()
            return 0
        
        if file_record:
            file_record.image_extraction_status = "completed"
            file_record.image_extraction_error = None
            db.commit()
        
        db.commit()
        
        logger.info(f"Image extraction completed: {extracted_count} images extracted (file_id={file_id})")
        return extracted_count
        
    except Exception as e:
        logger.error(f"Error extracting images: {e}")
        db.rollback()
        try:
            file_record = db.query(BaseFile).filter(BaseFile.id == file_id).first()
            if file_record:
                file_record.image_extraction_status = "failed"
                file_record.image_extraction_error = str(e)
                db.commit()
        except Exception as update_error:
            logger.error(f"Failed to update image extraction status: {update_error}")
        return 0
    finally:
        db.close()


def _save_image_to_storage(image_bytes: bytes, image_ext: str) -> str:
    image_id = uuid.uuid4().hex
    return file_storage.save_image(image_id, image_bytes, image_ext)


def _extract_images_from_pdf(db, file_data: bytes, file_id: str, user_id: int, knowledge_base_id: str) -> int:
    try:
        import fitz
    except ImportError:
        logger.error("PyMuPDF not installed. Run: pip install pymupdf")
        return 0
    
    doc = fitz.open(stream=file_data, filetype="pdf")
    extracted_count = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images()
        
        for img_index, img in enumerate(images):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image.get("ext", "png")
                
                if len(image_bytes) < 100:
                    continue
                
                width, height = _get_image_dimensions(image_bytes)
                image_path = _save_image_to_storage(image_bytes, image_ext)
                
                extracted_image = ExtractedImage(
                    file_id=file_id,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    page_number=page_num + 1,
                    image_index=img_index + 1,
                    image_path=image_path,
                    image_format=image_ext,
                    width=width,
                    height=height
                )
                db.add(extracted_image)
                extracted_count += 1
                
            except Exception as e:
                logger.warning(f"Error extracting image {img_index} from PDF page {page_num}: {e}")
    
    doc.close()
    return extracted_count


def _extract_images_from_excel(db, file_data: bytes, file_id: str, user_id: int, knowledge_base_id: str) -> int:
    import zipfile
    import xml.etree.ElementTree as ET
    
    extracted_count = 0
    
    try:
        wb_stream = io.BytesIO(file_data)
        
        if zipfile.is_zipfile(wb_stream):
            wb_stream.seek(0)
            with zipfile.ZipFile(wb_stream, 'r') as zf:
                all_files = zf.namelist()
                logger.info(f"Excel archive contains {len(all_files)} files: {all_files}")
                
                media_files = [f for f in all_files if f.startswith('xl/media/')]
                logger.info(f"Found {len(media_files)} media files in xl/media/: {media_files}")
                
                drawings_files = [f for f in all_files if 'drawing' in f.lower()]
                logger.info(f"Found {len(drawings_files)} drawing files: {drawings_files}")
                
                image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.emf', '.wmf']
                all_image_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]
                logger.info(f"Found {len(all_image_files)} image files in entire archive: {all_image_files}")
                
                for img_index, media_path in enumerate(media_files):
                    try:
                        image_bytes = zf.read(media_path)
                        
                        if len(image_bytes) < 100:
                            continue
                        
                        image_ext = _detect_image_format_from_bytes(image_bytes)
                        
                        width, height = _get_image_dimensions(image_bytes)
                        image_path = _save_image_to_storage(image_bytes, image_ext)
                        
                        extracted_image = ExtractedImage(
                            file_id=file_id,
                            user_id=user_id,
                            knowledge_base_id=knowledge_base_id,
                            page_number=1,
                            image_index=img_index + 1,
                            image_path=image_path,
                            image_format=image_ext,
                            width=width,
                            height=height
                        )
                        db.add(extracted_image)
                        extracted_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error extracting media file {media_path}: {e}")
                
                if extracted_count == 0:
                    for drawing_file in drawings_files:
                        if drawing_file.endswith('.xml') and not drawing_file.endswith('.rels'):
                            try:
                                drawing_xml = zf.read(drawing_file)
                                logger.info(f"Parsing drawing file: {drawing_file}")
                                
                                ns = {
                                    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
                                    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                                    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                                }
                                
                                root = ET.fromstring(drawing_xml)
                                
                                for idx, pic in enumerate(root.findall('.//xdr:pic', ns)):
                                    blip = pic.find('.//a:blip', ns)
                                    if blip is not None:
                                        embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                        link_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link')
                                        logger.info(f"Found picture {idx}: embed={embed_id}, link={link_id}")
                                        
                                        for child in blip:
                                            logger.info(f"  blip child: tag={child.tag}, attrib={child.attrib}")
                                
                                for idx, blip_elem in enumerate(root.iter()):
                                    if 'blip' in blip_elem.tag.lower():
                                        logger.info(f"Blip element {idx}: tag={blip_elem.tag}, attrib={blip_elem.attrib}")
                                        for child in blip_elem:
                                            if child.text and len(child.text) > 100:
                                                logger.info(f"  Found embedded data: {len(child.text)} chars")
                                
                                for idx, pic in enumerate(root.iter()):
                                    if 'pic' in pic.tag.lower() or 'picture' in pic.tag.lower():
                                        logger.info(f"Pic element {idx}: tag={pic.tag}")
                                
                            except Exception as e:
                                logger.warning(f"Error parsing drawing XML {drawing_file}: {e}")
                    
                    rels_file = 'xl/drawings/_rels/drawing1.xml.rels'
                    if rels_file in all_files:
                        try:
                            rels_xml = zf.read(rels_file)
                            logger.info(f"Parsing rels file: {rels_file}")
                            
                            rels_root = ET.fromstring(rels_xml)
                            rels_ns = {'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                            
                            external_images = []
                            for rel in rels_root.findall('.//rel:Relationship', rels_ns):
                                rel_id = rel.get('Id')
                                rel_type = rel.get('Type')
                                rel_target = rel.get('Target')
                                rel_mode = rel.get('TargetMode', '')
                                logger.info(f"Relationship: Id={rel_id}, Type={rel_type}, Target={rel_target}, Mode={rel_mode}")
                                
                                if rel_target and rel_target.startswith('http') and rel_mode == 'External':
                                    logger.info(f"  -> External link: {rel_target}")
                                    external_images.append((rel_id, rel_target))
                            
                            if external_images:
                                logger.info(f"Found {len(external_images)} external image links, downloading...")
                                import httpx
                                
                                for img_idx, (rel_id, url) in enumerate(external_images):
                                    try:
                                        logger.info(f"Downloading image {img_idx + 1}: {url}")
                                        response = httpx.get(url, timeout=30.0, follow_redirects=True)
                                        
                                        if response.status_code == 200:
                                            image_bytes = response.content
                                            
                                            if len(image_bytes) < 100:
                                                logger.warning(f"Image too small: {len(image_bytes)} bytes")
                                                continue
                                            
                                            image_ext = _detect_image_format_from_bytes(image_bytes)
                                            width, height = _get_image_dimensions(image_bytes)
                                            image_path = _save_image_to_storage(image_bytes, image_ext)
                                            
                                            extracted_image = ExtractedImage(
                                                file_id=file_id,
                                                user_id=user_id,
                                                knowledge_base_id=knowledge_base_id,
                                                page_number=1,
                                                image_index=img_idx + 1,
                                                image_path=image_path,
                                                image_format=image_ext,
                                                width=width,
                                                height=height
                                            )
                                            db.add(extracted_image)
                                            extracted_count += 1
                                            logger.info(f"Downloaded and saved image {img_idx + 1}: {len(image_bytes)} bytes")
                                        else:
                                            logger.warning(f"Failed to download image: HTTP {response.status_code}")
                                    except Exception as e:
                                        logger.warning(f"Error downloading external image {url}: {e}")
                        except Exception as e:
                            logger.warning(f"Error reading rels file: {e}")
                
                if extracted_count == 0 and all_image_files:
                    logger.info(f"No images in xl/media/, trying to extract from other locations...")
                    for img_index, img_path in enumerate(all_image_files):
                        try:
                            image_bytes = zf.read(img_path)
                            
                            if len(image_bytes) < 100:
                                continue
                            
                            image_ext = _detect_image_format_from_bytes(image_bytes)
                            
                            width, height = _get_image_dimensions(image_bytes)
                            image_path = _save_image_to_storage(image_bytes, image_ext)
                            
                            extracted_image = ExtractedImage(
                                file_id=file_id,
                                user_id=user_id,
                                knowledge_base_id=knowledge_base_id,
                                page_number=1,
                                image_index=img_index + 1,
                                image_path=image_path,
                                image_format=image_ext,
                                width=width,
                                height=height
                            )
                            db.add(extracted_image)
                            extracted_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Error extracting image file {img_path}: {e}")
        
        logger.info(f"ZIP extraction found {extracted_count} images, now trying openpyxl...")
        openpyxl_count = _extract_images_from_excel_openpyxl(db, file_data, file_id, user_id, knowledge_base_id)
        extracted_count = max(extracted_count, openpyxl_count)
    
    except zipfile.BadZipFile:
        logger.info("File is not a valid ZIP archive, trying openpyxl...")
        extracted_count = _extract_images_from_excel_openpyxl(db, file_data, file_id, user_id, knowledge_base_id)
    except Exception as e:
        logger.error(f"Error extracting images from Excel: {e}")
        extracted_count = _extract_images_from_excel_openpyxl(db, file_data, file_id, user_id, knowledge_base_id)
    
    return extracted_count


def _extract_images_from_excel_openpyxl(db, file_data: bytes, file_id: str, user_id: int, knowledge_base_id: str) -> int:
    try:
        from openpyxl import load_workbook
        from openpyxl.drawing.image import Image as OpenpyxlImage
    except ImportError:
        logger.error("openpyxl not installed. Run: pip install openpyxl")
        return 0
    
    wb = load_workbook(io.BytesIO(file_data), keep_vba=True)
    extracted_count = 0
    
    try:
        logger.info(f"openpyxl: workbook has {len(wb.worksheets)} sheets")
        
        for sheet_index, sheet in enumerate(wb.worksheets):
            image_count = 0
            
            has_images = hasattr(sheet, '_images')
            has_charts = hasattr(sheet, '_charts')
            has_drawings = hasattr(sheet, '_drawing')
            
            images_list = sheet._images if has_images else [] # type: ignore
            charts_list = sheet._charts if has_charts else [] # type: ignore
            drawing_obj = sheet._drawing if has_drawings else None # type: ignore
            
            logger.info(f"Sheet {sheet_index} ({sheet.title}): _images={len(images_list) if images_list else 0}, _charts={len(charts_list) if charts_list else 0}, _drawing={drawing_obj is not None}")
            
            if has_images and images_list:
                for img_index, img in enumerate(images_list):
                    try:
                        logger.info(f"  Processing image {img_index}: type={type(img).__name__}")
                        
                        image_bytes = img._data()
                        logger.info(f"  Image {img_index} size: {len(image_bytes)} bytes")
                        
                        if len(image_bytes) < 100:
                            continue
                        
                        image_ext = _detect_image_format_from_bytes(image_bytes)
                        
                        width, height = _get_image_dimensions(image_bytes)
                        image_path = _save_image_to_storage(image_bytes, image_ext)
                        
                        extracted_image = ExtractedImage(
                            file_id=file_id,
                            user_id=user_id,
                            knowledge_base_id=knowledge_base_id,
                            page_number=sheet_index + 1,
                            image_index=image_count + 1,
                            image_path=image_path,
                            image_format=image_ext,
                            width=width,
                            height=height
                        )
                        db.add(extracted_image)
                        image_count += 1
                        extracted_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Error extracting image {img_index} from Excel sheet {sheet_index}: {e}")
            
            if has_drawings and drawing_obj:
                try:
                    if hasattr(drawing_obj, '_images') and drawing_obj._images:
                        logger.info(f"  Found {len(drawing_obj._images)} images in drawing object")
                        for img_idx, img in enumerate(drawing_obj._images):
                            try:
                                if hasattr(img, '_data'):
                                    image_bytes = img._data()
                                    if len(image_bytes) > 100:
                                        image_ext = _detect_image_format_from_bytes(image_bytes)
                                        width, height = _get_image_dimensions(image_bytes)
                                        image_path = _save_image_to_storage(image_bytes, image_ext)
                                        extracted_image = ExtractedImage(
                                            file_id=file_id,
                                            user_id=user_id,
                                            knowledge_base_id=knowledge_base_id,
                                            page_number=sheet_index + 1,
                                            image_index=image_count + 1,
                                            image_path=image_path,
                                            image_format=image_ext,
                                            width=width,
                                            height=height
                                        )
                                        db.add(extracted_image)
                                        image_count += 1
                                        extracted_count += 1
                            except Exception as e:
                                logger.warning(f"Error extracting drawing image: {e}")
                except Exception as e:
                    logger.warning(f"Error processing drawing object: {e}")
            
            logger.info(f"Sheet {sheet_index} ({sheet.title}): extracted {image_count} images via openpyxl")
    
    except Exception as e:
        logger.error(f"Error processing Excel workbook with openpyxl: {e}")
    finally:
        wb.close()
    
    return extracted_count


def _detect_image_format_from_bytes(image_bytes: bytes) -> str:
    if len(image_bytes) < 4:
        return "png"
    
    if image_bytes[:2] == b'\xff\xd8':
        return "jpg"
    elif image_bytes[:4] == b'\x89PNG':
        return "png"
    elif image_bytes[:4] == b'GIF8':
        return "gif"
    elif image_bytes[:4] == b'BM':
        return "bmp"
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "webp"
    
    return "png"


def _extract_images_from_word(db, file_data: bytes, file_id: str, user_id: int, knowledge_base_id: str) -> int:
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed. Run: pip install python-docx")
        return 0
    
    doc = Document(io.BytesIO(file_data))
    extracted_count = 0
    
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                image_bytes = rel.target_part.blob
                
                if len(image_bytes) < 100:
                    continue
                
                image_ext = "png"
                content_type = rel.target_part.content_type
                if "jpeg" in content_type or "jpg" in content_type:
                    image_ext = "jpg"
                elif "gif" in content_type:
                    image_ext = "gif"
                elif "bmp" in content_type:
                    image_ext = "bmp"
                elif "tiff" in content_type:
                    image_ext = "tiff"
                elif "webp" in content_type:
                    image_ext = "webp"
                
                width, height = _get_image_dimensions(image_bytes)
                image_path = _save_image_to_storage(image_bytes, image_ext)
                
                extracted_image = ExtractedImage(
                    file_id=file_id,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    page_number=1,
                    image_index=extracted_count + 1,
                    image_path=image_path,
                    image_format=image_ext,
                    width=width,
                    height=height
                )
                db.add(extracted_image)
                extracted_count += 1
                
            except Exception as e:
                logger.warning(f"Error extracting image from Word document: {e}")
    
    return extracted_count


def _get_image_dimensions(image_bytes: bytes):
    width = None
    height = None
    try:
        from PIL import Image
        img_pil = Image.open(io.BytesIO(image_bytes))
        width, height = img_pil.size
    except Exception:
        pass
    return width, height


def convert_heic_to_jpeg(heic_content: bytes) -> tuple[bytes, str | None]:
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        
        from PIL import Image
        img = Image.open(io.BytesIO(heic_content))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        if img.info.get('orientation', 1) != 1:
            orientation = img.info['orientation']
            if orientation == 2:
                img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 4:
                img = img.rotate(180).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 5:
                img = img.rotate(-90, expand=True).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 6:
                img = img.rotate(-90, expand=True)
            elif orientation == 7:
                img = img.rotate(90, expand=True).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=90)
        jpeg_content = output.getvalue()
        
        return jpeg_content, None
    except Exception as e:
        logger.error(f"HEIC to JPEG conversion failed: {e}")
        raise HTTPException(status_code=400, detail=f"HEIC图片转换失败: {str(e)}")


@router.post("/{file_id}/extract-images")
def extract_images(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    supported_types = ["pdf", "xlsx", "xls", "docx", "doc"]
    if file_record.file_type.lower() not in supported_types:
        raise HTTPException(status_code=400, detail=f"只支持从 PDF、Excel、Word 文件中提取图片，当前文件类型: {file_record.file_type}")
    
    try:
        file_data = file_storage.read_file(file_record.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在或已被删除")
    except Exception as e:
        logger.error(f"Failed to read file for image extraction: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
    
    file_record.image_extraction_status = "processing"
    file_record.image_extraction_error = None
    db.commit()
    
    background_tasks.add_task(
        extract_images_from_file,
        file_data,
        str(file_record.id),
        file_record.user_id,
        str(file_record.knowledge_base_id),
        str(file_record.file_type)
    )
    
    logger.info(f"Image extraction task started: file_id={file_id}")
    
    return {"message": "图片提取任务已启动"}


@router.get("/{file_id}/images", response_model=List[ExtractedImageResponse])
def get_file_images(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    get_file_or_404(db, file_id, current_user.id)
    
    images = db.query(ExtractedImage).filter(
        ExtractedImage.file_id == file_id
    ).order_by(ExtractedImage.page_number, ExtractedImage.image_index).all()
    
    return images


@router.get("/{file_id}/images/{image_id}")
def download_image(
    file_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', image_id):
        raise HTTPException(status_code=400, detail="无效的图片ID")
    
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    image_record = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.file_id == file_id
    ).first()
    
    if not image_record:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    content_type_map = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'tiff': 'image/tiff',
        'webp': 'image/webp'
    }
    
    content_type = content_type_map.get(image_record.image_format.lower(), 'image/png')
    
    try:
        image_data = file_storage.read_image(image_record.image_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="图片文件不存在或已被删除")
    except Exception as e:
        logger.error(f"Failed to read image file: {e}")
        raise HTTPException(status_code=500, detail=f"读取图片失败: {str(e)}")
    
    base_filename = file_record.filename.rsplit('.', 1)[0] if '.' in file_record.filename else file_record.filename
    filename = f"{base_filename}_page{image_record.page_number}_img{image_record.image_index}.{image_record.image_format}"
    encoded_filename = quote(filename, safe='')
    
    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/{file_id}/images")
def delete_file_images(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    images = db.query(ExtractedImage).filter(ExtractedImage.file_id == file_id).all()
    for image in images:
        try:
            file_storage.delete_image(image.image_path)
        except Exception as e:
            logger.warning(f"Failed to delete image file {image.image_path}: {e}")
    
    deleted_count = db.query(ExtractedImage).filter(
        ExtractedImage.file_id == file_id
    ).delete()
    
    db.commit()
    
    logger.info(f"Deleted {deleted_count} images for file_id={file_id}")
    
    return {"message": f"已删除 {deleted_count} 张图片"}


@router.delete("/{file_id}/images/{image_id}")
def delete_single_image(
    file_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', image_id):
        raise HTTPException(status_code=400, detail="无效的图片ID")
    
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    image_record = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.file_id == file_id
    ).first()
    
    if not image_record:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        file_storage.delete_image(image_record.image_path)
    except Exception as e:
        logger.warning(f"Failed to delete image file {image_record.image_path}: {e}")
    
    db.delete(image_record)
    db.commit()
    
    logger.info(f"Deleted image {image_id} for file_id={file_id}")
    
    return {"message": "图片已删除"}


@router.post("", response_model=BaseFileResponse)
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    knowledge_base_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    logger.info(f"upload_file called: user_id={user_id}, knowledge_base_id={knowledge_base_id}, filename={file.filename}")
    
    if not re.match(r'^([a-f0-9\-]{36}|[a-f0-9]{32})$', knowledge_base_id):
        raise HTTPException(status_code=400, detail="无效的知识库ID")
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == knowledge_base_id,
        KnowledgeBase.user_id == user_id
    ).first()
    
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    allowed, wait_time = check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"上传过于频繁，请等待 {wait_time} 秒后再试"
        )
    
    if file.content_type not in ALLOWED_EXTENSIONS:
        allowed_types = ", ".join(["PDF", "Excel (.xlsx, .xls)", "Word (.docx, .doc)"])
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。允许的文件类型: {allowed_types}"
        )
    
    file_content = await file.read()
    
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大50MB）"
        )
    
    is_valid, result = validate_file_content(file_content, file.content_type)
    
    if not is_valid:
        logger.warning(f"文件验证失败: user={user_id}, filename={file.filename}, reason={result}")
        raise HTTPException(status_code=400, detail=result)
    
    original_filename = file.filename or "unknown"
    if result in ('heic', 'heif'):
        file_content, _ = convert_heic_to_jpeg(file_content)
        result = 'jpg'
        extension = '.jpg'
        if original_filename.lower().endswith(('.heic', '.heif')):
            original_filename = original_filename.rsplit('.', 1)[0] + '.jpg'
    else:
        extension = ALLOWED_EXTENSIONS.get(file.content_type, '')
    
    safe_filename = sanitize_filename(original_filename)
    file_id = uuid.uuid4().hex
    
    file_path, is_chunked = file_storage.save_file(file_id, file_content, extension)
    logger.info(f"File saved to filesystem: {file_path}, chunked={is_chunked}")
    
    new_file = BaseFile(
        id=file_id,
        filename=safe_filename,
        file_type=result,
        file_size=format_file_size(len(file_content)),
        file_path=file_path,
        is_chunked=is_chunked,
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        embedding_status="processing"
    )
    
    db.add(new_file)
    kb.file_count = (kb.file_count or 0) + 1
    
    try:
        db.commit()
        db.refresh(new_file)
    except Exception as e:
        logger.error(f"Database commit failed: {e}")
        file_storage.delete_file(file_path)
        raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")
    
    background_tasks.add_task(
        process_file_for_rag,
        str(new_file.id),
        file_content,
        result,
        knowledge_base_id,
        user_id
    )
    
    logger.info(f"文件上传成功: {safe_filename} (ID: {new_file.id}, KB: {kb.name}, user={user_id})")
    
    return new_file


@router.get("/{file_id}/status")
def get_file_status(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.file_id == file_id
    ).count()
    
    image_count = db.query(ExtractedImage).filter(
        ExtractedImage.file_id == file_id
    ).count()
    
    return {
        "id": file_record.id,
        "filename": file_record.filename,
        "embedding_status": file_record.embedding_status,
        "embedding_error": file_record.embedding_error,
        "image_extraction_status": file_record.image_extraction_status,
        "image_extraction_error": file_record.image_extraction_error,
        "image_count": image_count,
        "chunk_count": chunk_count
    }


@router.get("/{file_id}")
def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    try:
        file_content = file_storage.read_file(file_record.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在或已被删除")
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
    
    content_type_map = {
        'PDF': 'application/pdf',
        'Excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    content_type = content_type_map.get(str(file_record.file_type), 'application/octet-stream')
    encoded_filename = quote(str(file_record.filename))
    
    logger.info(f"文件下载: {file_record.filename} (ID: {file_id}, user={current_user.id})")
    
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    file_path = file_record.file_path
    
    images = db.query(ExtractedImage).filter(ExtractedImage.file_id == file_id).all()
    for image in images:
        try:
            file_storage.delete_image(image.image_path)
        except Exception as e:
            logger.warning(f"Failed to delete image file {image.image_path}: {e}")
    
    db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).delete()
    
    kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == file_record.knowledge_base_id
    ).first()
    
    if kb and kb.file_count and kb.file_count > 0:
        kb.file_count -= 1
    
    db.delete(file_record)
    db.commit()
    
    try:
        file_storage.delete_file(file_path)
        logger.info(f"File deleted from filesystem: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file from filesystem: {e}")
    
    logger.info(f"文件删除成功: {file_record.filename} (ID: {file_id}, user={current_user.id})")
    
    return {"message": "删除成功"}


class EmbeddingSettingsRequest:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap


from pydantic import BaseModel


class EmbeddingSettings(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200


@router.put("/{file_id}/embedding-settings")
def update_embedding_settings(
    file_id: str,
    settings: EmbeddingSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    if settings.chunk_size < 100 or settings.chunk_size > 8000:
        raise HTTPException(status_code=400, detail="分块大小必须在 100-8000 之间")
    
    if settings.chunk_overlap < 0 or settings.chunk_overlap > 1000:
        raise HTTPException(status_code=400, detail="重叠大小必须在 0-1000 之间")
    
    if settings.chunk_overlap >= settings.chunk_size:
        raise HTTPException(status_code=400, detail="重叠大小必须小于分块大小")
    
    file_record.chunk_size = settings.chunk_size
    file_record.chunk_overlap = settings.chunk_overlap
    db.commit()
    
    logger.info(f"Embedding设置已更新: file_id={file_id}, chunk_size={settings.chunk_size}, chunk_overlap={settings.chunk_overlap}")
    
    return {"message": "设置已保存", "chunk_size": settings.chunk_size, "chunk_overlap": settings.chunk_overlap}


@router.post("/{file_id}/re-embed")
def re_embed_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    validate_file_id(file_id)
    file_record = get_file_or_404(db, file_id, current_user.id)
    
    try:
        file_data = file_storage.read_file(file_record.file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在或已被删除")
    except Exception as e:
        logger.error(f"Failed to read file for re-embed: {e}")
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
    
    db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).delete()
    
    file_record.embedding_status = "processing"
    file_record.embedding_error = None
    db.commit()
    
    chunk_size = file_record.chunk_size or 1000
    chunk_overlap = file_record.chunk_overlap or 200
    
    background_tasks.add_task(
        process_file_for_rag_with_settings,
        str(file_record.id),
        file_data,
        str(file_record.file_type),
        str(file_record.knowledge_base_id),
        file_record.user_id,
        chunk_size,
        chunk_overlap
    )
    
    logger.info(f"重新生成Embedding任务已启动: file_id={file_id}")
    
    return {"message": "重新生成Embedding任务已启动"}
