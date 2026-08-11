from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app.schemas.test_case import (
    TestCaseFolderCreate,
    TestCaseFolderUpdate,
    TestCaseFolderResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseBatchCreate,
    TestCaseResponse,
    ImageInfo
)
from app.models.test_case_folder import TestCaseFolder
from app.models.test_case import TestCase
from app.models.file import BaseFile
from app.models.test_case_image import TestCaseImage
from app.models.extracted_image import ExtractedImage
from app.models.conversation import TestResult
from app.models.user import User
from app.auth import get_current_user
from app.services.file_storage import file_storage
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test-cases", tags=["测试用例"])


@router.get("/folders", response_model=List[TestCaseFolderResponse])
def get_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folders = db.query(TestCaseFolder).filter(
        TestCaseFolder.user_id == current_user.id
    ).order_by(TestCaseFolder.created_at.desc()).all()
    
    for folder in folders:
        folder.case_count = db.query(TestCase).filter(
            TestCase.folder_id == str(folder.id)
        ).count()
    
    return folders


@router.post("/folders", response_model=TestCaseFolderResponse)
def create_folder(
    folder_data: TestCaseFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = TestCaseFolder(
        name=folder_data.name,
        description=folder_data.description,
        user_id=current_user.id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    folder.case_count = 0
    return folder


@router.put("/folders/{folder_id}", response_model=TestCaseFolderResponse)
def update_folder(
    folder_id: str,
    folder_data: TestCaseFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    if folder_data.name is not None:
        folder.name = folder_data.name
    if folder_data.description is not None:
        folder.description = folder_data.description
    
    db.commit()
    db.refresh(folder)
    folder.case_count = db.query(TestCase).filter(
        TestCase.folder_id == str(folder.id)
    ).count()
    return folder


@router.delete("/folders/{folder_id}")
def delete_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    deleted_cases = db.query(TestCase).filter(
        TestCase.folder_id == folder_id
    ).delete()
    
    deleted_results = db.query(TestResult).filter(
        TestResult.test_folder_id == folder_id
    ).delete()
    
    db.delete(folder)
    db.commit()
    
    return {"message": "删除成功", "deleted_cases": deleted_cases, "deleted_results": deleted_results}


def get_case_images(db: Session, case_id: str) -> List[ImageInfo]:
    case_images = db.query(TestCaseImage).filter(
        TestCaseImage.test_case_id == case_id
    ).order_by(TestCaseImage.display_order).all()
    
    images = []
    for ci in case_images:
        image = db.query(ExtractedImage).filter(
            ExtractedImage.id == ci.image_id
        ).first()
        if image:
            images.append(ImageInfo(
                id=str(image.id),
                url=f"/api/test-cases/images/{image.id}",
                preview_url=f"/api/test-cases/images/{image.id}/preview"
            ))
    return images


@router.get("/folders/{folder_id}/cases", response_model=List[TestCaseResponse])
def get_cases(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    cases = db.query(TestCase).filter(
        TestCase.folder_id == folder_id
    ).order_by(TestCase.row_order, TestCase.created_at).all()
    
    result = []
    for case in cases:
        images = get_case_images(db, str(case.id))
        
        file_name = None
        if case.file_id:
            file = db.query(BaseFile).filter(
                BaseFile.id == case.file_id
            ).first()
            if file:
                file_name = file.filename
        
        result.append(TestCaseResponse(
            id=str(case.id),
            folder_id=str(case.folder_id),
            user_id=case.user_id,
            question=case.question,
            file_id=case.file_id,
            sample_answer=case.sample_answer,
            row_order=case.row_order,
            created_at=case.created_at,
            updated_at=case.updated_at,
            images=images,
            file_name=file_name
        ))
    
    return result


@router.post("/cases", response_model=TestCaseResponse)
def create_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == case_data.folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    max_order_result = db.query(func.max(TestCase.row_order)).filter(
        TestCase.folder_id == case_data.folder_id
    ).scalar()
    
    next_order = (max_order_result or 0) + 1
    
    case = TestCase(
        folder_id=case_data.folder_id,
        user_id=current_user.id,
        question=case_data.question,
        file_id=case_data.file_id,
        sample_answer=case_data.sample_answer,
        row_order=next_order
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    if case_data.image_ids:
        for order, image_id in enumerate(case_data.image_ids):
            case_image = TestCaseImage(
                test_case_id=str(case.id),
                image_id=image_id,
                display_order=order
            )
            db.add(case_image)
        db.commit()
    
    images = get_case_images(db, str(case.id))
    
    file_name = None
    if case.file_id:
        file = db.query(BaseFile).filter(
            BaseFile.id == case.file_id
        ).first()
        if file:
            file_name = file.filename
    
    result = TestCaseResponse(
        id=str(case.id),
        folder_id=str(case.folder_id),
        user_id=case.user_id,
        question=case.question,
        file_id=case.file_id,
        sample_answer=case.sample_answer,
        row_order=case.row_order,
        created_at=case.created_at,
        updated_at=case.updated_at,
        images=images,
        file_name=file_name
    )
    return result


@router.post("/cases/batch", response_model=List[TestCaseResponse])
def create_cases_batch(
    case_data: TestCaseBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == case_data.folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    max_order_result = db.query(func.max(TestCase.row_order)).filter(
        TestCase.folder_id == case_data.folder_id
    ).scalar()
    
    max_order = max_order_result or 0
    
    processed_cases = []
    for idx, case_item in enumerate(case_data.cases):
        row_order = case_item.row_order if case_item.row_order is not None else (max_order + idx + 1)
        
        existing_case = db.query(TestCase).filter(
            TestCase.folder_id == case_data.folder_id,
            TestCase.row_order == row_order
        ).first()
        
        if existing_case:
            if case_item.question is not None and case_item.question.strip():
                existing_case.question = case_item.question
            if case_item.sample_answer is not None and case_item.sample_answer.strip():
                existing_case.sample_answer = case_item.sample_answer
            
            if case_item.image_ids is not None and len(case_item.image_ids) > 0:
                db.query(TestCaseImage).filter(
                    TestCaseImage.test_case_id == str(existing_case.id)
                ).delete()
                
                for order, image_id in enumerate(case_item.image_ids):
                    case_image = TestCaseImage(
                        test_case_id=str(existing_case.id),
                        image_id=image_id,
                        display_order=order
                    )
                    db.add(case_image)
            
            processed_cases.append((existing_case, case_item))
        else:
            new_case = TestCase(
                folder_id=case_data.folder_id,
                user_id=current_user.id,
                question=case_item.question,
                file_id=case_item.file_id,
                sample_answer=case_item.sample_answer,
                row_order=row_order
            )
            db.add(new_case)
            db.flush()
            
            if case_item.image_ids:
                for order, image_id in enumerate(case_item.image_ids):
                    case_image = TestCaseImage(
                        test_case_id=str(new_case.id),
                        image_id=image_id,
                        display_order=order
                    )
                    db.add(case_image)
            
            processed_cases.append((new_case, case_item))
    
    db.commit()
    
    result = []
    for case, case_item in processed_cases:
        db.refresh(case)
        
        images = get_case_images(db, str(case.id))
        
        file_name = None
        if case.file_id:
            file = db.query(BaseFile).filter(
                BaseFile.id == case.file_id
            ).first()
            if file:
                file_name = file.filename
        
        result.append(TestCaseResponse(
            id=str(case.id),
            folder_id=str(case.folder_id),
            user_id=case.user_id,
            question=case.question,
            file_id=case.file_id,
            sample_answer=case.sample_answer,
            row_order=case.row_order,
            created_at=case.created_at,
            updated_at=case.updated_at,
            images=images,
            file_name=file_name
        ))
    
    return result


@router.put("/cases/{case_id}", response_model=TestCaseResponse)
def update_case(
    case_id: str,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(TestCase).filter(
        TestCase.id == case_id,
        TestCase.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if case_data.question is not None:
        case.question = case_data.question
    if case_data.image_ids is not None:
        db.query(TestCaseImage).filter(
            TestCaseImage.test_case_id == case_id
        ).delete()
        
        for order, image_id in enumerate(case_data.image_ids):
            case_image = TestCaseImage(
                test_case_id=case_id,
                image_id=image_id,
                display_order=order
            )
            db.add(case_image)
    if case_data.file_id is not None:
        case.file_id = case_data.file_id if case_data.file_id else None
    if case_data.sample_answer is not None:
        case.sample_answer = case_data.sample_answer
    
    db.commit()
    db.refresh(case)
    
    images = get_case_images(db, str(case.id))
    
    file_name = None
    if case.file_id:
        file = db.query(BaseFile).filter(
            BaseFile.id == case.file_id
        ).first()
        if file:
            file_name = file.filename
    
    result = TestCaseResponse(
        id=str(case.id),
        folder_id=str(case.folder_id),
        user_id=case.user_id,
        question=case.question,
        file_id=case.file_id,
        sample_answer=case.sample_answer,
        row_order=case.row_order,
        created_at=case.created_at,
        updated_at=case.updated_at,
        images=images,
        file_name=file_name
    )
    return result


@router.delete("/cases/{case_id}")
def delete_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(TestCase).filter(
        TestCase.id == case_id,
        TestCase.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    folder_id = case.folder_id
    deleted_row_order = case.row_order
    
    db.delete(case)
    db.commit()
    
    cases_to_update = db.query(TestCase).filter(
        TestCase.folder_id == folder_id,
        TestCase.row_order > deleted_row_order
    ).order_by(TestCase.row_order).all()
    
    for c in cases_to_update:
        c.row_order = c.row_order - 1
        db.commit()
    
    return {"message": "删除成功"}


@router.post("/cases/batch-delete")
def delete_cases_batch(
    case_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not case_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的用例")
    
    cases = db.query(TestCase).filter(
        TestCase.id.in_(case_ids),
        TestCase.user_id == current_user.id
    ).all()
    
    if not cases:
        raise HTTPException(status_code=404, detail="未找到要删除的用例")
    
    folder_ids = set(case.folder_id for case in cases)
    
    for case in cases:
        db.delete(case)
    
    db.commit()
    
    for folder_id in folder_ids:
        remaining_cases = db.query(TestCase).filter(
            TestCase.folder_id == folder_id
        ).order_by(TestCase.row_order).all()
        
        for idx, case in enumerate(remaining_cases):
            if case.row_order != idx + 1:
                case.row_order = idx + 1
                db.commit()
    
    return {"message": "批量删除成功", "deleted_count": len(cases)}


@router.put("/cases/reorder")
def reorder_cases(
    folder_id: str,
    case_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = db.query(TestCaseFolder).filter(
        TestCaseFolder.id == folder_id,
        TestCaseFolder.user_id == current_user.id
    ).first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")
    
    for idx, case_id in enumerate(case_ids):
        case = db.query(TestCase).filter(
            TestCase.id == case_id,
            TestCase.folder_id == folder_id
        ).first()
        if case:
            case.row_order = idx
    
    db.commit()
    
    return {"message": "排序成功"}


@router.get("/images/{image_id}")
def get_image(
    image_id: str,
    db: Session = Depends(get_db)
):
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        image_data = file_storage.read_image(image.image_path)
        content_type = f"image/{image.image_format.lower()}" if image.image_format else "image/png"
        from fastapi.responses import Response
        return Response(content=image_data, media_type=content_type)
    except Exception as e:
        logger.error(f"Error loading image: {e}")
        raise HTTPException(status_code=500, detail="无法加载图片")


@router.get("/images/{image_id}/preview")
def get_image_preview(
    image_id: str,
    db: Session = Depends(get_db)
):
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        image_data = file_storage.read_image(image.image_path)
        content_type = f"image/{image.image_format.lower()}" if image.image_format else "image/png"
        
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_data))
            
            max_size = 200
            if max(img.width, img.height) > max_size:
                ratio = max_size / max(img.width, img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img_format = image.image_format.upper() if image.image_format else 'PNG'
            if img_format == 'JPG':
                img_format = 'JPEG'
            img.save(output, format=img_format)
            preview_data = output.getvalue()
            
            from fastapi.responses import Response
            return Response(content=preview_data, media_type=content_type)
        except Exception as e:
            logger.warning(f"Error creating preview, returning original: {e}")
            from fastapi.responses import Response
            return Response(content=image_data, media_type=content_type)
    except Exception as e:
        logger.error(f"Error loading image: {e}")
        raise HTTPException(status_code=500, detail="无法加载图片")


@router.get("/knowledge-bases")
def get_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.knowledge_base import KnowledgeBase
    
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.user_id == current_user.id
    ).all()
    
    return [{"id": str(kb.id), "name": kb.name} for kb in knowledge_bases]


@router.get("/knowledge-bases/{kb_id}/files")
def get_knowledge_base_files(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    files = db.query(BaseFile).filter(
        BaseFile.knowledge_base_id == kb_id,
        BaseFile.user_id == current_user.id
    ).all()
    
    return [{"id": str(f.id), "filename": f.filename, "file_type": f.file_type} for f in files]


@router.get("/files/{file_id}/preview")
def preview_file_content(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file = db.query(BaseFile).filter(
        BaseFile.id == file_id,
        BaseFile.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        file_data = file_storage.read_file(file.file_path)
        
        if file.file_type.lower() in ['xlsx', 'xls']:
            import io
            import pandas as pd
            
            df = pd.read_excel(io.BytesIO(file_data), sheet_name=0)
            
            columns = df.columns.tolist()
            rows = df.head(50).fillna('').to_dict('records')
            
            return {
                "file_type": "excel",
                "columns": columns,
                "rows": rows,
                "total_rows": len(df)
            }
        else:
            from app.services.text_extractor import TextExtractor
            extractor = TextExtractor()
            text = extractor.extract_text(file_data, file.file_type)
            
            if text is None:
                text = ""
            
            lines = [line.strip() for line in text.split('\n') if line.strip()][:100]
            
            return {
                "file_type": "document",
                "content": text[:5000],
                "lines": lines
            }
    except Exception as e:
        logger.error(f"Error previewing file: {e}")
        raise HTTPException(status_code=500, detail=f"无法读取文件: {str(e)}")


@router.get("/files/{file_id}/images")
def get_file_images(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    images = db.query(ExtractedImage).filter(
        ExtractedImage.file_id == file_id
    ).all()
    
    result = []
    for img in images:
        result.append({
            "id": str(img.id),
            "page_number": img.page_number,
            "image_index": img.image_index,
            "width": img.width,
            "height": img.height,
            "preview_url": f"/api/test-cases/images/{img.id}/preview"
        })
    
    return result
