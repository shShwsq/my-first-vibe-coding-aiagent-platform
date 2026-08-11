from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, GenerateCodeRequest, TestCallRequest
from app.models.agent import Agent
from app.models.api_config import ApiConfig
from app.models.user import User
from app.models.functional_model import FunctionalModel
from app.auth import get_current_user
from app.services.llm_client import (
    extract_content_with_config,
    extract_content_from_stream_data,
    detect_response_type,
    call_llm
)
from app.prompts import (
    CODE_GENERATION_SYSTEM_PROMPT,
    CODE_GENERATION_USER_PROMPT,
    RESPONSE_CONFIG_SYSTEM_PROMPT,
    RESPONSE_CONFIG_USER_PROMPT
)
from app.http_client import http_client_manager
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["智能体管理"])


@router.get("", response_model=List[AgentResponse])
def get_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return agent


@router.get("/check-name/{name}")
def check_agent_name(
    name: str,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Agent).filter(
        Agent.user_id == current_user.id,
        Agent.name == name
    )
    
    if agent_id:
        query = query.filter(Agent.id != agent_id)
    
    existing_agent = query.first()
    
    return {"available": existing_agent is None}


@router.post("", response_model=AgentResponse)
def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_agent = db.query(Agent).filter(
        Agent.user_id == current_user.id,
        Agent.name == agent_data.name
    ).first()
    
    if existing_agent:
        raise HTTPException(status_code=400, detail=f"智能体名称 '{agent_data.name}' 已存在，请使用其他名称")
    
    new_agent = Agent(
        user_id=current_user.id,
        **agent_data.model_dump()
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    if agent_data.name:
        existing_agent = db.query(Agent).filter(
            Agent.user_id == current_user.id,
            Agent.name == agent_data.name,
            Agent.id != agent_id
        ).first()
        
        if existing_agent:
            raise HTTPException(status_code=400, detail=f"智能体名称 '{agent_data.name}' 已存在，请使用其他名称")
    
    update_data = agent_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}")
def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    db.delete(agent)
    db.commit()
    return {"message": "删除成功"}


@router.post("/generate-code")
async def generate_call_code(
    request: GenerateCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.functional_config import get_code_gen_config
    
    code_gen_model = get_code_gen_config(db)
    
    if code_gen_model:
        model_name = code_gen_model.get("model", "")
        model_code = code_gen_model.get("model", "")
        model_api_key = code_gen_model.get("api_key", "")
        model_api_url = code_gen_model.get("url", "https://api.openai.com/v1")
        call_type = str(code_gen_model.get("call_type", "OpenAI Chat"))
        logger.info(f"使用配置的代码生成模型: {model_name} (code: {model_code})")
    else:
        default_config = db.query(ApiConfig).filter(
            ApiConfig.user_id == current_user.id,
            ApiConfig.is_default == True
        ).first()
        
        if not default_config:
            default_config = db.query(ApiConfig).filter(
                ApiConfig.user_id == current_user.id
            ).first()
        
        if not default_config:
            raise HTTPException(status_code=400, detail="请先配置默认大模型或由管理员配置代码生成模型")
        
        model_name = default_config.name
        model_code = default_config.code
        model_api_key = default_config.api_key
        model_api_url = default_config.api_url
        call_type = str(default_config.call_type) if default_config.call_type is not None else "OpenAI Chat"
        logger.info(f"使用用户的默认模型: {model_name} (code: {model_code})")
    
    logger.info(f"=== 开始生成调用代码 ===")
    logger.info(f"调用方式: {call_type}")
    logger.info(f"模型API URL: {model_api_url}")

    try:
        url = str(model_api_url) if model_api_url else "https://api.anthropic.com"

        messages = [
            {"role": "system", "content": CODE_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": CODE_GENERATION_USER_PROMPT.format(
                api_url=request.api_url,
                call_params_example=request.call_params_example
            )}
        ]

        result = await call_llm(
            messages=messages,
            model=model_code,
            api_key=model_api_key,
            url=url,
            call_type=call_type,
            structured_output=False,
            timeout=60.0,
            default_response={"content": ""}
        )

        generated_code = result.get("content", "")
        logger.info(f"生成的代码:\n{generated_code}")

        generated_code = str(generated_code) if generated_code else ""
        code_match = re.search(r'```python\s*(.*?)\s*```', generated_code, re.DOTALL)
        if code_match:
            generated_code = code_match.group(1)

        logger.info(f"=== 代码生成完成 ===")
        return {"code": generated_code.strip()}

    except Exception as e:
        logger.error(f"代码生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代码生成失败: {str(e)}")


