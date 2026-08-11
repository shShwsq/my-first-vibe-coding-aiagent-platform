import logging
import httpx
import asyncio
import os
import uuid
import io
import base64
import json
import re
from contextvars import ContextVar
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.utils.param_converter import convert_param_type
from app.http_client import http_client_manager

logger = logging.getLogger(__name__)

WORKFLOW_FILES_DIR = Path(__file__).parent.parent.parent.parent / "workflow_files"

_current_node_id: ContextVar[Optional[Union[int, str]]] = ContextVar('current_node_id', default=None)


class GotoExit(Exception):
    """用于提前退出 exec 执行的自定义异常"""
    pass


class FinalReturnExit(Exception):
    """用于 final_return 提前退出 exec 执行的自定义异常"""
    pass

class DictObject:
    """字典对象，支持属性访问"""
    def __init__(self, data: Any = None):
        self._data = data if data is not None else {}
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return super().__getattribute__(name)
        if isinstance(self._data, dict):
            if name in self._data:
                value = self._data[name]
                if isinstance(value, dict):
                    return DictObject(value)
                return value
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
    
    def __getitem__(self, key):
        return self._data[key] if isinstance(self._data, dict) else None
    
    def get(self, key, default=None):
        if isinstance(self._data, dict):
            return self._data.get(key, default)
        return default
    
    def __repr__(self):
        return f"DictObject({self._data})"


class Memory:
    def __init__(self, db: Optional[Session] = None, user_id: Optional[int] = None, agent_id: Optional[int] = None):
        self._data: Dict[str, Any] = {}
        self._editable: Dict[str, bool] = {}
        self._long_memory: Dict[str, Any] = {}
        self.history: List[Dict[str, str]] = []
        self._db = db
        self._user_id = user_id
        self._agent_id = agent_id
    
    def set(self, name: str, value: Any, is_editable: bool = False, is_long: bool = False):
        self._data[name] = value
        self._editable[name] = is_editable
        if is_long:
            self._long_memory[name] = value
        logger.info(f"Memory.set: {name}={value}, is_editable={is_editable}, is_long={is_long}")
    
    def get(self, name: str) -> Any:
        if name == "history":
            logger.info(f"Memory.get: history={self.history}")
            return self.history
        
        value = self._data.get(name)
        if value is not None:
            logger.info(f"Memory.get (from memory): {name}={value}")
            return value
        
        value = self._long_memory.get(name)
        if value is not None:
            self._data[name] = value
            logger.info(f"Memory.get (from long memory): {name}={value}")
            return value
        
        logger.info(f"Memory.get: {name}=None")
        return None
    
    def get_long_memory_data(self) -> Dict[str, Any]:
        return self._long_memory.copy()


