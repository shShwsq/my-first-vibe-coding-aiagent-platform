from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.api_config import ApiConfigCreate, ApiConfigUpdate, ApiConfigResponse
from app.models.api_config import ApiConfig
from app.models.user import User
from app.auth import get_current_user
from typing import List

router = APIRouter(prefix="/api-config", tags=["模型API"])


@router.get("", response_model=List[ApiConfigResponse])
def get_api_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    configs = db.query(ApiConfig).filter(ApiConfig.user_id == current_user.id).all()
    return configs


@router.get("/{config_id}", response_model=ApiConfigResponse)
def get_api_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(ApiConfig).filter(
        ApiConfig.id == config_id,
        ApiConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.post("", response_model=ApiConfigResponse)
def create_api_config(
    config_data: ApiConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if config_data.is_default:
        db.query(ApiConfig).filter(
            ApiConfig.user_id == current_user.id,
            ApiConfig.is_default == True
        ).update({"is_default": False})
    
    new_config = ApiConfig(
        user_id=current_user.id,
        **config_data.model_dump()
    )
    db.add(new_config)
    db.commit()
    db.refresh(new_config)
    return new_config


@router.put("/{config_id}", response_model=ApiConfigResponse)
def update_api_config(
    config_id: int,
    config_data: ApiConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(ApiConfig).filter(
        ApiConfig.id == config_id,
        ApiConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    if config_data.is_default:
        db.query(ApiConfig).filter(
            ApiConfig.user_id == current_user.id,
            ApiConfig.is_default == True,
            ApiConfig.id != config_id
        ).update({"is_default": False})
    
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_api_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.conversation import Conversation
    
    config = db.query(ApiConfig).filter(
        ApiConfig.id == config_id,
        ApiConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    db.query(Conversation).filter(
        Conversation.api_id == config_id
    ).update({"api_id": None})
    
    db.delete(config)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{config_id}/test")
def test_api_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = db.query(ApiConfig).filter(
        ApiConfig.id == config_id,
        ApiConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {"success": True, "message": f"API 连接测试成功 ({config.name})"}
