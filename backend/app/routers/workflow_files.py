import os
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["workflow-files"])

WORKFLOW_FILES_DIR = Path(__file__).parent.parent.parent / "workflow_files"


class DeleteFilesRequest(BaseModel):
    file_paths: List[str]


@router.get("/workflow-files/{file_path:path}")
async def get_workflow_file(file_path: str):
    """
    获取工作流生成的文件
    """
    full_path = WORKFLOW_FILES_DIR / file_path
    
    if not full_path.exists():
        logger.error(f"Workflow file not found: {full_path}")
        raise HTTPException(status_code=404, detail="文件不存在")
    
    if not str(full_path.resolve()).startswith(str(WORKFLOW_FILES_DIR.resolve())):
        logger.error(f"Path traversal attempt: {file_path}")
        raise HTTPException(status_code=403, detail="禁止访问")
    
    return FileResponse(
        path=full_path,
        filename=full_path.name,
        media_type="application/octet-stream"
    )


@router.post("/workflow-files/delete")
async def delete_workflow_files(
    request: DeleteFilesRequest,
    current_user: User = Depends(get_current_user)
):
    """
    删除工作流测试生成的文件
    """
    deleted = []
    failed = []
    
    for file_path in request.file_paths:
        try:
            full_path = WORKFLOW_FILES_DIR / file_path
            
            if not str(full_path.resolve()).startswith(str(WORKFLOW_FILES_DIR.resolve())):
                failed.append({"path": file_path, "reason": "禁止访问"})
                continue
            
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                deleted.append(file_path)
                logger.info(f"Deleted workflow test file: {file_path}")
            else:
                failed.append({"path": file_path, "reason": "文件不存在"})
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            failed.append({"path": file_path, "reason": str(e)})
    
    return {"deleted": deleted, "failed": failed}


@router.post("/workflow-files/delete-beacon")
async def delete_workflow_files_beacon(request: DeleteFilesRequest):
    """
    删除工作流测试生成的文件（用于 sendBeacon，无需认证）
    """
    deleted = []
    failed = []
    
    for file_path in request.file_paths:
        try:
            full_path = WORKFLOW_FILES_DIR / file_path
            
            if not str(full_path.resolve()).startswith(str(WORKFLOW_FILES_DIR.resolve())):
                failed.append({"path": file_path, "reason": "禁止访问"})
                continue
            
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                deleted.append(file_path)
                logger.info(f"Deleted workflow test file (beacon): {file_path}")
            else:
                failed.append({"path": file_path, "reason": "文件不存在"})
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            failed.append({"path": file_path, "reason": str(e)})
    
    return {"deleted": deleted, "failed": failed}
