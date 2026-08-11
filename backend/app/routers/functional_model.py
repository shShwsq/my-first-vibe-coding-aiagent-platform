from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.functional_model import FunctionalModel
from app.models.user import User
from app.auth import get_current_user
from app.schemas.functional_model import (
    FunctionalModelCreate,
    FunctionalModelUpdate,
    FunctionalModelResponse
)

router = APIRouter(prefix="/functional-models", tags=["功能模型管理"])


def check_superuser(current_user: User):
    if current_user.is_superuser is not True:
        raise HTTPException(status_code=403, detail="只有超级管理员可以管理功能模型")


@router.get("", response_model=List[FunctionalModelResponse])
def get_functional_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superuser(current_user)
    return db.query(FunctionalModel).all()


@router.get("/by-type/{functional_type}", response_model=FunctionalModelResponse)
def get_functional_model_by_type(
    functional_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    model = db.query(FunctionalModel).filter(
        FunctionalModel.functional_type == functional_type,
        FunctionalModel.is_active == True
    ).first()
    if not model:
        return None
    return model


@router.get("/{model_id}", response_model=FunctionalModelResponse)
def get_functional_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superuser(current_user)
    model = db.query(FunctionalModel).filter(FunctionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="功能模型不存在")
    return model


@router.post("", response_model=FunctionalModelResponse)
def create_functional_model(
    model_data: FunctionalModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superuser(current_user)
    
    existing = db.query(FunctionalModel).filter(
        FunctionalModel.functional_type == model_data.functional_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"类型 '{model_data.functional_type}' 的功能模型已存在，请编辑现有配置"
        )
    
    new_model = FunctionalModel(**model_data.model_dump())
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    return new_model


@router.put("/{model_id}", response_model=FunctionalModelResponse)
def update_functional_model(
    model_id: int,
    model_data: FunctionalModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superuser(current_user)
    
    model = db.query(FunctionalModel).filter(FunctionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="功能模型不存在")
    
    update_data = model_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
    
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}")
def delete_functional_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superuser(current_user)
    
    model = db.query(FunctionalModel).filter(FunctionalModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="功能模型不存在")
    
    db.delete(model)
    db.commit()
    return {"message": "删除成功"}
