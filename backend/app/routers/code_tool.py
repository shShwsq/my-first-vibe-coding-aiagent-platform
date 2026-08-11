import time
import logging
import traceback
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.code_tool import (
    CodeToolCreate, 
    CodeToolUpdate, 
    CodeToolResponse,
    CodeToolExecuteRequest,
    CodeToolExecuteResponse
)
from app.models.code_tool import CodeTool
from app.models.user import User
from app.auth import get_current_user
from typing import List, Optional
from app.utils.param_converter import convert_param_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/code-tools", tags=["代码工具管理"])


@router.get("", response_model=List[CodeToolResponse])
def get_code_tools(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tools = db.query(CodeTool).filter(CodeTool.user_id == current_user.id).all()
    return tools


@router.get("/{tool_id}", response_model=CodeToolResponse)
def get_code_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.id == tool_id,
        CodeTool.user_id == current_user.id
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail="代码工具不存在")
    return tool


@router.get("/by-name/{name}", response_model=CodeToolResponse)
def get_code_tool_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.user_id == current_user.id,
        CodeTool.name == name
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"代码工具 '{name}' 不存在")
    return tool


@router.get("/check-name/{name}")
def check_code_tool_name(
    name: str,
    tool_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(CodeTool).filter(
        CodeTool.user_id == current_user.id,
        CodeTool.name == name
    )
    
    if tool_id:
        query = query.filter(CodeTool.id != tool_id)
    
    existing_tool = query.first()
    
    return {"available": existing_tool is None}


@router.post("", response_model=CodeToolResponse)
def create_code_tool(
    tool_data: CodeToolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_tool = db.query(CodeTool).filter(
        CodeTool.user_id == current_user.id,
        CodeTool.name == tool_data.name
    ).first()
    
    if existing_tool:
        raise HTTPException(status_code=400, detail=f"代码工具名称 '{tool_data.name}' 已存在，请使用其他名称")
    
    if not is_valid_function_name(tool_data.name):
        raise HTTPException(status_code=400, detail="函数名只能包含字母、数字和下划线，且必须以字母或下划线开头")
    
    new_tool = CodeTool(
        user_id=current_user.id,
        name=tool_data.name,
        display_name=tool_data.display_name,
        description=tool_data.description,
        code=tool_data.code,
        parameters=[p.model_dump() for p in tool_data.parameters] if tool_data.parameters else None,
        return_type=tool_data.return_type,
        is_active=True
    )
    db.add(new_tool)
    db.commit()
    db.refresh(new_tool)
    return new_tool


@router.put("/{tool_id}", response_model=CodeToolResponse)
def update_code_tool(
    tool_id: int,
    tool_data: CodeToolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.id == tool_id,
        CodeTool.user_id == current_user.id
    ).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="代码工具不存在")
    
    if tool_data.name:
        existing_tool = db.query(CodeTool).filter(
            CodeTool.user_id == current_user.id,
            CodeTool.name == tool_data.name,
            CodeTool.id != tool_id
        ).first()
        
        if existing_tool:
            raise HTTPException(status_code=400, detail=f"代码工具名称 '{tool_data.name}' 已存在，请使用其他名称")
        
        if not is_valid_function_name(tool_data.name):
            raise HTTPException(status_code=400, detail="函数名只能包含字母、数字和下划线，且必须以字母或下划线开头")
    
    update_data = tool_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'parameters' and value is not None:
            value = [p.model_dump() if hasattr(p, 'model_dump') else p for p in value]
        setattr(tool, key, value)
    
    db.commit()
    db.refresh(tool)
    return tool


@router.delete("/{tool_id}")
def delete_code_tool(
    tool_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.id == tool_id,
        CodeTool.user_id == current_user.id
    ).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="代码工具不存在")
    
    db.delete(tool)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{tool_id}/execute", response_model=CodeToolExecuteResponse)
def execute_code_tool(
    tool_id: int,
    request: CodeToolExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.id == tool_id,
        CodeTool.user_id == current_user.id
    ).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="代码工具不存在")
    
    if not tool.is_active:
        raise HTTPException(status_code=400, detail="代码工具已禁用")
    
    tool_data = {
        "name": tool.name,
        "code": tool.code,
        "parameters": tool.parameters
    }
    
    db.close()
    
    return execute_tool_code_from_data(tool_data, request.arguments)


@router.post("/by-name/{name}/execute", response_model=CodeToolExecuteResponse)
def execute_code_tool_by_name(
    name: str,
    request: CodeToolExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tool = db.query(CodeTool).filter(
        CodeTool.user_id == current_user.id,
        CodeTool.name == name
    ).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"代码工具 '{name}' 不存在")
    
    if not tool.is_active:
        raise HTTPException(status_code=400, detail="代码工具已禁用")
    
    tool_data = {
        "name": tool.name,
        "code": tool.code,
        "parameters": tool.parameters
    }
    
    db.close()
    
    return execute_tool_code_from_data(tool_data, request.arguments)


