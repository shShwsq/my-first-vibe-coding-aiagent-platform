from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
from pathlib import Path
import json
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user
from app.services.llm_client import get_intent_model_config, call_llm, stream_llm
from app.services.workflow.parser import WorkflowParser
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/workflow-ai", tags=["工作流AI助手"])


WORKFLOW_LANGUAGE_DOC = Path(__file__).parent.parent / "services" / "workflow" / "README_language.md"


def load_workflow_language_doc() -> str:
    try:
        return WORKFLOW_LANGUAGE_DOC.read_text(encoding="utf-8")
    except Exception:
        return ""


class WorkflowCheckRequest(BaseModel):
    code: str


class WorkflowGenerateRequest(BaseModel):
    requirements: str
    current_code: Optional[str] = ""


class WorkflowIssue(BaseModel):
    line: int
    message: str
    severity: str = "warning"


class WorkflowCheckResponse(BaseModel):
    success: bool
    issues: List[WorkflowIssue]
    message: str


class WorkflowGenerateResponse(BaseModel):
    success: bool
    code: str
    message: str


def build_check_system_prompt() -> str:
    language_doc = load_workflow_language_doc()
    
    return f"""你是一个专业的工作流代码审查专家。你的任务是检查工作流代码中的问题并给出具体的行数。

以下是工作流语言的完整规范：

{language_doc}

语法结构说明：
- 节点定义以**不在字符串里的分号**分隔
- 代码节点用{{}}或``````包裹
- 工作流代码由"节点定义"和"代码节点"交替组成
- 节点定义以分号结束，分号后可选跟随一个代码节点（用`{{}}`或` ``` `包裹），该代码节点的节点ID自动设置为前一个节点ID加`_code`后缀

**重要：节点定义的解析规则**：
- 解析器会将节点定义中**不在字符串内的换行符去除**，将多行节点合并为单行JSON
- 因此节点定义可以跨越多行书写，字符串值中的换行符在解析时会被保留
- **不要误报**：节点定义中的多行字符串不是错误，解析器会正确处理
- **不要误报**：节点定义跨行书写不是错误，只要最后一行有分号即可
- **不要误报**：字符串值内部允许包含换行符，这是合法的，解析器会保留字符串内的换行符

**重要：字符串内的表达式占位符**：
- 节点参数中的字符串值可以包含 `{{ctx.xxx()}}` 或 `{{memory.xxx()}}` 等占位符
- 这些占位符在运行时会由执行器自动替换为实际值
- **不要误报**：字符串内的 `{{ctx.output(1).content}}` 等写法是合法的，不是JSON语法错误
- **不要误报**：字符串内的 `{{memory.get("answer")}}` 等写法是合法的，不是JSON语法错误

请检查以下方面：
1. 语法错误（括号不匹配、节点格式错误等）
2. 节点ID引用错误（引用了不存在的节点ID）
3. 逻辑错误（跳转逻辑不合理、条件判断错误等）
4. 参数使用错误（使用了不存在的参数、参数类型错误等）
5. 是否符合上述语言规范


# 一般节点参数说明
其他规则：
- 节点必须包含"id"和"node"字段，不同节点根据节点参数说明检查参数是否正确
- ctx.output()中的节点ID必须是实际存在的节点
- ctx.goto()中的节点ID必须是实际存在的节点

行号说明：
- 代码每行前面已经标注了行号（如 "  1 | "、"  2 | "）
- 请直接使用代码行前面的行号指出问题所在
- 不要自行计算行号或添加偏移量

请以JSON格式返回结果，格式如下：
{{
    "success": true/false,
    "issues": [
        {{"line": 行号, "message": "问题描述", "severity": "error/warning/info"}}
    ],
    "message": "总体评价"
}}

只返回JSON，不要返回其他内容。"""


