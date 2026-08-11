from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.workflow_agent import WorkflowAgentCreate, WorkflowAgentUpdate, WorkflowAgentResponse
from app.models.workflow_agent import WorkflowAgent
from app.models.workflow_log import WorkflowLog
from app.models.user import User
from app.auth import get_current_user
from typing import List, Optional

router = APIRouter(prefix="/workflow-agents", tags=["工作流智能体管理"])


@router.get("", response_model=List[WorkflowAgentResponse])
def get_workflow_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agents = db.query(WorkflowAgent).filter(WorkflowAgent.user_id == current_user.id).all()
    return agents


@router.get("/{agent_id}", response_model=WorkflowAgentResponse)
def get_workflow_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.id == agent_id,
        WorkflowAgent.user_id == current_user.id
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="工作流智能体不存在")
    return agent


@router.get("/check-name/{name}")
def check_workflow_agent_name(
    name: str,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WorkflowAgent).filter(
        WorkflowAgent.user_id == current_user.id,
        WorkflowAgent.name == name
    )
    
    if agent_id:
        query = query.filter(WorkflowAgent.id != agent_id)
    
    existing_agent = query.first()
    
    return {"available": existing_agent is None}


@router.post("", response_model=WorkflowAgentResponse)
def create_workflow_agent(
    agent_data: WorkflowAgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.user_id == current_user.id,
        WorkflowAgent.name == agent_data.name
    ).first()
    
    if existing_agent:
        raise HTTPException(status_code=400, detail=f"工作流智能体名称 '{agent_data.name}' 已存在，请使用其他名称")
    
    new_agent = WorkflowAgent(
        user_id=current_user.id,
        name=agent_data.name,
        description=agent_data.description,
        workflow_code=None,
        is_active=True
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent


@router.put("/{agent_id}", response_model=WorkflowAgentResponse)
def update_workflow_agent(
    agent_id: int,
    agent_data: WorkflowAgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.id == agent_id,
        WorkflowAgent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="工作流智能体不存在")
    
    if agent_data.name:
        existing_agent = db.query(WorkflowAgent).filter(
            WorkflowAgent.user_id == current_user.id,
            WorkflowAgent.name == agent_data.name,
            WorkflowAgent.id != agent_id
        ).first()
        
        if existing_agent:
            raise HTTPException(status_code=400, detail=f"工作流智能体名称 '{agent_data.name}' 已存在，请使用其他名称")
    
    update_data = agent_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
def delete_workflow_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.workflow_long_memory import WorkflowLongMemory
    
    agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.id == agent_id,
        WorkflowAgent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="工作流智能体不存在")
    
    db.query(WorkflowLog).filter(
        WorkflowLog.agent_id == agent_id
    ).delete(synchronize_session=False)
    
    db.query(WorkflowLongMemory).filter(
        WorkflowLongMemory.user_id == current_user.id,
        WorkflowLongMemory.agent_id == agent_id
    ).delete(synchronize_session=False)
    
    db.delete(agent)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{agent_id}/clear-long-memory")
def clear_workflow_long_memory(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.workflow_long_memory import WorkflowLongMemory
    
    agent = db.query(WorkflowAgent).filter(
        WorkflowAgent.id == agent_id,
        WorkflowAgent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="工作流智能体不存在")
    
    deleted = db.query(WorkflowLongMemory).filter(
        WorkflowLongMemory.user_id == current_user.id,
        WorkflowLongMemory.agent_id == agent_id
    ).delete(synchronize_session=False)
    
    db.commit()
    return {"message": "清除成功", "deleted_count": deleted}