def is_valid_function_name(name: str) -> bool:
    if not name:
        return False
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, name))


class NoOpCtx:
    """用于前端测试运行时的空操作 ctx，当代码调用 ctx.verbose_return() 等方法时不会报错"""
    def __getattr__(self, name):
        def no_op(*args, **kwargs):
            pass
        return no_op


def _serialize_result(result):
    import pandas as pd
    
    if result is None:
        return result
    
    if isinstance(result, pd.DataFrame):
        return {
            "__type__": "DataFrame",
            "columns": list(result.columns),
            "shape": list(result.shape),
            "head": result.head(5).to_dict(orient="records"),
            "dtypes": {col: str(dtype) for col, dtype in result.dtypes.items()}
        }
    
    if isinstance(result, dict):
        return {k: _serialize_result(v) for k, v in result.items()}
    
    if isinstance(result, (list, tuple)):
        return [_serialize_result(item) for item in result]
    
    return result


def execute_tool_code_from_data(tool_data: dict, arguments: dict, ctx=None) -> CodeToolExecuteResponse:
    """
    从工具数据执行代码（不依赖数据库连接）
    
    参数:
        tool_data: 包含 name, code, parameters 的字典
        arguments: 函数参数
        ctx: 上下文对象（可选）
    """
    start_time = time.time()
    
    try:
        parameters = tool_data.get("parameters", [])
        if parameters:
            param_types = {p.get("name"): p.get("type", "str") for p in parameters}
            param_required = {p.get("name"): p.get("required", True) for p in parameters}
            logger.debug(f"参数类型定义: {param_types}")
            logger.debug(f"参数必填定义: {param_required}")
            
            converted_args = {}
            for key, value in arguments.items():
                param_type = param_types.get(key, "str")
                original_type = type(value).__name__
                converted_args[key] = convert_param_type(value, param_type)
                converted_type = type(converted_args[key]).__name__
                logger.debug(f"参数转换: {key} [{original_type}] -> [{converted_type}] (目标类型: {param_type})")
            
            for param_name, required in param_required.items():
                if not required and param_name not in converted_args:
                    converted_args[param_name] = None
                    logger.debug(f"非必填参数 {param_name} 未传递，设置为 None")
            
            arguments = converted_args
            logger.debug(f"转换后的参数: {list(arguments.keys())}")
        
        global_vars = {
            "__builtins__": __builtins__,
        }
        
        global_vars["ctx"] = ctx if ctx is not None else NoOpCtx()
        
        exec(tool_data["code"], global_vars)
        
        if tool_data["name"] not in global_vars:
            return CodeToolExecuteResponse(
                success=False,
                error=f"代码中未找到函数定义: {tool_data['name']}",
                execution_time=time.time() - start_time
            )
        
        func = global_vars[tool_data["name"]]
        
        if not callable(func):
            return CodeToolExecuteResponse(
                success=False,
                error=f"{tool_data['name']} 不是可调用的函数",
                execution_time=time.time() - start_time
            )
        
        result = func(**arguments)
        
        if result is not None:
            result = _serialize_result(result)
        
        execution_time = time.time() - start_time
        
        return CodeToolExecuteResponse(
            success=True,
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"执行代码工具 {tool_data['name']} 失败: {error_msg}")
        logger.error(traceback.format_exc())
        
        return CodeToolExecuteResponse(
            success=False,
            error=error_msg,
            execution_time=time.time() - start_time
        )


def execute_tool_code(tool: CodeTool, arguments: dict, ctx=None) -> CodeToolExecuteResponse:
    start_time = time.time()
    
    try:
        global_vars = {
            "__builtins__": __builtins__,
        }
        
        global_vars["ctx"] = ctx if ctx is not None else NoOpCtx()
        
        exec(tool.code, global_vars)
        
        if tool.name not in global_vars:
            return CodeToolExecuteResponse(
                success=False,
                error=f"代码中未找到函数定义: {tool.name}",
                execution_time=time.time() - start_time
            )
        
        func = global_vars[tool.name]
        
        if not callable(func):
            return CodeToolExecuteResponse(
                success=False,
                error=f"{tool.name} 不是可调用的函数",
                execution_time=time.time() - start_time
            )
        
        result = func(**arguments)
        
        execution_time = time.time() - start_time
        
        return CodeToolExecuteResponse(
            success=True,
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"执行代码工具 {tool.name} 失败: {error_msg}")
        logger.error(traceback.format_exc())
        
        return CodeToolExecuteResponse(
            success=False,
            error=error_msg,
            execution_time=time.time() - start_time
        )