def build_generate_system_prompt() -> str:
    language_doc = load_workflow_language_doc()
    
    return f"""你是一个专业的工作流代码生成专家。你的任务是根据用户的要求生成或修改工作流代码。

以下是工作流语言的完整规范：

{language_doc}

请根据用户要求生成完整的工作流代码。

重要规则：
1. 严格遵守上述语言规范
2. 节点必须以分号结尾
3. 节点必须包含"id"和"node"字段
4. 代码节点必须用{{}}或``````包裹
5. 确保节点ID引用正确
6. 确保逻辑正确

只返回代码，不要返回其他解释。"""


@router.post("/check")
async def check_workflow_code_stream(
    request: WorkflowCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    model_config = get_intent_model_config(db)
    
    if not model_config:
        raise HTTPException(status_code=500, detail="未配置功能模型")
    
    parser = WorkflowParser()
    parse_error = None
    parse_issues = []
    
    try:
        is_valid, message, params = parser.validate(request.code)
        if not is_valid:
            parse_error = message
            parse_issues.append({
                "line": 0,
                "message": f"解析错误: {message}",
                "severity": "error"
            })
    except Exception as e:
        parse_error = str(e)
        parse_issues.append({
            "line": 0,
            "message": f"解析异常: {str(e)}",
            "severity": "error"
        })
    
    # 为代码添加行号，方便大模型准确定位
    code_lines = request.code.split('\n')
    numbered_code = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(code_lines)])
    
    user_content = f"""请检查以下工作流代码的问题。每行代码前面已经标注了行号：

{numbered_code}

请根据行号直接指出问题所在的行。"""
    if parse_error:
        user_content += f"\n\n注意：代码解析失败，错误信息：{parse_error}\n请尝试找出代码中的语法问题。"
    
    messages = [
        {"role": "system", "content": build_check_system_prompt()},
        {"role": "user", "content": user_content}
    ]
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        if parse_issues:
            for issue in parse_issues:
                yield f"data: {json.dumps({'type': 'issue', 'data': issue})}\n\n"
        
        full_content = ""
        async for chunk in stream_llm(
            messages=messages,
            model=model_config["model"],
            api_key=model_config["api_key"],
            url=model_config["url"],
            call_type=model_config["call_type"]
        ):
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str and data_str != "[DONE]":
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            full_content += data["content"]
                            yield f"data: {json.dumps({'type': 'chunk', 'content': data['content']})}\n\n"
                        elif "error" in data:
                            yield f"data: {json.dumps({'type': 'error', 'message': data['error']})}\n\n"
                            return
                    except json.JSONDecodeError:
                        continue
        
        yield f"data: {json.dumps({'type': 'complete', 'content': full_content})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/generate")
async def generate_workflow_code_stream(
    request: WorkflowGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    model_config = get_intent_model_config(db)
    
    if not model_config:
        raise HTTPException(status_code=500, detail="未配置功能模型")
    
    user_content = f"用户要求：{request.requirements}"
    if request.current_code:
        user_content += f"\n\n当前代码（请在此基础上修改）：\n{request.current_code}"
    else:
        user_content += "\n\n请生成全新的工作流代码。"
    
    messages = [
        {"role": "system", "content": build_generate_system_prompt()},
        {"role": "user", "content": user_content}
    ]
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        full_content = ""
        async for chunk in stream_llm(
            messages=messages,
            model=model_config["model"],
            api_key=model_config["api_key"],
            url=model_config["url"],
            call_type=model_config["call_type"]
        ):
            if chunk.startswith("data: "):
                data_str = chunk[6:].strip()
                if data_str and data_str != "[DONE]":
                    try:
                        data = json.loads(data_str)
                        if "content" in data:
                            full_content += data["content"]
                            yield f"data: {json.dumps({'type': 'chunk', 'content': data['content']})}\n\n"
                        elif "error" in data:
                            yield f"data: {json.dumps({'type': 'error', 'message': data['error']})}\n\n"
                            return
                    except json.JSONDecodeError:
                        continue
        
        yield f"data: {json.dumps({'type': 'complete', 'content': full_content})}\n\n"
    
    return StreamingResponse(generate_stream(), media_type="text/event-stream")