@router.post("/test-call")
async def test_agent_call(
    request: TestCallRequest,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"=== 开始测试调用 ===")
    logger.info(f"测试消息: {request.message}")
    logger.info(f"响应类型: {request.response_type}")
    if request.response_extract_config:
        logger.info(f"响应提取配置: {request.response_extract_config}")
    if request.kwargs:
        logger.info(f"额外参数(kwargs): {json.dumps(request.kwargs, ensure_ascii=False)}")
    logger.info(f"调用代码:\n{request.call_code}")
    
    try:
        local_vars = {}
        exec(request.call_code, {"__builtins__": __builtins__, "httpx": httpx, "json": json}, local_vars)
        
        if "call_agent" not in local_vars:
            logger.error("代码中未找到 call_agent 函数")
            raise HTTPException(status_code=400, detail="代码中未找到 call_agent 函数")
        
        call_agent = local_vars["call_agent"]
        kwargs = request.kwargs or {}
        config = call_agent(request.api_key, message=request.message, **kwargs)
        
        if not isinstance(config, dict):
            raise HTTPException(status_code=400, detail="call_agent 函数必须返回字典")
        
        required_keys = ["url", "method", "headers"]
        for key in required_keys:
            if key not in config:
                raise HTTPException(status_code=400, detail=f"请求配置缺少必需的键: {key}")
        
        url = config["url"]
        method = config["method"].upper()
        headers = config["headers"]
        body = config.get("body", {})
        
        logger.info(f"=== HTTP请求 ===")
        logger.info(f"请求方法: {method}")
        logger.info(f"请求URL: {url}")
        logger.info(f"请求Headers:\n{json.dumps(headers, ensure_ascii=False, indent=2)}")
        logger.info(f"请求Body:\n{json.dumps(body, ensure_ascii=False, indent=2)}")
        
        if request.response_type == "stream":
            body["stream"] = True
            result_chunks = []
            content_parts = []
            
            client = http_client_manager.client
            async with client.stream(method, url, headers=headers, json=body) as response:
                logger.info(f"响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    return {"success": False, "error": f"API调用失败: {response.status_code} - {error_text.decode()}"}
                
                async for line in response.aiter_lines():
                    if line:
                        result_chunks.append(line)
                        if line.startswith("data: "):
                            data_content = line[6:]
                            if data_content != "[DONE]":
                                try:
                                    data = json.loads(data_content)
                                    logger.debug(f"SSE数据: {json.dumps(data, ensure_ascii=False)}")
                                    content = extract_content_from_stream_data(data)
                                    if content:
                                        content_parts.append(content)
                                except json.JSONDecodeError:
                                    pass
                        else:
                            try:
                                data = json.loads(line)
                                logger.debug(f"JSON数据: {json.dumps(data, ensure_ascii=False)}")
                                content = extract_content_from_stream_data(data)
                                if content:
                                    content_parts.append(content)
                            except json.JSONDecodeError:
                                pass
            
            raw_result = "\n".join(result_chunks)
            logger.info(f"流式响应长度: {len(raw_result)}")
            processed_result = "".join(content_parts) if content_parts else raw_result
        else:
            client = http_client_manager.client
            if method == "GET":
                response = await client.get(url, headers=headers)
            else:
                response = await client.post(url, headers=headers, json=body)
                
                logger.info(f"响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    return {"success": False, "error": f"API调用失败: {response.status_code} - {response.text}"}
                
                response_text = response.text
                logger.info(f"响应内容:\n{response_text[:2000]}")
                
                if response_text.strip().startswith("data: ") or "\ndata: " in response_text:
                    return {
                        "success": False, 
                        "error": "检测到SSE流式响应，但智能体配置为非流式模式。请在智能体设置中将响应格式改为「流式响应」。",
                        "is_stream_response": True
                    }
                
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    result = {"text": response_text}
                    logger.info("响应不是JSON格式，作为纯文本处理")
                
                response_type_detected = detect_response_type(result)
                processed_result = extract_content_with_config(result, request.response_extract_config)
        
        logger.info(f"=== 测试调用完成 ===")
        return {
            "success": True, 
            "result": processed_result,
            "raw_response": result if request.response_type != "stream" else None,
            "response_type_detected": response_type_detected if request.response_type != "stream" else None
        }
        
    except Exception as e:
        logger.error(f"测试调用失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


class GenerateExtractConfigRequest(BaseModel):
    response_data: dict


@router.post("/generate-extract-config")
async def generate_extract_config(
    request: GenerateExtractConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"=== 开始生成响应提取配置 ===")
    
    result = request.response_data
    
    if "choices" in result:
        choices = result.get("choices", [])
        if choices:
            choice = choices[0]
            if "message" in choice:
                return {"config": '{"type": "openai_chat"}', "type": "openai_chat"}
            elif "delta" in choice:
                return {"config": '{"type": "openai_chat"}', "type": "openai_chat"}
    
    if "output" in result:
        output = result.get("output", [])
        if isinstance(output, list):
            for item in output:
                if item.get("type") == "message":
                    return {"config": '{"type": "openai_responses"}', "type": "openai_responses"}
    
    if "content" in result:
        content = result.get("content", [])
        if content and isinstance(content, list):
            if content[0].get("type") == "text" or "text" in content[0]:
                return {"config": '{"type": "anthropic"}', "type": "anthropic"}
    
    if "text" in result and len(result) == 1:
        return {"config": '{"type": "text"}', "type": "text"}
    
    from app.services.functional_config import get_code_gen_config
    
    code_gen_model = get_code_gen_config(db)
    
    if not code_gen_model:
        default_config = db.query(ApiConfig).filter(
            ApiConfig.user_id == current_user.id,
            ApiConfig.is_default == True
        ).first()
        
        if not default_config:
            default_config = db.query(ApiConfig).filter(
                ApiConfig.user_id == current_user.id
            ).first()
    
    if not code_gen_model and not default_config:
        return {"config": None, "error": "无法识别响应格式，且未配置代码生成模型"}
    
    if code_gen_model:
        model_code = code_gen_model.get("model", "")
        model_api_key = code_gen_model.get("api_key", "")
        model_api_url = code_gen_model.get("url", "https://api.openai.com/v1")
        call_type = str(code_gen_model.get("call_type", "OpenAI Chat"))
    elif default_config:
        model_code = default_config.code
        model_api_key = default_config.api_key
        model_api_url = default_config.api_url
        call_type = str(default_config.call_type) if default_config.call_type is not None else "OpenAI Chat"
    else:
        return {"config": None, "error": "无法识别响应格式，且未配置代码生成模型"}

    try:
        url = str(model_api_url) if model_api_url else "https://api.anthropic.com"

        messages = [
            {"role": "system", "content": RESPONSE_CONFIG_SYSTEM_PROMPT},
            {"role": "user", "content": RESPONSE_CONFIG_USER_PROMPT.format(
                response_data=json.dumps(result, ensure_ascii=False, indent=2)
            )}
        ]

        model_result = await call_llm(
            messages=messages,
            model=model_code,
            api_key=model_api_key,
            url=url,
            call_type=call_type,
            structured_output=False,
            timeout=60.0,
            default_response={"content": ""}
        )

        config_text = model_result.get("content", "").strip()

        if config_text.startswith("```"):
            lines = config_text.split("\n")
            config_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            json.loads(config_text)
            return {"config": config_text, "type": "custom"}
        except json.JSONDecodeError:
            return {"config": None, "error": "模型返回的不是有效的JSON配置"}

    except Exception as e:
        logger.error(f"生成配置失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"config": None, "error": str(e)}


def create_logged_requests(log_list):
    import requests as original_requests
    
    class LoggedSession(original_requests.Session):
        def request(self, method, url, **kwargs):
            headers = dict(kwargs.get('headers', {}))
            body = kwargs.get('json', kwargs.get('data', kwargs.get('params', None)))
            
            log_entry = {
                'method': method.upper(),
                'url': url,
                'headers': headers,
                'body': None
            }
            
            if body is not None:
                if isinstance(body, dict):
                    log_entry['body'] = json.dumps(body, ensure_ascii=False, indent=2)
                else:
                    log_entry['body'] = str(body)
            
            log_list.append(log_entry)
            
            return super().request(method, url, **kwargs)
    
    class LoggedRequests:
        Session = LoggedSession
        
        @staticmethod
        def get(url, **kwargs):
            return original_requests.get(url, **kwargs)
        
        @staticmethod
        def post(url, **kwargs):
            headers = dict(kwargs.get('headers', {}))
            body = kwargs.get('json', kwargs.get('data', kwargs.get('params', None)))
            
            log_entry = {
                'method': 'POST',
                'url': url,
                'headers': headers,
                'body': None
            }
            
            if body is not None:
                if isinstance(body, dict):
                    log_entry['body'] = json.dumps(body, ensure_ascii=False, indent=2)
                else:
                    log_entry['body'] = str(body)
            
            log_list.append(log_entry)
            
            return original_requests.post(url, **kwargs)
        
        @staticmethod
        def put(url, **kwargs):
            return original_requests.put(url, **kwargs)
        
        @staticmethod
        def delete(url, **kwargs):
            return original_requests.delete(url, **kwargs)
        
        @staticmethod
        def patch(url, **kwargs):
            return original_requests.patch(url, **kwargs)
        
        @staticmethod
        def head(url, **kwargs):
            return original_requests.head(url, **kwargs)
        
        @staticmethod
        def options(url, **kwargs):
            return original_requests.options(url, **kwargs)
        
        @staticmethod
        def request(method, url, **kwargs):
            return original_requests.request(method, url, **kwargs)
    
    LoggedRequests.codes = original_requests.codes  # type: ignore
    LoggedRequests.exceptions = original_requests.exceptions  # type: ignore
    LoggedRequests.Response = original_requests.Response  # type: ignore
    
    return LoggedRequests


def create_logged_httpx(log_list):
    class LoggedClient(httpx.Client):
        def request(self, method, url, **kwargs):
            headers = dict(kwargs.get('headers', {}))
            body = kwargs.get('json', kwargs.get('data', kwargs.get('params', None)))
            
            log_entry = {
                'method': method.upper(),
                'url': str(url),
                'headers': headers,
                'body': None
            }
            
            if body is not None:
                if isinstance(body, dict):
                    log_entry['body'] = json.dumps(body, ensure_ascii=False, indent=2)
                else:
                    log_entry['body'] = str(body)
            
            log_list.append(log_entry)
            
            return super().request(method, url, **kwargs)
    
    class LoggedHttpx:
        Client = LoggedClient
        
        @staticmethod
        def get(url, **kwargs):
            with httpx.Client() as client:
                return client.get(url, **kwargs)
        
        @staticmethod
        def post(url, **kwargs):
            headers = dict(kwargs.get('headers', {}))
            body = kwargs.get('json', kwargs.get('data', kwargs.get('params', None)))
            
            log_entry = {
                'method': 'POST',
                'url': str(url),
                'headers': headers,
                'body': None
            }
            
            if body is not None:
                if isinstance(body, dict):
                    log_entry['body'] = json.dumps(body, ensure_ascii=False, indent=2)
                else:
                    log_entry['body'] = str(body)
            
            log_list.append(log_entry)
            
            with httpx.Client() as client:
                return client.post(url, **kwargs)
    
    LoggedHttpx.HTTPError = httpx.HTTPError  # type: ignore
    LoggedHttpx.RequestError = httpx.RequestError  # type: ignore
    LoggedHttpx.HTTPStatusError = httpx.HTTPStatusError  # type: ignore
    
    return LoggedHttpx
