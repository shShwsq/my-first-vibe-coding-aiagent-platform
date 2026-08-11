import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.workflow_agent import WorkflowAgent
from app.auth import get_current_user
from app.routers.unified_agent_chat import run_workflow_agent_stream
from app.services.workflow import WorkflowParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow-test", tags=["工作流测试"])


class WorkflowTestRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None
    conversation_id: Optional[int] = None
    code: Optional[str] = None


class ParseRequest(BaseModel):
    code: str


class ParseResponse(BaseModel):
    success: bool
    message: str
    params: List[Dict[str, Any]]
    nodes: Optional[Dict[str, Any]] = None


@router.post("/parse", response_model=ParseResponse)
async def parse_workflow_code(
    request: ParseRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        parser = WorkflowParser()
        success, message, params = parser.validate(request.code)
        
        nodes = None
        if success:
            nodes = parser.nodes
        
        return ParseResponse(
            success=success,
            message=message,
            params=params,
            nodes=nodes
        )
    except Exception as e:
        logger.error(f"Parse workflow code failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return ParseResponse(
            success=False,
            message=f"解析失败: {str(e)}",
            params=[]
        )


@router.post("/{agent_id}/stream")
async def test_workflow_stream(
    agent_id: int,
    request: WorkflowTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.id == agent_id,
        WorkflowAgent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="工作流智能体不存在")
    
    async def generate():
        context = {}
        try:
            async for item in run_workflow_agent_stream(
                agent=agent,
                query=request.query,
                user_id=current_user.id,
                params=request.params,
                conversation_id=request.conversation_id,
                context=context,
                include_header=True,
                workflow_code_override=request.code
            ):
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'context', 'context': {'ui_config': context.get('ui_config'), 'saved_files': context.get('saved_files'), 'full_content': context.get('full_content')}}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Workflow test failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
