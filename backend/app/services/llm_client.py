import json
import logging
import re
from typing import Optional, AsyncGenerator, Union, Any
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.http_client import http_client_manager

logger = logging.getLogger(__name__)


def build_api_url(base_url: str, api_type: str) -> str:
    """
    构建LLM API的完整URL
    
    Args:
        base_url: 基础URL，如 "https://api.openai.com/v1" 或 "https://api.anthropic.com"
        api_type: API类型，支持以下值：
            - "openai_chat": OpenAI Chat Completions API
            - "openai_responses": OpenAI Responses API
            - "anthropic": Anthropic Messages API
    
    Returns:
        完整的API URL
    
    Examples:
        >>> build_api_url("https://api.openai.com/v1", "openai_chat")
        'https://api.openai.com/v1/chat/completions'
        
        >>> build_api_url("https://api.openai.com", "openai_chat")
        'https://api.openai.com/v1/chat/completions'
        
        >>> build_api_url("https://custom-api.com/v1", "openai_chat")
        'https://custom-api.com/v1/chat/completions'
        
        >>> build_api_url("https://custom-api.com", "openai_chat")
        'https://custom-api.com/v1/chat/completions'
    """
    api_endpoints = {
        "openai_chat": "/chat/completions",
        "openai_responses": "/responses",
        "anthropic": "/v1/messages",
    }
    
    if api_type not in api_endpoints:
        raise ValueError(f"不支持的API类型: {api_type}。支持的类型: {list(api_endpoints.keys())}")
    
    endpoint = api_endpoints[api_type]
    
    if base_url.endswith("/v1"):
        return f"{base_url}{endpoint}"
    elif base_url.endswith(".com"):
        return f"{base_url}/v1{endpoint}"
    else:
        return f"{base_url}"


def get_intent_model_config(db: Session) -> Optional[dict]:
    from app.services.functional_config import get_functional_config_dict
    return get_functional_config_dict(db, "intent_recognition")


async def stream_llm(
    messages: list,
    model: str,
    api_key: str,
    url: str,
    call_type: str,
    enable_thinking: Optional[bool] = False,
    timeout: float = 60.0,
    **kwargs
) -> AsyncGenerator[str, None]:
    enable_search = kwargs.pop("enable_search", False)
    if enable_search:
        if call_type == "OpenAI Responses":
            kwargs.setdefault("tools", []).append({"type": "web_search"})
        else:
            kwargs["enable_search"] = True
    
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    if call_type == "OpenAI Responses":
        async for chunk in stream_openai_responses(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            enable_thinking=enable_thinking or False,
            timeout=timeout,
            **kwargs
        ):
            yield chunk
    elif call_type == "Anthropic":
        async for chunk in stream_anthropic_chat(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            timeout=timeout,
            **kwargs
        ):
            yield chunk
    else:
        async for chunk in stream_openai_chat(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            enable_thinking=enable_thinking or False,
            timeout=timeout,
            **kwargs
        ):
            yield chunk


async def call_llm(
    messages: list,
    model: str,
    api_key: str,
    url: str,
    call_type: str,
    structured_output: bool = False,
    timeout: float = 60.0,
    default_response: Optional[dict] = None,
    **kwargs
) -> dict:
    enable_search = kwargs.pop("enable_search", None)
    if enable_search:
        if call_type == "OpenAI Responses":
            kwargs.setdefault("tools", []).append({"type": "web_search"})
        else:
            kwargs["enable_search"] = True
    
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    if call_type == "OpenAI Responses":
        result = await call_openai_responses(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            timeout=timeout,
            **kwargs
        )
    elif call_type == "Anthropic":
        result = await call_anthropic(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            timeout=timeout,
            **kwargs
        )
    else:
        result = await call_openai_chat(
            messages=messages,
            model=model,
            api_key=api_key,
            url=url,
            timeout=timeout,
            **kwargs
        )
    
    if "error" in result:
        if structured_output and default_response is not None:
            return default_response
        raise HTTPException(status_code=500, detail=result["error"])
    
    content = result.get("content", "")
    
    if structured_output:
        try:
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON directly: {content}, error: {e}")
            json_match = re.search(r'\{[\s\S]*?\}', content)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return parsed
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse extracted JSON: {json_match.group()}, error: {e2}")
            if default_response is not None:
                return default_response
            return {"error": "无法解析JSON", "raw_content": content}
    
    return {"content": content}