class WorkflowContext:
    def __init__(self, db: Optional[Session] = None, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.variables: Dict[str, Any] = {}
        self.node_outputs: Dict[str, Any] = {}
        self._goto_targets: List[str] = []
        self._loop_counts: Dict[Union[str, tuple], int] = {}
        self._background_tasks: Dict[str, asyncio.Task] = {}
        self._final_result: Any = None
        self._history_enabled: Dict[str, bool] = {}
        self._verbose_outputs: List[Dict[str, Any]] = []
        self._verbose_queue: Optional[asyncio.Queue] = None
        self.memory: Optional[Memory] = None
        self._ui_elements: Dict[str, Any] = {"buttons": [], "charts": [], "modals": []}
        self._ui_layout: Dict[str, Any] = {}
        self._saved_files: List[Dict[str, Any]] = []
    
    def _get_db_session(self) -> Session:
        """
        获取数据库会话，优先使用已有的会话，否则创建新会话
        
        如果需要在数据库操作后关闭会话，应该使用 _release_db_session 方法
        """
        if self.db:
            return self.db
        
        from app.database import SessionLocal
        return SessionLocal()
    
    def _release_db_session(self, db: Session):
        """
        释放数据库会话
        
        如果会话是外部传入的，不关闭；如果是内部创建的，关闭会话
        """
        if db and db is not self.db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"关闭数据库会话时出错（可能是连接已失效）: {e}")
                try:
                    db.invalidate()
                except Exception:
                    pass
    
    def set_verbose_queue(self, queue: asyncio.Queue):
        self._verbose_queue = queue
    
    def set(self, name: str, value: Any):
        self.variables[name] = value
        logger.debug(f"ctx.set: {name}={value}")
    
    def get(self, name: str) -> Any:
        value = self.variables.get(name)
        logger.debug(f"ctx.get: {name}={value}")
        return value
    
    def goto(self, *targets: Union[int, str], max_loops: int = 10) -> bool:
        if not targets:
            logger.warning("ctx.goto: 没有指定跳转目标")
            return False
        
        current_node = _current_node_id.get()
        target_key = (str(current_node),) + tuple(str(t) for t in targets)
        current_count = self._loop_counts.get(target_key, 0)
        
        if current_count >= max_loops:
            logger.warning(f"ctx.goto: 从节点 {current_node} 跳转到 {targets} 已达到最大次数 {max_loops}")
            return False
        
        self._loop_counts[target_key] = current_count + 1
        self._goto_targets = [str(t) for t in targets]
        logger.debug(f"ctx.goto: from={current_node}, targets={targets}, count={current_count + 1}")
        
        raise GotoExit(f"跳转到节点: {targets}")
    
    def final_return(self, result: Any, history: bool = True):
        self._final_result = result
        current_node = _current_node_id.get()
        if current_node is not None:
            self._history_enabled[str(current_node)] = history
        
        if history and self.memory is not None:
            if isinstance(result, dict):
                result_str = json.dumps(result, ensure_ascii=False)
            else:
                result_str = str(result)
            
            self.memory.history.append({
                "role": "assistant",
                "content": result_str
            })
            logger.debug(f"ctx.final_return: 已添加历史记录, history长度={len(self.memory.history)}")
        
        logger.debug(f"ctx.final_return: result={result}, history={history}, node={current_node}")
        
        raise FinalReturnExit(f"工作流最终返回: {result}")
    
    def verbose_return(self, content: Any, node_name: Optional[str] = None):
        verbose_item = {
            "content": content,
            "node_name": node_name or ""
        }
        self._verbose_outputs.append(verbose_item)
        logger.info(f"ctx.verbose_return: content={content}, node_name={node_name}, queue_exists={self._verbose_queue is not None}")
        
        if self._verbose_queue:
            try:
                self._verbose_queue.put_nowait(verbose_item)
                logger.info(f"ctx.verbose_return: 成功放入队列, queue_size={self._verbose_queue.qsize()}")
            except Exception as e:
                logger.error(f"Failed to put verbose output to queue: {e}")
        else:
            logger.warning("ctx.verbose_return: verbose_queue 为 None，无法实时传输")
    
    def output(self, *node_ids: Union[int, str], join_mode: str = "dict") -> Any:
        if not node_ids:
            logger.warning("ctx.output: 没有指定节点ID")
            return None
        
        if len(node_ids) == 1:
            node_id = str(node_ids[0])
            output = self.node_outputs.get(node_id)
            logger.debug(f"ctx.output: node_id={node_id}, output={output}")
            if isinstance(output, dict):
                return DictObject(output)
            return output
        
        results = {}
        for nid in node_ids:
            node_output = self.node_outputs.get(str(nid))
            if node_output is not None:
                results[str(nid)] = node_output
        
        if join_mode == "list":
            return list(results.values())
        elif join_mode == "str":
            return ", ".join(str(v) for v in results.values())
        else:
            return DictObject(results)
    
    async def wait_for_nodes(self, *node_ids: Union[int, str]) -> Dict[Union[int, str], Any]:
        if not node_ids:
            return {}
        
        results = {}
        for nid in node_ids:
            node_id = str(nid)
            if node_id in self._background_tasks:
                task = self._background_tasks[node_id]
                if not task.done():
                    logger.debug(f"ctx.wait_for_nodes: 等待后台节点 {node_id} 完成")
                    try:
                        result = await task
                        self.node_outputs[node_id] = result
                        results[node_id] = result
                    except Exception as e:
                        logger.error(f"ctx.wait_for_nodes: 节点 {node_id} 执行失败: {e}")
                        results[node_id] = {"error": str(e)}
                else:
                    results[node_id] = self.node_outputs.get(node_id)
            else:
                results[node_id] = self.node_outputs.get(node_id)
        
        logger.debug(f"ctx.wait_for_nodes: 结果={results}")
        return results
    
    async def http(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: str = "") -> tuple:
        logger.debug(f"ctx.http: url={url}, method={method}")
        
        try:
            client = http_client_manager.client
            if method.upper() == "GET":
                response = await client.get(url, headers=headers or {})
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers or {}, content=body)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers or {}, content=body)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers or {})
            else:
                response = await client.request(method, url, headers=headers or {}, content=body)
            
            logger.debug(f"ctx.http response: status={response.status_code}")
            return response.status_code, response.text, dict(response.headers)
        except Exception as e:
            logger.error(f"ctx.http error: {e}")
            return 500, str(e), {}
    
    async def knowledgebase(self, baselist: Optional[List[str]] = None, query: Optional[str] = None, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        logger.debug(f"ctx.knowledgebase: baselist={baselist}, query={query}, file_paths={file_paths}")
        
        if not query:
            logger.error("ctx.knowledgebase: 查询内容为空")
            return {"error": "查询内容为空", "context": None, "sources": []}
        
        db = self._get_db_session()
        should_release_db = db is not self.db
        
        try:
            from app.services.rag_service import retrieve_context_by_name, retrieve_context_from_file
            
            all_contexts = []
            sources = []
            
            if baselist:
                for base_name in baselist:
                    context = await retrieve_context_by_name(
                    base_name=base_name,
                    user_id=self.user_id,
                    query=query,
                    db=db
                )
                
                if context:
                    all_contexts.append(context)
                    sources.append(base_name)
            
            if file_paths:
                from app.models.file import BaseFile
                for file_path in file_paths:
                    test_file = db.query(BaseFile).filter(
                        BaseFile.file_path == file_path,
                        BaseFile.user_id == self.user_id
                    ).first()
                    
                    if test_file:
                        context = await retrieve_context_from_file(
                            db=db,
                            file_id=test_file.id,
                            user_id=self.user_id,
                            query=query
                        )
                        
                        if context:
                            all_contexts.append(context)
                            sources.append(test_file.filename)
            
            if not all_contexts:
                return {"error": None, "context": "", "sources": []}
            
            combined_context = "\n\n".join(all_contexts)
            
            return {
                "error": None,
                "context": combined_context,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"ctx.knowledgebase error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e), "context": None, "sources": []}
        finally:
            if should_release_db:
                self._release_db_session(db)
    
    def get_file_content(self, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        from app.services.file_storage import file_storage
        
        normalized_path = file_path.replace("\\", "/")
        
        if normalized_path.startswith("files/") or normalized_path.startswith("images/") or normalized_path.startswith("chunks/"):
            abs_path = file_storage.base_dir / normalized_path
        else:
            abs_path = WORKFLOW_FILES_DIR / file_path
        
        if not abs_path.exists():
            logger.warning(f"ctx.get_file_content: file not found: {file_path}")
            return []
        
        try:
            file_data = abs_path.read_bytes()
            extension = abs_path.suffix.lstrip(".").lower()
            
            from app.services.text_extractor import TextExtractor
            
            extractor = TextExtractor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            text = extractor.extract_text(file_data, extension)
            
            if not text:
                return []
            
            chunks = extractor.split_text_into_chunks(text)
            return [chunk_text for chunk_text, _ in chunks]
        except FileNotFoundError as e:
            logger.warning(f"ctx.get_file_content: {e}")
            return []
        except Exception as e:
            logger.error(f"ctx.get_file_content error: {e}")
            return []
    
    async def call_agent(
        self, 
        agent_id: Union[int, str], 
        agent_type: Optional[str] = None,
        verbose_return: bool = False,
        **kwargs
    ) -> Any:
        logger.debug(f"ctx.call_agent: agent_id={agent_id}, agent_type={agent_type}, verbose_return={verbose_return}, kwargs={kwargs}")
        
        db = self._get_db_session()
        try:
            if isinstance(agent_id, str) and agent_id.isdigit():
                agent_id = int(agent_id)
            
            from app.models.agent import Agent
            from app.models.workflow_agent import WorkflowAgent
            
            if agent_type == "workflow_agent":
                return await self._call_workflow_agent(agent_id, verbose_return=verbose_return, db=db, **kwargs)
            elif agent_type == "agent":
                return await self._call_http_agent(agent_id, verbose_return=verbose_return, db=db, **kwargs)
            else:
                workflow_agent = db.query(WorkflowAgent).filter(
                    WorkflowAgent.id == agent_id,
                    WorkflowAgent.user_id == self.user_id
                ).first()
                
                if workflow_agent:
                    return await self._call_workflow_agent(agent_id, verbose_return=verbose_return, db=db, **kwargs)
                
                http_agent = db.query(Agent).filter(
                    Agent.id == agent_id,
                    Agent.user_id == self.user_id
                ).first()
                
                if http_agent:
                    return await self._call_http_agent(agent_id, verbose_return=verbose_return, db=db, **kwargs)
                
                logger.warning(f"ctx.call_agent: 智能体 {agent_id} 不存在")
                return {"error": f"智能体 {agent_id} 不存在"}
                
        except Exception as e:
            logger.error(f"ctx.call_agent error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
        finally:
            self._release_db_session(db)
    
    async def _call_workflow_agent(
        self, 
        agent_id: Union[int, str], 
        verbose_return: bool = False,
        db: Optional[Session] = None,
        **kwargs
    ) -> Any:
        from app.models.workflow_agent import WorkflowAgent
        from app.routers.unified_agent_chat import execute_workflow_agent
        
        if not self.user_id:
            return {"error": "用户ID未初始化"}
        
        if db is None:
            db = self._get_db_session()
        
        should_release_db = db is not self.db
        
        try:
            agent = db.query(WorkflowAgent).filter(
                WorkflowAgent.id == agent_id,
                WorkflowAgent.user_id == self.user_id
            ).first()
            
            if not agent:
                logger.warning(f"ctx.call_agent: 工作流智能体 {agent_id} 不存在")
                return {"error": f"工作流智能体 {agent_id} 不存在"}
            
            query = kwargs.get("input_data") or kwargs.get("query") or kwargs.get("messages") or ""
            if isinstance(query, list):
                for msg in query:
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        query = msg.get("content", "")
                        break
                    elif isinstance(msg, str):
                        query = msg
                        break
            query = str(query) if query else ""
            
            params = {}
            for key, value in kwargs.items():
                if key not in ["input_data", "query", "messages", "verbose_return", "db"]:
                    params[key] = value
            
            verbose_queue: Optional[asyncio.Queue] = None
            if verbose_return:
                verbose_queue = self._verbose_queue
            
            result, stream_generator, executor = await execute_workflow_agent(
                agent=agent,
                query=query,
                db=None,
                user_id=self.user_id,
                params=params if params else None,
                verbose_queue=verbose_queue
            )
            
            full_content = ""
            
            if hasattr(result, '__aiter__'):
                async for chunk in result:
                    if chunk:
                        content = self._extract_stream_content(chunk)
                        if content:
                            full_content += content
                            if verbose_return:
                                self.verbose_return(content)
                return full_content
            else:
                final_result = full_content if full_content else (str(result) if result else "")
                if verbose_return:
                    self.verbose_return(final_result)
                return final_result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"工作流执行失败: {str(e)}"}
        finally:
            if should_release_db:
                self._release_db_session(db)
    
    async def _call_http_agent(
        self, 
        agent_id: Union[int, str], 
        verbose_return: bool = False,
        db: Optional[Session] = None,
        **kwargs
    ) -> Any:
        from app.models.agent import Agent
        from app.routers.unified_agent_chat import call_agent, stream_agent_call
        
        if not self.user_id:
            return {"error": "用户ID未初始化"}
        
        if db is None:
            db = self._get_db_session()
        
        should_release_db = db is not self.db
        
        try:
            agent = db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.user_id == self.user_id
            ).first()
            
            if not agent:
                logger.warning(f"ctx.call_agent: HTTP智能体 {agent_id} 不存在")
                return {"error": f"HTTP智能体 {agent_id} 不存在"}
            
            messages = kwargs.get("messages")
            query: Any = kwargs.get("query") or kwargs.get("input_data") or ""
            
            if messages:
                if isinstance(messages, list):
                    for msg in messages:
                        if isinstance(msg, dict) and msg.get("role") == "user":
                            query = msg.get("content", "")
                            break
                        elif isinstance(msg, str):
                            query = msg
                            break
                elif isinstance(messages, str):
                    query = messages
            
            params = {}
            for key, value in kwargs.items():
                if key not in ["input_data", "query", "messages", "verbose_return", "db"]:
                    params[key] = value
            
            response_type = str(agent.response_type) if agent.response_type is not None else "non_stream"
            
            if response_type == "stream":
                full_content = ""
                async for content in stream_agent_call(agent, str(query), params if params else None):
                    if verbose_return:
                        self.verbose_return(content)
                    full_content += content
                return full_content
            else:
                result = await call_agent(agent, str(query), params if params else None)
                if verbose_return:
                    self.verbose_return(result)
                return result
                
        except Exception as e:
            logger.error(f"HTTP agent call failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": f"调用智能体失败: {str(e)}"}
        finally:
            if should_release_db:
                self._release_db_session(db)
    
    def _extract_stream_content(self, chunk: str) -> str:
        import json
        content = ""
        if chunk.startswith("data: "):
            data_str = chunk[6:]
            if data_str.strip() and data_str.strip() != "[DONE]":
                try:
                    data = json.loads(data_str)
                    if isinstance(data.get("content"), str):
                        content = data["content"]
                except json.JSONDecodeError:
                    pass
        else:
            try:
                data = json.loads(chunk)
                if isinstance(data.get("content"), str):
                    content = data["content"]
            except json.JSONDecodeError:
                if chunk and not chunk.startswith('{'):
                    content = chunk
        return content
    
    def get_goto_targets(self) -> List[str]:
        return self._goto_targets
    
    def clear_goto_targets(self):
        self._goto_targets = []
    
    def should_return(self) -> bool:
        return self._final_result is not None
    
    def get_final_result(self) -> Any:
        return self._final_result
    
    def get_verbose_outputs(self) -> List[Dict[str, Any]]:
        return self._verbose_outputs
    
    def is_history_enabled(self, node_id: Optional[Union[int, str]] = None) -> bool:
        if node_id is None:
            node_id = _current_node_id.get()
        if node_id is None:
            return True
        return self._history_enabled.get(str(node_id), True)
    
    def increment_loop_count(self, node_id: Union[int, str]):
        key = str(node_id)
        self._loop_counts[key] = self._loop_counts.get(key, 0) + 1
    
    def get_loop_count(self, node_id: Union[int, str]) -> int:
        return self._loop_counts.get(str(node_id), 0)
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        logger.debug(f"ctx.call_tool: tool_name={tool_name}, kwargs={kwargs}")
        logger.debug(f"ctx.call_tool: kwargs types = {[(k, type(v).__name__) for k, v in kwargs.items()]}")
        
        db = self._get_db_session()
        should_release_db = db is not self.db
        
        try:
            from app.models.code_tool import CodeTool
            
            tool = db.query(CodeTool).filter(
                CodeTool.user_id == self.user_id,
                CodeTool.name == tool_name,
                CodeTool.is_active == True
            ).first()
            
            if not tool:
                logger.warning(f"ctx.call_tool: 代码工具 '{tool_name}' 不存在或已禁用")
                return {"error": f"代码工具 '{tool_name}' 不存在或已禁用"}
            
            tool_code = tool.code
            tool_func_name = tool.name
            tool_parameters = tool.parameters
            logger.debug(f"ctx.call_tool: tool_parameters = {tool_parameters}")
            
        finally:
            if should_release_db:
                self._release_db_session(db)
        
        try:
            if tool_parameters:
                kwargs = self._convert_tool_params(kwargs, tool_parameters)
                logger.debug(f"ctx.call_tool: after conversion, kwargs types = {[(k, type(v).__name__) for k, v in kwargs.items()]}")
            
            global_vars = {"__builtins__": __builtins__}
            global_vars["ctx"] = self
            
            exec(tool_code, global_vars)
            
            if tool_func_name not in global_vars:
                return {"error": f"代码中未找到函数定义: {tool_func_name}"}
            
            func = global_vars[tool_func_name]
            
            if not callable(func):
                return {"error": f"{tool_func_name} 不是可调用的函数"}
            
            import inspect
            import asyncio
            if inspect.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = await asyncio.to_thread(func, **kwargs)
            
            logger.debug(f"ctx.call_tool: result={result}")
            return result
            
        except Exception as e:
            logger.error(f"ctx.call_tool error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def _convert_tool_params(self, kwargs: dict, parameters: list) -> dict:
        param_types = {p.get("name"): p.get("type", "str") for p in parameters}
        param_required = {p.get("name"): p.get("required", True) for p in parameters}
        converted = {}
        for key, value in kwargs.items():
            param_type = param_types.get(key, "str")
            converted[key] = convert_param_type(value, param_type)
        
        for param_name, required in param_required.items():
            if not required and param_name not in converted:
                converted[param_name] = None
                logger.debug(f"工作流调用工具：非必填参数 {param_name} 未传递，设置为 None")
        
        return converted
    
    def save_file(self, content: Any, filename: Optional[str] = None, file_type: Optional[str] = None) -> str:
        """
        保存工作流生成的文件（图片、Excel等）到服务器
        
        参数:
            content: 文件内容，支持以下类型：
                - bytes: 直接保存的二进制数据
                - str: base64编码的字符串（需指定file_type）
                - matplotlib.figure.Figure: matplotlib图表对象
                - pandas.DataFrame: 会保存为Excel文件
                - PIL.Image: PIL图片对象
            filename: 可选的文件名（不含扩展名），如不指定则自动生成UUID
            file_type: 文件类型，如 'png', 'jpg', 'xlsx', 'csv', 'pdf' 等
        
        返回:
            str: 文件的相对路径，可用于前端访问
        """
        try:
            WORKFLOW_FILES_DIR.mkdir(parents=True, exist_ok=True)
            
            date_prefix = datetime.now().strftime("%Y/%m/%d")
            file_dir = WORKFLOW_FILES_DIR / date_prefix
            file_dir.mkdir(parents=True, exist_ok=True)
            
            if filename is None:
                filename = str(uuid.uuid4())[:8]
            
            content_type = type(content).__name__
            extension = ""
            file_content = None
            
            if isinstance(content, bytes):
                file_content = content
                if file_type:
                    extension = f".{file_type}"
                else:
                    extension = ".bin"
            
            elif isinstance(content, str):
                try:
                    file_content = base64.b64decode(content)
                    if file_type:
                        extension = f".{file_type}"
                    else:
                        extension = ".bin"
                except Exception:
                    file_content = content.encode('utf-8')
                    extension = ".txt"
            
            elif hasattr(content, 'savefig'):
                if file_type in ['png', 'jpg', 'jpeg', 'pdf', 'svg']:
                    extension = f".{file_type}"
                else:
                    extension = ".png"
                    file_type = "png"
                
                buffer = io.BytesIO()
                content.savefig(buffer, format=file_type or 'png', bbox_inches='tight', dpi=150)
                buffer.seek(0)
                file_content = buffer.read()
                buffer.close()
            
            elif hasattr(content, 'to_excel'):
                extension = ".xlsx"
                file_type = "xlsx"
                buffer = io.BytesIO()
                content.to_excel(buffer, index=False, engine='openpyxl')
                buffer.seek(0)
                file_content = buffer.read()
                buffer.close()
            
            elif hasattr(content, 'to_csv'):
                extension = ".csv"
                file_type = "csv"
                file_content = content.to_csv(index=False).encode('utf-8')
            
            elif hasattr(content, 'save'):
                if file_type in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']:
                    extension = f".{file_type}"
                else:
                    extension = ".png"
                    file_type = "png"
                
                buffer = io.BytesIO()
                content.save(buffer, format=file_type.upper() if file_type else 'PNG')
                buffer.seek(0)
                file_content = buffer.read()
                buffer.close()
            
            else:
                file_content = str(content).encode('utf-8')
                extension = ".txt"
            
            dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
            safe_filename = filename
            for char in dangerous_chars:
                safe_filename = safe_filename.replace(char, '')
            safe_filename = safe_filename.strip()
            
            if not safe_filename:
                safe_filename = str(uuid.uuid4())[:8]
            
            if safe_filename.endswith(extension):
                safe_filename = safe_filename[:-len(extension)]
            
            full_filename = f"{safe_filename}{extension}"
            file_path = file_dir / full_filename
            
            counter = 1
            while file_path.exists():
                full_filename = f"{safe_filename}_{counter}{extension}"
                file_path = file_dir / full_filename
                counter += 1
            
            file_path.write_bytes(file_content)
            
            relative_path = str(file_path.relative_to(WORKFLOW_FILES_DIR))
            url_path = relative_path.replace("\\", "/")
            
            self._saved_files.append({
                "file_path": relative_path,
                "file_type": file_type or extension.lstrip('.')
            })
            
            logger.info(f"ctx.save_file: 保存文件成功, path={relative_path}, size={len(file_content)} bytes, type={content_type}")
            
            return f"/api/workflow-files/{url_path}"
            
        except Exception as e:
            logger.error(f"ctx.save_file error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"保存文件失败: {str(e)}"
    
    def save_chart(self, figure: Any, filename: Optional[str] = None, file_type: str = "png") -> str:
        """
        保存matplotlib图表到服务器（save_file的便捷方法）
        
        参数:
            figure: matplotlib.figure.Figure对象
            filename: 可选的文件名
            file_type: 图片格式，默认png
        
        返回:
            str: 文件的相对路径
        """
        return self.save_file(figure, filename=filename, file_type=file_type)
    
    def save_dataframe(self, df: Any, filename: Optional[str] = None, file_type: str = "xlsx") -> str:
        """
        保存pandas DataFrame到服务器（save_file的便捷方法）
        
        参数:
            df: pandas.DataFrame对象
            filename: 可选的文件名
            file_type: 文件格式，支持 'xlsx' 或 'csv'
        
        返回:
            str: 文件的相对路径
        """
        return self.save_file(df, filename=filename, file_type=file_type)
    
    def add_ui_element(self, element: Dict[str, Any]) -> None:
        """
        动态添加UI元素
        
        参数:
            element: UI元素配置字典，必须包含"type"字段
        """
        element_type = element.get("type")
        if element_type == "button":
            self._ui_elements["buttons"].append(element)
        elif element_type == "chart":
            self._ui_elements["charts"].append(element)
        elif element_type == "modal":
            self._ui_elements["modals"].append(element)
        else:
            logger.warning(f"未知的UI元素类型: {element_type}")
    
    def set_layout(self, layout: Dict[str, Any]) -> None:
        """
        设置UI布局配置
        
        参数:
            layout: 布局配置，支持以下字段：
                - direction: 布局方向，"row"（横向）或 "column"（纵向），默认 "column"
                - gap: 元素间距，如 "16px"
                - padding: 内边距，如 "20px"
                - align: 对齐方式，"start", "center", "end", "stretch"
                - justify: 主轴对齐，"start", "center", "end", "space-between", "space-around"
                - chart_width: 图表默认宽度，如 "400px" 或 "100%"
                - chart_height: 图表默认高度，如 "300px"
                - button_group: 按钮组配置，如 {"position": "top", "align": "center"}
        
        示例:
            ctx.set_layout({
                "direction": "column",
                "gap": "20px",
                "chart_width": "100%",
                "chart_height": "300px"
            })
        """
        self._ui_layout = layout
        logger.debug(f"ctx.set_layout: {layout}")
    
    def get_ui_elements(self) -> Dict[str, Any]:
        """
        获取动态添加的UI元素和布局配置
        
        返回:
            Dict: 包含 buttons, charts, modals 和 layout 的字典
        """
        return {
            "buttons": self._ui_elements.get("buttons", []),
            "charts": self._ui_elements.get("charts", []),
            "modals": self._ui_elements.get("modals", []),
            "layout": self._ui_layout,
            "context": self.variables
        }
    
    def clear_ui(self) -> None:
        """
        清除所有动态添加的UI元素和布局配置
        """
        self._ui_elements = {"buttons": [], "charts": [], "modals": []}
        self._ui_layout = {}
        logger.debug("ctx.clear_ui: 已清除所有UI元素")
    
    def add_button(self, id: str, label: str, action: Dict[str, Any], style: Optional[Dict[str, Any]] = None) -> None:
        """
        添加按钮
        
        参数:
            id: 按钮ID
            label: 按钮显示文本
            action: 点击动作，支持以下类型：
                - {"type": "show_modal", "modal_id": "modal1"}：显示弹窗
                - {"type": "close_modal", "modal_id": "modal1"}：关闭弹窗
                - {"type": "download", "url": "path/to/file"}：下载文件
                - {"type": "send_text", "text": "你好"}：发送指定文本到对话
            style: 可选的样式配置
        """
        button = {
            "type": "button",
            "id": id,
            "label": label,
            "action": action
        }
        if style:
            button["style"] = style
        self._ui_elements["buttons"].append(button)
        logger.debug(f"ctx.add_button: id={id}, label={label}, action={action}")
    
    def add_chart(self, id: str, chart_type: str, data: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None, image_url: Optional[str] = None) -> None:
        """
        添加图表
        
        参数:
            id: 图表ID
            chart_type: 图表类型（bar, line, pie, doughnut, radar, scatter）
            data: 可选的图表数据
            options: 可选的图表配置
            image_url: 可选的图片URL（如ctx.save_file()返回的路径）
        """
        chart: Dict[str, Any] = {
            "type": "chart",
            "id": id,
            "chart_type": chart_type
        }
        if data:
            chart["data"] = data
        if options:
            chart["options"] = options
        
        if not image_url and data:
            image_url = self._generate_chart_image(id, chart_type, data, options)
        
        if image_url:
            chart["image_url"] = image_url
        self._ui_elements["charts"].append(chart)
        logger.debug(f"ctx.add_chart: id={id}, type={chart_type}")
    
    def _generate_chart_image(self, chart_id: str, chart_type: str, data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Optional[str]:
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
            
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
            labels = data.get('labels', [])
            datasets = data.get('datasets', [])
            
            if not datasets:
                return None
            
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
            
            if chart_type == 'radar':
                fig = plt.figure(figsize=(8, 6))
                ax = fig.add_subplot(111, polar=True)
                
                angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
                angles += angles[:1]
                
                for i, dataset in enumerate(datasets):
                    values = dataset.get('data', [])
                    values = values + values[:1] if values else []
                    label = dataset.get('label', '')
                    ax.plot(angles, values, 'o-', linewidth=2, label=label, color=colors[i % len(colors)])
                    ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(labels)
                if len(datasets) > 1:
                    ax.legend()
            
            else:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                if chart_type in ('pie', 'doughnut'):
                    dataset = datasets[0]
                    values = dataset.get('data', [])
                    ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors[:len(values)])
                    ax.axis('equal')
                
                elif chart_type == 'bar':
                    x = np.arange(len(labels))
                    width = 0.8 / len(datasets) if len(datasets) > 1 else 0.8
                    
                    for i, dataset in enumerate(datasets):
                        values = dataset.get('data', [])
                        label = dataset.get('label', '')
                        offset = (i - len(datasets)/2 + 0.5) * width if len(datasets) > 1 else 0
                        ax.bar(x + offset, values, width, label=label, color=colors[i % len(colors)])
                    
                    ax.set_xticks(x)
                    ax.set_xticklabels(labels)
                    if len(datasets) > 1:
                        ax.legend()
                
                elif chart_type == 'line':
                    for i, dataset in enumerate(datasets):
                        values = dataset.get('data', [])
                        label = dataset.get('label', '')
                        ax.plot(labels, values, marker='o', label=label, color=colors[i % len(colors)])
                    if len(datasets) > 1:
                        ax.legend()
                
                elif chart_type == 'scatter':
                    for i, dataset in enumerate(datasets):
                        points = dataset.get('data', [])
                        label = dataset.get('label', '')
                        if points and isinstance(points[0], (list, tuple)):
                            x_vals = [p[0] for p in points]
                            y_vals = [p[1] for p in points]
                        else:
                            x_vals = range(len(points))
                            y_vals = points
                        ax.scatter(x_vals, y_vals, label=label, color=colors[i % len(colors)])
                    if len(datasets) > 1:
                        ax.legend()
                
                else:
                    logger.warning(f"Unknown chart type: {chart_type}")
                    plt.close(fig)
                    return None
            
            if options and options.get('title', {}).get('text'):
                fig.suptitle(options['title']['text'])
            
            plt.tight_layout()
            
            image_url = self.save_file(fig, filename=f"chart_{chart_id}", file_type="png")
            plt.close(fig)
            
            return image_url
            
        except Exception as e:
            logger.error(f"Failed to generate chart image: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def add_modal(self, id: str, title: str, content: str, css: Optional[str] = None, script: Optional[str] = None, width: str = "600px", height: str = "auto", close_on_overlay: bool = True) -> None:
        """
        添加弹窗
        
        参数:
            id: 弹窗ID
            title: 弹窗标题
            content: 弹窗内容（支持HTML，可包含{{chart:图表ID}}占位符）
            css: 自定义CSS样式
            script: 自定义JavaScript脚本
            width: 弹窗宽度
            height: 弹窗高度
            close_on_overlay: 点击遮罩层是否关闭弹窗
        """
        modal = {
            "type": "modal",
            "id": id,
            "title": title,
            "content": content,
            "width": width,
            "height": height,
            "close_on_overlay": close_on_overlay
        }
        if css:
            modal["css"] = css
        if script:
            modal["script"] = script
        self._ui_elements["modals"].append(modal)
        logger.debug(f"ctx.add_modal: id={id}, title={title}")

    def _get_api_config(self, model_id: Optional[int] = None) -> Any:
        """
        获取 API 配置，使用临时数据库会话
        """
        from app.models.api_config import ApiConfig
        
        db = self._get_db_session()
        should_release = db is not self.db
        
        try:
            if model_id:
                config = db.query(ApiConfig).filter(
                    ApiConfig.id == model_id,
                    ApiConfig.user_id == self.user_id
                ).first()
            else:
                config = db.query(ApiConfig).filter(
                    ApiConfig.user_id == self.user_id,
                    ApiConfig.is_default == True
                ).first()
                
                if not config:
                    config = db.query(ApiConfig).filter(
                        ApiConfig.user_id == self.user_id
                    ).first()
            
            return config
        finally:
            if should_release:
                self._release_db_session(db)
    
    def _process_value(self, value):
        if isinstance(value, dict):
            if "__expr__" in value:
                return self._eval_expression(value["__expr__"])
            if "__template__" in value:
                return self._process_template(value["__template__"])
            return {k: self._process_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._process_value(item) for item in value]
        elif isinstance(value, str):
            return self._process_variables(value)
        return value
    
    def _process_template(self, parts):
        result = []
        for part in parts:
            if isinstance(part, dict) and "__expr__" in part:
                expr_value = self._eval_expression(part["__expr__"])
                result.append(str(expr_value) if expr_value is not None else "")
            else:
                result.append(str(part))
        return ''.join(result)
    
    def _process_variables(self, text: str) -> str:
        logger.debug(f"处理变量: {text[:100]}..." if len(text) > 100 else f"处理变量: {text}")
        
        original_text = text
        
        eval_locals = {
            'ctx': self,
            'memory': self.memory
        }
        
        def eval_braced_expr(match):
            expr_content = match.group(1)
            try:
                result = eval(expr_content, {}, eval_locals)
                logger.debug(f"表达式 {{{expr_content}}} = {result}")
                return str(result) if result is not None else ""
            except Exception as e:
                logger.debug(f"表达式计算失败: {e}")
                return match.group(0)
        
        text = re.sub(r'\{(ctx\.[^{}]+|memory\.[^{}]+)\}', eval_braced_expr, text)
        
        if text != original_text:
            logger.debug(f"变量处理后: {text[:100]}..." if len(text) > 100 else f"变量处理后: {text}")
        
        return text
    
    def _eval_expression(self, expression: str):
        logger.debug(f"计算表达式: {expression}")
        
        try:
            expr = str(expression)
            expr = expr.replace('ctx.', 'self.')
            expr = expr.replace('memory.', 'self.memory.')
            
            result = eval(expr)
            logger.debug(f"表达式结果: {result}")
            return result
        except Exception as e:
            logger.debug(f"表达式计算失败: {e}, 返回原表达式")
            return expression
    
    async def _wrap_stream_with_history(self, stream_generator):
        full_content = ""
        chunk_count = 0
        async for chunk in stream_generator:
            chunk_count += 1
            if chunk:
                content = None
                if chunk.startswith("data: "):
                    data_str = chunk[6:]
                    if data_str.strip() and data_str.strip() != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if isinstance(data.get("content"), str):
                                content = data["content"]
                        except json.JSONDecodeError:
                            pass
                else:
                    try:
                        data = json.loads(chunk)
                        if isinstance(data.get("content"), str):
                            content = data["content"]
                    except json.JSONDecodeError:
                        if chunk and not chunk.startswith('{'):
                            content = chunk
                
                if content:
                    full_content += content
                yield chunk
        
        logger.info(f"流式输出完成，共处理 {chunk_count} 个 chunk，内容长度: {len(full_content)}")
        if full_content and self.memory:
            self._add_to_history(full_content)
            logger.info(f"已保存到 history，当前 history 长度: {len(self.memory.history)}")
        else:
            logger.warning("full_content 为空，未保存到 history")
    
    def _add_to_history(self, content: Any, role: Optional[str] = "assistant"):
        if isinstance(content, dict):
            content_str = json.dumps(content, ensure_ascii=False)
        else:
            content_str = str(content)
        
        if self.memory:
            self.memory.history.append({
                "role": role or "assistant",
                "content": content_str
            })
            logger.debug(f"添加到历史记录: {content_str[:100]}..." if len(content_str) > 100 else f"添加到历史记录: {content_str}")
    
    async def call_model(
        self,
        model_id: Optional[int],
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_search: Optional[bool] = None,
        stream: bool = False,
        output_format: str = 'text',
        timeout: int = 60
    ) -> Union[str, Dict[str, Any], DictObject, AsyncGenerator]:
        """
        调用大模型
        
        参数:
            model_id: 模型配置ID（为None时使用默认模型）
            messages: 消息列表
            tools: 工具列表（可选）
            enable_search: 是否启用搜索功能（可选）
            stream: 是否流式输出
            output_format: 输出格式，'text' 或 'json'
            timeout: 超时时间（秒）
        
        返回:
            非流式：文本内容或解析后的JSON对象
            流式：异步生成器（由调用方处理）
        """
        from app.services.llm_client import call_llm, stream_llm
        
        config = self._get_api_config(model_id)
        
        if not config:
            logger.error("未找到模型配置")
            return {"error": "未找到模型配置，请先配置API"}
        
        call_type = getattr(config, 'call_type', None) or "OpenAI Chat"
        api_url = getattr(config, 'api_url', None)
        model_code = getattr(config, 'code', '')
        api_key = getattr(config, 'api_key', '')
        
        logger.info(f"ctx.call_model: model={model_code}, call_type={call_type}, stream={stream}, output_format={output_format}")
        
        url = str(api_url) if api_url else "https://api.anthropic.com"
        
        try:
            if stream:
                stream_generator = stream_llm(
                    messages=messages,
                    model=model_code,
                    api_key=api_key,
                    url=url,
                    call_type=call_type,
                    timeout=float(timeout),
                    tools=tools,
                    enable_search=enable_search
                )
                return stream_generator
            else:
                result = await call_llm(
                    messages=messages,
                    model=model_code,
                    api_key=api_key,
                    url=url,
                    call_type=call_type,
                    structured_output=(output_format == 'json'),
                    timeout=float(timeout),
                    default_response={"content": ""},
                    tools=tools,
                    enable_search=enable_search
                )
                
                logger.debug(f"模型响应长度: {len(result)}")
                
                if output_format == 'json':
                    try:
                        parsed_content = json.loads(result) if isinstance(result, str) else result
                        if isinstance(parsed_content, dict):
                            return DictObject(parsed_content)
                        return parsed_content
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON解析失败，返回原始内容: {e}")
                        return result
                else:
                    content = result.get("content", "")
                    return content
        except Exception as e:
            logger.error(f"ctx.call_model error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
