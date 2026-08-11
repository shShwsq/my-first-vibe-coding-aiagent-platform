import json
import logging
import re
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.api_config import ApiConfig
from app.models.agent import Agent
from app.models.workflow_agent import WorkflowAgent
from app.models.workflow_memory import WorkflowMemory
from app.models.workflow_ui import WorkflowUI
from app.models.conversation import ChatMessage, Conversation
from app.models.code_tool import CodeTool
from app.auth import get_current_user
from app.schemas.chat import ChatRequest
from app.http_client import http_client_manager
from app.prompts import (
    UNIFIED_INTENT_SYSTEM_PROMPT,
    UNIFIED_INTENT_USER_PROMPT,
    INTENT_RECOGNITION_SYSTEM_PROMPT,
    INTENT_RECOGNITION_USER_PROMPT,
    GENERAL_CHAT_SYSTEM_PROMPT
)
from app.services.llm_client import (
    get_intent_model_config,
    call_llm,
    stream_llm
)
from app.services.workflow import WorkflowParser, WorkflowExecutor
from app.services.conversation_saver import stream_and_save, save_conversation_messages
from app.services.chat_helpers import get_chat_config, prepare_messages, create_stream_response
import httpx
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-agent-chat", tags=["统一智能体聊天"])


def format_agents_info(agents: List[dict], workflow_agents: List[dict]) -> str:
    lines = []
    
    if agents:
        lines.append("【普通智能体】")
        for agent in agents:
            name = agent.get('name', 'unknown')
            desc = agent.get('description', '')
            line = f"- {name}"
            if desc:
                line += f": {desc}"
            lines.append(line)
    
    if workflow_agents:
        lines.append("\n【工作流智能体】")
        for agent in workflow_agents:
            name = agent.get('name', 'unknown')
            desc = agent.get('description', '')
            line = f"- {name}"
            if desc:
                line += f": {desc}"
            lines.append(line)
    
    return "\n".join(lines) if lines else "暂无可用智能体"


def format_params_for_prompt(params: List[Dict[str, Any]]) -> str:
    if not params:
        return "无参数定义"
    
    SYSTEM_PARAMS = {"file_paths", "file_list"}
    
    lines = []
    for param in params:
        name = param.get('name', 'unknown')
        
        if name in SYSTEM_PARAMS:
            continue
        
        default = param.get('default', '')
        param_type = param.get('type', 'string')
        desc = param.get('description', '')
        
        line = f"- {name}: {param_type}"
        if default:
            line += f" (默认值: {default})"
        if desc:
            line += f" - {desc}"
        lines.append(line)
    
    return "\n".join(lines) if lines else "无参数定义"


WORKFLOW_INTENT_USER_PROMPT = """请分析以下对话上下文和用户消息，判断是否需要调用工作流智能体，并根据参数定义提取参数：

{conversation_context}

当前用户消息：{message}

用户上传的文件：{file_list}

智能体名称：{agent_name}

智能体描述：{agent_description}

参数定义：
{params_definition}

请根据参数定义分析需要提取哪些参数，并从用户消息中提取这些参数的值。
如果参数有默认值且用户没有明确指定，可以使用默认值。
请输出JSON格式的判断结果。禁止输出任何解释或说明。
"""