async def stream_openai_chat(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.openai.com/v1",
    enable_thinking: bool = False,
    timeout: float = 60.0,
    **kwargs
) -> AsyncGenerator[str, None]:
    api_url = build_api_url(url, "openai_chat")
    
    body = {
        "model": model,
        "messages": messages,
        "stream": True,
        "enable_thinking": enable_thinking,
        **kwargs
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    body = {k: v for k, v in body.items() if not (isinstance(v, list) and len(v) == 0)}
    logger.info("=" * 60)
    logger.info("OpenAI Chat API Request:")
    logger.info(f"URL: {api_url}")
    logger.info(f"Body: {json.dumps(body, indent=2, ensure_ascii=False)}")
    logger.info("=" * 60)
    
    client = http_client_manager.client
    async with client.stream(
        "POST",
        api_url,
        headers=headers,
        json=body,
        timeout=timeout
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    if chunk.get("choices"):
                        delta = chunk["choices"][0]["delta"]
                        if delta.get("reasoning_content"):
                            reasoning = delta["reasoning_content"]
                            yield f"data: {json.dumps({'reasoning': reasoning})}\n\n"
                        if delta.get("content"):
                            content = delta["content"]
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    elif chunk.get("error"):
                        logger.error(f"LLM API error: {chunk.get('error')}")
                        yield f"data: {json.dumps({'error': str(chunk.get('error'))})}\n\n"
                        break
                except json.JSONDecodeError:
                    continue
    
    yield "data: [DONE]\n\n"


async def stream_openai_responses(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.openai.com/v1",
    enable_thinking: bool = False,
    timeout: float = 60.0,
    **kwargs
) -> AsyncGenerator[str, None]:
    api_url = build_api_url(url, "openai_responses")
    body = {
        "model": model,
        "input": messages,
        "stream": True,
        "enable_thinking": enable_thinking,
        **kwargs
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    body = {k: v for k, v in body.items() if not (isinstance(v, list) and len(v) == 0)}
    logger.info("=" * 60)
    logger.info("OpenAI Responses API Request:")
    logger.info(f"URL: {api_url}")
    logger.info(f"Body: {json.dumps(body, indent=2, ensure_ascii=False)}")
    logger.info("=" * 60)
    
    client = http_client_manager.client
    async with client.stream(
        "POST",
        api_url,
        headers=headers,
        json=body,
        timeout=timeout
    ) as response:
        byte_buffer = b""
        text_buffer = ""
        async for chunk_bytes in response.aiter_bytes():
            byte_buffer += chunk_bytes
            try:
                decoded = byte_buffer.decode("utf-8")
                byte_buffer = b""
                text_buffer += decoded
            except UnicodeDecodeError:
                continue
            
            while "\n\n" in text_buffer:
                line, text_buffer = text_buffer.split("\n\n", 1)
                
                for part in line.split("\n"):
                    if part.startswith("data:"):
                        data = part[5:].strip()
                        if data == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(data)
                            event_type = chunk.get("type", "")
                            
                            if event_type == "response.output_text.delta":
                                content = chunk.get("delta", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            elif event_type == "response.reasoning_summary_text.delta":
                                reasoning = chunk.get("delta", "")
                                if reasoning:
                                    yield f"data: {json.dumps({'reasoning': reasoning})}\n\n"
                            elif event_type == "response.failed":
                                error_msg = chunk.get("response", {}).get("error", {}).get("message", "Unknown error")
                                logger.error(f"Response failed: {error_msg}")
                                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                            elif event_type == "response.completed":
                                logger.info(f"Response completed: {chunk.get('response', {}).get('usage', {})}")
                            elif event_type.startswith("response."):
                                logger.info(f"Response event: {event_type}")
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {e}")
    
    yield "data: [DONE]\n\n"


async def stream_anthropic_chat(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.anthropic.com",
    timeout: float = 60.0,
    **kwargs
) -> AsyncGenerator[str, None]:
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    api_url = build_api_url(url, "anthropic")
    
    body = {
        "model": model,
        "messages": formatted_messages,
        "max_tokens": 4096,
        "stream": True,
        **kwargs
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    logger.info("=" * 60)
    logger.info("Anthropic API Request:")
    logger.info(f"URL: {api_url}")
    logger.info(f"Body: {json.dumps(body, indent=2, ensure_ascii=False)}")
    logger.info("=" * 60)
    
    client = http_client_manager.client
    async with client.stream(
        "POST",
        api_url,
        headers=headers,
        json=body,
        timeout=timeout
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]
                try:
                    event = json.loads(data)
                    if event.get("type") == "content_block_delta":
                        if event.get("delta", {}).get("type") == "text_delta":
                            content = event["delta"]["text"]
                            yield f"data: {json.dumps({'content': content})}\n\n"
                except json.JSONDecodeError:
                    continue
    
    yield "data: [DONE]\n\n"


async def call_openai_chat(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.openai.com/v1",
    timeout: float = 60.0,
    **kwargs
) -> dict:
    api_url = build_api_url(url, "openai_chat")
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "enable_thinking": False,
        **kwargs
    }
    body = {k: v for k, v in body.items() if not (isinstance(v, list) and len(v) == 0)}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"OpenAI Chat Request URL: {api_url}")
    logger.info(f"OpenAI Chat Request body: {json.dumps(body, ensure_ascii=False, indent=2)}")
    
    client = http_client_manager.client
    response = await client.post(api_url, headers=headers, json=body, timeout=timeout)
    if response.status_code != 200:
        logger.error(f"OpenAI Chat call failed with status {response.status_code}: {response.text}")
        return {"error": f"LLM调用失败: {response.text}"}
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    logger.info(f"OpenAI Chat Response: {content}")
    
    return {"content": content}


async def call_openai_responses(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.openai.com/v1",
    timeout: float = 60.0,
    **kwargs
) -> dict:
    api_url = build_api_url(url, "openai_responses")
    body = {
        "model": model,
        "input": messages,
        "enable_thinking": False,
        "stream": False,
        **kwargs
    }
    body = {k: v for k, v in body.items() if not (isinstance(v, list) and len(v) == 0)}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"OpenAI Responses Request URL: {api_url}")
    logger.info(f"OpenAI Responses Request body: {json.dumps(body, ensure_ascii=False, indent=2)}")
    
    client = http_client_manager.client
    response = await client.post(api_url, headers=headers, json=body, timeout=timeout)
    if response.status_code != 200:
        logger.error(f"OpenAI Responses call failed with status {response.status_code}: {response.text}")
        return {"error": f"LLM调用失败: {response.text}"}
    
    result = response.json()
    
    content = ""
    output = result.get("output", [])
    if isinstance(output, list):
        for item in output:
            if item.get("type") == "message":
                content_list = item.get("content", [])
                if isinstance(content_list, list):
                    for content_item in content_list:
                        if content_item.get("type") == "output_text":
                            content = content_item.get("text", "")
                            break
    
    logger.info(f"OpenAI Responses Response: {content}")
    return {"content": content}


async def call_anthropic(
    messages: list,
    model: str,
    api_key: str,
    url: str = "https://api.anthropic.com",
    timeout: float = 60.0,
    **kwargs
) -> dict:
    formatted_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    
    api_url = build_api_url(url, "anthropic")
    
    body = {
        "model": model,
        "messages": formatted_messages,
        "max_tokens": 4096,
        **kwargs
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Anthropic Request URL: {api_url}")
    logger.info(f"Anthropic Request body: {json.dumps(body, ensure_ascii=False, indent=2)}")
    
    client = http_client_manager.client
    response = await client.post(api_url, headers=headers, json=body, timeout=timeout)
    if response.status_code != 200:
        logger.error(f"Anthropic call failed with status {response.status_code}: {response.text}")
        return {"error": f"LLM调用失败: {response.text}"}
    
    result = response.json()
    content_list = result.get("content", [])
    content = content_list[0].get("text", "") if content_list else ""
    
    logger.info(f"Anthropic Response: {content}")
    return {"content": content}


def detect_response_type(result: dict) -> str:
    if not isinstance(result, dict):
        return "unknown"
    
    if "choices" in result:
        choices = result.get("choices", [])
        if choices:
            choice = choices[0]
            if "message" in choice:
                return "openai_chat"
            elif "delta" in choice:
                return "openai_chat_stream"
    
    if "output" in result:
        output = result.get("output", [])
        if isinstance(output, list):
            for item in output:
                if item.get("type") == "message":
                    return "openai_responses"
    
    if "content" in result:
        content = result.get("content", [])
        if content and isinstance(content, list):
            if content[0].get("type") == "text" or "text" in content[0]:
                return "anthropic"
    
    if "text" in result and len(result) == 1:
        return "text"
    
    return "custom"


def extract_content_from_stream_data(data: dict) -> str:
    if 'choices' in data:
        choices = data.get('choices', [])
        if choices:
            choice = choices[0]
            delta = choice.get('delta', {})
            if delta:
                content = delta.get('content', '')
                if content:
                    return content
            message = choice.get('message', {})
            if message:
                content = message.get('content', '')
                if content:
                    return content
    
    elif 'output' in data:
        output = data.get('output', [])
        if isinstance(output, list):
            for item in output:
                if item.get('type') == 'message':
                    content_list = item.get('content', [])
                    if isinstance(content_list, list):
                        for content_item in content_list:
                            if content_item.get('type') == 'output_text':
                                return content_item.get('text', '')
    
    elif 'content' in data:
        content = data.get('content', [])
        if isinstance(content, list) and content:
            return content[0].get('text', '')
    
    elif 'text' in data:
        return data.get('text', '')
    
    elif 'd' in data:
        d = data.get('d', {})
        if isinstance(d, dict):
            answer = d.get('answer', '')
            if answer:
                return answer
    
    elif 'data' in data:
        data_obj = data.get('data', {})
        if isinstance(data_obj, dict):
            answer = data_obj.get('answer', '')
            if answer:
                return answer
    
    return ''


def extract_by_path(data: dict, path: str) -> str:
    keys = path.replace("]", "").replace("[", ".").split(".")
    keys = [k for k in keys if k]
    
    current = data
    for key in keys:
        if key.isdigit():
            key = int(key)
            if isinstance(current, list) and 0 <= key < len(current):
                current = current[key]
            else:
                return str(data)
        else:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return str(data)
    
    if isinstance(current, str):
        return current
    elif isinstance(current, (int, float, bool)):
        return str(current)
    else:
        return str(current) if current else str(data)


def extract_content_auto(result: dict) -> str:
    if "choices" in result:
        choices = result.get("choices", [])
        if choices:
            choice = choices[0]
            if "message" in choice:
                return choice.get("message", {}).get("content", str(result))
            elif "delta" in choice:
                return choice.get("delta", {}).get("content", str(result))
    
    elif "output" in result:
        output = result.get("output", [])
        if isinstance(output, list):
            for item in output:
                if item.get("type") == "message":
                    content = item.get("content", [])
                    if isinstance(content, list):
                        for content_item in content:
                            if content_item.get("type") == "output_text":
                                return content_item.get("text", str(result))
    
    elif "content" in result:
        content = result.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", str(result))
    
    elif "text" in result:
        return result.get("text", str(result))
    
    return str(result)


def extract_content_with_config(result: dict, config_str: Optional[str] = None) -> str:
    auto_result = extract_content_auto(result)
    if auto_result != str(result):
        logger.info("使用预设模式成功提取内容")
        return auto_result
    
    if not config_str:
        logger.info("预设模式提取失败，且无自定义配置，返回原始结果")
        return auto_result
    
    logger.info("预设模式提取失败，尝试使用自定义配置")
    
    try:
        config = json.loads(config_str)
    except json.JSONDecodeError:
        logger.warning(f"Invalid response_extract_config: {config_str}")
        return auto_result
    
    if "type" in config:
        extract_type = config["type"]
        
        if extract_type == "openai_chat":
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", str(result))
        
        elif extract_type == "openai_responses":
            output = result.get("output", [])
            if isinstance(output, list):
                for item in output:
                    if item.get("type") == "message":
                        content = item.get("content", [])
                        if isinstance(content, list):
                            for content_item in content:
                                if content_item.get("type") == "output_text":
                                    return content_item.get("text", str(result))
        
        elif extract_type == "anthropic":
            content = result.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", str(result))
        
        elif extract_type == "text":
            if "text" in result:
                return result.get("text", str(result))
            return str(result)
    
    elif "path" in config:
        path = config["path"]
        return extract_by_path(result, path)
    
    return auto_result