def get_request_config(agent: Agent, query: str, params: Optional[dict] = None) -> dict:
    logger.info(f"Getting request config for agent: {agent.name}")
    
    try:
        local_vars = {}
        call_code_str = str(agent.call_code) if agent.call_code is not None else ""
        exec(call_code_str, {"__builtins__": __builtins__, "httpx": httpx, "json": json}, local_vars)
        
        if "call_agent" not in local_vars:
            raise ValueError(f"智能体 {agent.name} 的调用代码无效")
        
        call_agent_func = local_vars["call_agent"]
        
        call_kwargs = {"message": query}
        if params:
            call_kwargs.update(params)
        
        config = call_agent_func(agent.api_key, **call_kwargs)
        
        if not isinstance(config, dict):
            raise ValueError("call_agent 函数必须返回字典")
        
        required_keys = ["url", "method", "headers"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"请求配置缺少必需的键: {key}")
        
        return config
    except Exception as e:
        logger.error(f"Get request config failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def call_agent(
    agent: Agent,
    query: str,
    params: Optional[dict] = None
) -> str:
    logger.info(f"Calling agent (non-stream): {agent.name}")
    
    if params:
        logger.info(f"Extracted params: {json.dumps(params, ensure_ascii=False)}")
    
    try:
        config = get_request_config(agent, query, params)
        
        url = config["url"]
        method = config["method"].upper()
        headers = config["headers"]
        body = config.get("body", {})
        
        logger.info(f"=== 智能体请求 ===")
        logger.info(f"Request URL: {url}")
        logger.info(f"Request Method: {method}")
        
        client = http_client_manager.client
        if method == "GET":
            response = await client.get(url, headers=headers)
        else:
            response = await client.post(url, headers=headers, json=body)
        
        if response.status_code != 200:
            return f"API调用失败: {response.status_code} - {response.text}"
        
        response_text = response.text
        
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"text": response_text}
        
        from app.services.llm_client import extract_content_with_config
        if isinstance(result, dict):
            config_str = str(agent.response_extract_config) if agent.response_extract_config is not None else None
            return extract_content_with_config(result, config_str)
        return str(result)
            
    except Exception as e:
        logger.error(f"Agent call failed: {str(e)}")
        return f"调用智能体 {agent.name} 失败: {str(e)}"


async def stream_agent_call(
    agent: Agent,
    query: str,
    params: Optional[dict] = None
) -> AsyncGenerator[str, None]:
    logger.info(f"Calling agent (stream): {agent.name}")
    
    if params:
        logger.info(f"Extracted params: {json.dumps(params, ensure_ascii=False)}")
    
    from app.services.llm_client import extract_content_with_config, extract_content_from_stream_data
    
    extract_config = str(agent.response_extract_config) if agent.response_extract_config is not None else None
    
    try:
        config = get_request_config(agent, query, params)
        
        url = config["url"]
        method = config["method"].upper()
        headers = config["headers"]
        body = config.get("body", {})
        
        client = http_client_manager.client
        async with client.stream(method, url, headers=headers, json=body) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield f"API调用失败: {response.status_code} - {error_text.decode()}"
                    return
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        data_content = line[6:]
                        if data_content == "[DONE]":
                            continue
                        
                        try:
                            data = json.loads(data_content)
                            if extract_config:
                                content = extract_content_with_config(data, extract_config)
                            else:
                                content = extract_content_from_stream_data(data)
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            if data_content and not data_content.startswith('{'):
                                yield data_content
                    else:
                        try:
                            data = json.loads(line)
                            if extract_config:
                                content = extract_content_with_config(data, extract_config)
                            else:
                                content = extract_content_from_stream_data(data)
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            pass
                            
    except Exception as e:
        logger.error(f"Agent stream call failed: {str(e)}")
        yield f"调用智能体 {agent.name} 失败: {str(e)}"


async def execute_workflow_agent(
    agent: WorkflowAgent,
    query: str,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
    params: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[int] = None,
    verbose_queue: Optional[asyncio.Queue] = None,
    workflow_code_override: Optional[str] = None
) -> tuple:
    logger.info(f"Executing workflow agent: {agent.name}")
    if params:
        logger.info(f"Workflow params: {json.dumps(params, ensure_ascii=False)}")
    
    workflow_code = workflow_code_override if workflow_code_override is not None else (str(agent.workflow_code) if agent.workflow_code else "")
    
    if not workflow_code:
        return "工作流智能体未配置工作流代码", None, []
    
    try:
        parser = WorkflowParser()
        nodes = parser.parse(workflow_code)
        
        executor = WorkflowExecutor(
            db=None, 
            user_id=user_id,
            agent_id=agent.id
        )
        
        from app.database import SessionLocal
        memory_db = SessionLocal()
        try:
            executor.db = memory_db
            executor.load_memory(conversation_id)
            if conversation_id:
                logger.info(f"Loaded conversation memory for conversation_id: {conversation_id}")
            logger.info(f"Conversation history: {executor.memory}")
        finally:
            executor.db = None
            memory_db.close()
        
        if verbose_queue:
            executor.set_verbose_queue(verbose_queue)
        
        execute_kwargs = {"input_data": query}
        if params:
            execute_kwargs.update(params)
        
        result = await executor.execute(nodes, **execute_kwargs)
        
        if executor.has_stream_node():
            return result, executor.get_stream_generator(), executor
        
        return str(result) if result else "工作流执行完成，但未返回结果", None, executor
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"工作流执行失败: {str(e)}", None, None


async def run_workflow_agent_stream(
    agent: WorkflowAgent,
    query: str,
    user_id: int,
    params: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    include_header: bool = True,
    workflow_code_override: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    运行工作流智能体并生成流式输出，不保存到数据库
    
    Args:
        agent: 工作流智能体
        query: 用户查询
        user_id: 用户ID
        params: 工作流参数
        conversation_id: 会话ID（用于加载记忆）
        context: 可选的上下文字典，用于存储执行结果
            - 执行完成后会填充: full_content, executor, ui_config, saved_files
        include_header: 是否包含头部消息
        workflow_code_override: 可选的工作流代码覆盖（用于测试未保存的代码）
    
    Yields:
        Dict[str, Any]: 包含 content, type 等字段的输出字典
    """
    if context is None:
        context = {}
    
    context["full_content"] = ""
    context["executor"] = None
    context["ui_config"] = None
    context["saved_files"] = None
    context["result"] = None
    
    if include_header:
        header_msg = f"[调用工作流智能体: {agent.name}]\n\n"
        context["full_content"] = header_msg
        yield {"content": header_msg, "type": "header", "agent_name": agent.name}
    
    verbose_queue = asyncio.Queue()
    execution_result = {"result": None, "stream_generator": None, "executor": None, "done": False}
    
    async def run_workflow():
        try:
            result, stream_generator, executor = await execute_workflow_agent(
                agent, query, None, user_id, params, conversation_id, verbose_queue, workflow_code_override
            )
            execution_result["result"] = result
            execution_result["stream_generator"] = stream_generator
            execution_result["executor"] = executor
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            execution_result["result"] = f"工作流执行失败: {str(e)}"
        finally:
            execution_result["done"] = True
            await verbose_queue.put(None)
    
    workflow_task = asyncio.create_task(run_workflow())
    
    while True:
        try:
            verbose_item = await asyncio.wait_for(verbose_queue.get(), timeout=0.1)
            if verbose_item is None:
                break
            
            if isinstance(verbose_item, dict):
                content = verbose_item.get("content")
                node_name = verbose_item.get("node_name", "")
                item_type = verbose_item.get("type", "verbose")
                
                if content is None:
                    content = ""
                
                if item_type == "stream_chunk":
                    context["full_content"] += str(content)
                    yield {"content": str(content), "type": "stream_chunk"}
                else:
                    if node_name:
                        verbose_msg = f"[{node_name}] {content}"
                    else:
                        verbose_msg = str(content)
                    context["full_content"] += verbose_msg
                    yield {"content": verbose_msg, "type": "verbose", "node_name": node_name}
            else:
                context["full_content"] += str(verbose_item)
                yield {"content": str(verbose_item), "type": "verbose"}
        except asyncio.TimeoutError:
            if execution_result["done"]:
                break
            continue
    
    await workflow_task
    
    if execution_result["stream_generator"]:
        stream_gen = execution_result["stream_generator"]
        try:
            async for chunk in stream_gen:
                if chunk:
                    if chunk.startswith("data: "):
                        data_str = chunk[6:]
                        if data_str.strip() and data_str.strip() != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                if isinstance(data.get("content"), str):
                                    context["full_content"] += data["content"]
                                yield {"content": data.get("content", ""), "type": "stream_chunk", "raw": data}
                            except json.JSONDecodeError:
                                pass
                    else:
                        try:
                            data = json.loads(chunk)
                            if isinstance(data.get("content"), str):
                                context["full_content"] += data["content"]
                            yield {"content": data.get("content", ""), "type": "stream_chunk", "raw": data}
                        except json.JSONDecodeError:
                            if chunk and not chunk.startswith('{'):
                                context["full_content"] += chunk
                                yield {"content": chunk, "type": "stream_chunk"}
        finally:
            await stream_gen.aclose()
    else:
        result = execution_result["result"]
        if result:
            if isinstance(result, dict) and result.get("type") == "ui":
                pass
            else:
                context["full_content"] += str(result)
                yield {"content": str(result), "type": "result"}
    
    context["executor"] = execution_result["executor"]
    context["result"] = execution_result["result"]
    
    if execution_result["executor"]:
        context["ui_config"] = execution_result["executor"].get_ui_config()
        context["saved_files"] = execution_result["executor"].get_saved_files()
        
        logger.info(f"Workflow executor UI config: {context['ui_config']}")
        logger.info(f"Workflow executor node_outputs: {execution_result['executor'].ctx.node_outputs}")
        logger.info(f"Workflow executor ui_elements: {execution_result['executor'].ctx.get_ui_elements()}")
        
        if context["ui_config"]:
            logger.info(f"Yielding UI config to frontend: {context['ui_config']}")
            yield {"type": "ui_config", "ui_config": context["ui_config"]}
        else:
            logger.warning("No UI config found from executor")
    
    yield {"type": "done"}


@router.post("/stream")
async def unified_agent_chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    config = get_chat_config(db, request.config_id, current_user.id)
    
    messages, last_message = prepare_messages(request.messages)
    
    conversation_context = ""
    if len(messages) > 1:
        context_parts = []
        for msg in messages[:-1]:
            role = "用户" if msg["role"] == "user" else "助手"
            context_parts.append(f"{role}: {msg['content']}")
        conversation_context = "对话历史：\n" + "\n".join(context_parts)
    else:
        conversation_context = "（无历史对话）"
    
    agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
    workflow_agents = db.query(WorkflowAgent).filter(WorkflowAgent.user_id == current_user.id).all()
    
    agents_list = [{"name": a.name, "description": a.description} for a in agents]
    workflow_agents_list = [{"name": a.name, "description": a.description} for a in workflow_agents]
    agents_info = format_agents_info(agents_list, workflow_agents_list)
    
    intent_model_config = get_intent_model_config(db)
    if intent_model_config:
        intent_model = intent_model_config["model"]
        intent_api_key = intent_model_config["api_key"]
        intent_url = intent_model_config["url"]
        intent_call_type = intent_model_config.get("call_type", "OpenAI Chat")
    else:
        intent_model = config.model_code
        intent_api_key = config.api_key
        intent_url = config.url
        intent_call_type = config.call_type
    
    intent_messages = [
        {"role": "system", "content": UNIFIED_INTENT_SYSTEM_PROMPT},
        {"role": "user", "content": UNIFIED_INTENT_USER_PROMPT.format(
            conversation_context=conversation_context,
            message=last_message,
            agents_info=agents_info
        )}
    ]
    
    try:
        intent_result = await call_llm(
            messages=intent_messages,
            model=intent_model,
            api_key=intent_api_key,
            url=intent_url,
            call_type=intent_call_type,
            structured_output=True,
            timeout=30.0,
            default_response={"need_agent": False, "reason": "意图识别失败"}
        )
    except Exception as e:
        logger.error(f"Intent recognition failed: {str(e)}")
        intent_result = {"need_agent": False, "reason": "意图识别失败"}
    
    logger.info(f"Unified intent result: {intent_result}")
    
    if not intent_result.get("need_agent"):
        chat_messages = [
            {"role": "system", "content": GENERAL_CHAT_SYSTEM_PROMPT}
        ] + messages
        
        stream_gen = stream_llm(
            messages=chat_messages,
            model=config.model_code,
            api_key=config.api_key,
            url=config.url,
            call_type=config.call_type,
            enable_thinking=request.enable_thinking,
            timeout=60.0,
            enable_search=request.enable_search
        )
        
        return create_stream_response(
            stream_gen=stream_gen,
            db=db,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            user_message=last_message,
            api_id=request.config_id,
            conversation_mode="agent"
        )
    
    agent_name = intent_result.get("agent_name", "")
    agent_type = intent_result.get("agent_type", "agent")
    query = intent_result.get("query", last_message)
    
    if agent_type == "workflow_agent":
        agent = db.query(WorkflowAgent).filter(
            WorkflowAgent.user_id == current_user.id,
            WorkflowAgent.name == agent_name
        ).first()
        
        if not agent:
            all_names = [a.name for a in agents] + [a.name for a in workflow_agents]
            for name in all_names:
                if name.replace(" ", "") == agent_name.replace(" ", ""):
                    agent = db.query(WorkflowAgent).filter(
                        WorkflowAgent.user_id == current_user.id,
                        WorkflowAgent.name == name
                    ).first()
                    break
        
        if not agent:
            async def workflow_agent_error_stream():
                all_names = [a.name for a in agents] + [a.name for a in workflow_agents]
                msg = f'未找到名为 "{agent_name}" 的工作流智能体。可用的智能体：{", ".join(all_names)}'
                yield f"data: {json.dumps({'content': msg})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(workflow_agent_error_stream(), media_type="text/event-stream")
        
        params_definition = ""
        if agent.workflow_code:
            valid, message, params = WorkflowParser().validate(agent.workflow_code)
            if valid:
                params_definition = format_params_for_prompt(params)
        
        agent_description = str(agent.description) if agent.description else ""
        
        file_list = [fi.name for fi in request.file_items] if request.file_items else []
        
        param_intent_messages = [
            {"role": "system", "content": INTENT_RECOGNITION_SYSTEM_PROMPT},
            {"role": "user", "content": WORKFLOW_INTENT_USER_PROMPT.format(
                conversation_context=conversation_context,
                message=last_message,
                file_list=", ".join(file_list) if file_list else "无",
                agent_name=agent_name,
                agent_description=agent_description,
                params_definition=params_definition
            )}
        ]
        
        try:
            param_result = await call_llm(
                messages=param_intent_messages,
                model=intent_model,
                api_key=intent_api_key,
                url=intent_url,
                call_type=intent_call_type,
                structured_output=True,
                timeout=30.0,
                default_response={"need_agent": True, "agent_name": agent_name, "query": query, "params": {}}
            )
        except Exception as e:
            logger.error(f"Param extraction failed: {str(e)}")
            param_result = {"need_agent": True, "agent_name": agent_name, "query": query, "params": {}}
        
        extracted_params = param_result.get("params", {})
        query = param_result.get("query", query)
        
        if request.file_paths and len(request.file_paths) > 0:
            extracted_params["file_paths"] = request.file_paths
        if file_list and len(file_list) > 0:
            extracted_params["file_list"] = file_list
        async def workflow_response_stream():
            from app.models.workflow_file import WorkflowFile
            from app.database import SessionLocal
            
            context = {}
            
            async for item in run_workflow_agent_stream(
                agent, query, current_user.id, extracted_params, 
                request.conversation_id, context, include_header=True
            ):
                item_type = item.get("type", "")
                content = item.get("content", "")
                
                if item_type == "done":
                    break
                elif item_type == "ui_config":
                    yield f"data: {json.dumps({'type': 'ui_config', 'ui_config': item.get('ui_config')})}\n\n"
                elif content:
                    yield f"data: {json.dumps({'content': content, 'type': item_type})}\n\n"
            
            if context.get("executor"):
                save_db = SessionLocal()
                try:
                    conversation_id = request.conversation_id
                    
                    if not conversation_id:
                        new_conversation = Conversation(
                            user_id=current_user.id,
                            title=query[:50] if len(query) > 50 else query,
                            conversation_mode="agent",
                            api_id=request.config_id
                        )
                        save_db.add(new_conversation)
                        save_db.flush()
                        conversation_id = new_conversation.id
                    
                    user_message = ChatMessage(
                        conversation_id=conversation_id,
                        role="user",
                        content=last_message
                    )
                    save_db.add(user_message)
                    save_db.flush()
                    
                    assistant_message = ChatMessage(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=context.get("full_content", "")
                    )
                    save_db.add(assistant_message)
                    save_db.flush()
                    
                    memory_data = context["executor"].get_memory_data()
                    save_db.query(WorkflowMemory).filter(
                        WorkflowMemory.conversation_id == conversation_id
                    ).delete()
                    
                    if "history" in memory_data:
                        history_value = json.dumps(memory_data["history"], ensure_ascii=False)
                        history_record = WorkflowMemory(
                            conversation_id=conversation_id,
                            key="history",
                            value=history_value,
                            is_editable=False
                        )
                        save_db.add(history_record)
                    
                    if "variables" in memory_data:
                        for key, var_data in memory_data["variables"].items():
                            value = var_data.get("value")
                            is_editable = var_data.get("is_editable", False)
                            value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                            var_record = WorkflowMemory(
                                conversation_id=conversation_id,
                                key=key,
                                value=value_str,
                                is_editable=is_editable
                            )
                            save_db.add(var_record)
                    
                    ui_config = context.get("ui_config")
                    if ui_config:
                        workflow_ui = WorkflowUI(
                            conversation_id=conversation_id,
                            message_id=assistant_message.id,
                            ui_config=ui_config
                        )
                        save_db.add(workflow_ui)
                    
                    saved_files = context.get("saved_files")
                    if saved_files:
                        for file_info in saved_files:
                            workflow_file = WorkflowFile(
                                conversation_id=conversation_id,
                                message_id=assistant_message.id,
                                file_path=file_info.get("file_path"),
                                file_type=file_info.get("file_type")
                            )
                            save_db.add(workflow_file)
                    
                    long_memory_data = context["executor"].memory.get_long_memory_data()
                    if long_memory_data:
                        logger.info(f"Saving long memory for user {current_user.id}, agent {agent.id}, conversation {conversation_id}")
                        logger.info(f"Long memory keys: {list(long_memory_data.keys())}")
                        
                        from app.models.workflow_long_memory import WorkflowLongMemory
                        saved_count = 0
                        updated_count = 0
                        
                        for key, value in long_memory_data.items():
                            logger.info(f"Processing long memory key: {key}, value type: {type(value).__name__}, value: {value}")
                            
                            existing = save_db.query(WorkflowLongMemory).filter(
                                WorkflowLongMemory.user_id == current_user.id,
                                WorkflowLongMemory.agent_id == agent.id,
                                WorkflowLongMemory.key == key
                            ).first()
                            
                            value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
                            logger.info(f"Converted value_str for key {key}: {value_str}")
                            
                            if existing:
                                logger.info(f"Found existing record for key {key}, old value: {existing.value}")
                                existing.value = value_str
                                updated_count += 1
                                logger.info(f"Updated long memory key: {key}, new value: {existing.value}")
                            else:
                                long_memory_record = WorkflowLongMemory(
                                    user_id=current_user.id,
                                    agent_id=agent.id,
                                    key=key,
                                    value=value_str
                                )
                                save_db.add(long_memory_record)
                                saved_count += 1
                                logger.info(f"Created new long memory key: {key}")
                        
                        logger.info(f"Long memory save completed: {saved_count} created, {updated_count} updated")
                    else:
                        logger.info(f"No long memory data to save for conversation {conversation_id}")
                    
                    save_db.commit()
                    
                    yield f"data: {json.dumps({'type': 'saved', 'conversation_id': conversation_id, 'message_id': assistant_message.id})}\n\n"
                finally:
                    save_db.close()
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(workflow_response_stream(), media_type="text/event-stream")
    
    else:
        agent = db.query(Agent).filter(
            Agent.user_id == current_user.id,
            Agent.name == agent_name
        ).first()
        
        if not agent:
            all_names = [a.name for a in agents] + [a.name for a in workflow_agents]
            for name in all_names:
                if name.replace(" ", "") == agent_name.replace(" ", ""):
                    agent = db.query(Agent).filter(
                        Agent.user_id == current_user.id,
                        Agent.name == name
                    ).first()
                    break
        
        if not agent:
            async def agent_error_stream():
                all_names = [a.name for a in agents] + [a.name for a in workflow_agents]
                msg = f'未找到名为 "{agent_name}" 的智能体。可用的智能体：{", ".join(all_names)}'
                yield f"data: {json.dumps({'content': msg})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(agent_error_stream(), media_type="text/event-stream")
        
        call_code_for_intent = str(agent.call_code) if agent.call_code is not None else ""
        
        param_intent_messages = [
            {"role": "system", "content": INTENT_RECOGNITION_SYSTEM_PROMPT},
            {"role": "user", "content": INTENT_RECOGNITION_USER_PROMPT.format(
                conversation_context=conversation_context,
                message=last_message,
                agent_name=agent_name,
                call_code=call_code_for_intent
            )}
        ]
        
        try:
            param_result = await call_llm(
                messages=param_intent_messages,
                model=intent_model,
                api_key=intent_api_key,
                url=intent_url,
                call_type=intent_call_type,
                structured_output=True,
                timeout=30.0,
                default_response={"need_agent": True, "agent_name": agent_name, "query": query, "params": {}}
            )
        except Exception as e:
            logger.error(f"Param extraction failed: {str(e)}")
            param_result = {"need_agent": True, "agent_name": agent_name, "query": query, "params": {}}
        
        extracted_params = param_result.get("params", {})
        query = param_result.get("query", query)
        
        if request.file_paths and len(request.file_paths) > 0:
            extracted_params["file_paths"] = request.file_paths
        
        async def agent_response_stream():
            header_msg = f"[调用智能体: {agent.name}]\n\n"
            yield f"data: {json.dumps({'content': header_msg})}\n\n"
            
            full_content = header_msg
            response_type = str(agent.response_type) if agent.response_type is not None else "non_stream"
            
            if response_type == "stream":
                async for content in stream_agent_call(agent, query, extracted_params):
                    full_content += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            else:
                result = await call_agent(agent, query, extracted_params)
                full_content += result
                yield f"data: {json.dumps({'content': result})}\n\n"
            
            conversation_id = request.conversation_id
            
            if not conversation_id:
                new_conversation = Conversation(
                    user_id=current_user.id,
                    title=query[:50] if len(query) > 50 else query,
                    conversation_mode="agent",
                    api_id=request.config_id
                )
                db.add(new_conversation)
                db.flush()
                conversation_id = new_conversation.id
            
            user_message = ChatMessage(
                conversation_id=conversation_id,
                role="user",
                content=last_message
            )
            db.add(user_message)
            db.flush()
            
            assistant_message = ChatMessage(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content
            )
            db.add(assistant_message)
            db.flush()
            
            db.commit()
            
            yield f"data: {json.dumps({'type': 'saved', 'conversation_id': conversation_id, 'message_id': assistant_message.id})}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(agent_response_stream(), media_type="text/event-stream")


@router.get("/agents")
def get_all_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
    workflow_agents = db.query(WorkflowAgent).filter(WorkflowAgent.user_id == current_user.id).all()
    
    result = []
    for a in agents:
        result.append({"id": a.id, "name": a.name, "description": a.description, "type": "agent"})
    for a in workflow_agents:
        result.append({"id": a.id, "name": a.name, "description": a.description, "type": "workflow_agent"})
    
    return result


class SaveMemoryRequest(BaseModel):
    conversation_id: int
    memory: Dict[str, Any]
    message_id: Optional[int] = None
    ui_config: Optional[Dict[str, Any]] = None
    saved_files: Optional[List[Dict[str, Any]]] = None


@router.post("/save-memory")
def save_workflow_memory(
    request: SaveMemoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.workflow_file import WorkflowFile
    
    db.query(WorkflowMemory).filter(
        WorkflowMemory.conversation_id == request.conversation_id
    ).delete()
    
    memory = request.memory
    
    if "history" in memory:
        history_value = json.dumps(memory["history"], ensure_ascii=False)
        history_record = WorkflowMemory(
            conversation_id=request.conversation_id,
            key="history",
            value=history_value,
            is_editable=False
        )
        db.add(history_record)
    
    if "variables" in memory:
        for key, var_data in memory["variables"].items():
            value = var_data.get("value")
            is_editable = var_data.get("is_editable", False)
            value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
            var_record = WorkflowMemory(
                conversation_id=request.conversation_id,
                key=key,
                value=value_str,
                is_editable=is_editable
            )
            db.add(var_record)
    
    if request.message_id and request.ui_config:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        message = db.query(ChatMessage).filter(
            ChatMessage.id == request.message_id,
            ChatMessage.conversation_id == request.conversation_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        workflow_ui = WorkflowUI(
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            ui_config=request.ui_config
        )
        db.add(workflow_ui)
        logger.info(f"Saved workflow UI for message {request.message_id}")
    
    if request.saved_files and request.message_id:
        for file_info in request.saved_files:
            workflow_file = WorkflowFile(
                conversation_id=request.conversation_id,
                message_id=request.message_id,
                file_path=file_info.get("file_path"),
                file_type=file_info.get("file_type")
            )
            db.add(workflow_file)
        logger.info(f"Saved {len(request.saved_files)} workflow files for message {request.message_id}")
    
    db.commit()
    logger.info(f"Saved memory for conversation {request.conversation_id}")
    
    return {"success": True, "message": "Memory saved successfully"}


@router.get("/workflow-ui/{message_id}")
def get_workflow_ui(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定消息的工作流UI配置
    """
    workflow_ui = db.query(WorkflowUI).join(ChatMessage).join(Conversation).filter(
        WorkflowUI.message_id == message_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not workflow_ui:
        return {"success": False, "ui_config": None}
    
    return {
        "success": True,
        "ui_config": workflow_ui.ui_config
    }


@router.get("/workflow-ui/conversation/{conversation_id}")
def get_conversation_workflow_uis(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定对话的所有工作流UI配置
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    workflow_uis = db.query(WorkflowUI).filter(
        WorkflowUI.conversation_id == conversation_id
    ).order_by(WorkflowUI.created_at).all()
    
    result = []
    for ui in workflow_uis:
        result.append({
            "id": ui.id,
            "message_id": ui.message_id,
            "ui_config": ui.ui_config,
            "created_at": ui.created_at.isoformat() if ui.created_at else None
        })
    
    return {
        "success": True,
        "workflow_uis": result
    }


@router.get("/agents/search")
def search_agents_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    agents = db.query(Agent).filter(
        Agent.user_id == current_user.id,
        Agent.name.ilike(f"%{name}%")
    ).all()
    
    workflow_agents = db.query(WorkflowAgent).filter(
        WorkflowAgent.user_id == current_user.id,
        WorkflowAgent.name.ilike(f"%{name}%")
    ).all()
    
    result = {
        "agents": [{"id": a.id, "name": a.name, "type": "agent"} for a in agents],
        "workflow_agents": [{"id": a.id, "name": a.name, "type": "workflow_agent"} for a in workflow_agents]
    }
    
    return result


@router.get("/code-tools/search")
def search_code_tools_by_name(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import or_
    
    tools = db.query(CodeTool).filter(
        CodeTool.user_id == current_user.id,
        or_(
            CodeTool.name.ilike(f"%{name}%"),
            CodeTool.display_name.ilike(f"%{name}%")
        )
    ).all()
    
    result = [{
        "name": t.name, 
        "display_name": t.display_name,
        "parameters": t.parameters or [],
        "description": t.description
    } for t in tools]
    
    return result
