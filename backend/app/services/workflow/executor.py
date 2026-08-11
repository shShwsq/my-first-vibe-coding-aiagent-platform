import logging
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from sqlalchemy.orm import Session

from .context import WorkflowContext, Memory, DictObject, _current_node_id, GotoExit, FinalReturnExit
from .workflow_logger import WorkflowLogger
from app.utils.param_converter import convert_param_type

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, db: Optional[Session] = None, user_id: Optional[int] = None,
                 agent_id: Optional[int] = None):
        logger.debug(f"WorkflowExecutor.__init__: user_id={user_id}")
        self.db = db
        self.user_id = user_id
        self.agent_id = agent_id
        self.ctx = WorkflowContext(db=None, user_id=user_id)
        self.memory = Memory(db=db, user_id=user_id, agent_id=agent_id)
        self.ctx.memory = self.memory
        self.verbose_outputs: List[Any] = []
        self._stream_node: Optional[str] = None
        self._stream_generator: Optional[AsyncGenerator] = None
        self._verbose_queue: Optional[asyncio.Queue] = None
        self._kwargs: Dict[str, Any] = {}
        
        self.workflow_logger = WorkflowLogger(
            user_id=user_id,
            agent_id=agent_id
        )
    
    def _get_db_session(self) -> Session:
        if self.db:
            return self.db
        from app.database import SessionLocal
        return SessionLocal()
    
    def _release_db_session(self, db: Session):
        if db and db is not self.db:
            db.close()
    
    def load_memory(self, conversation_id: Optional[int] = None):
        if not self.db:
            return
        
        if conversation_id:
            from app.models import WorkflowMemory
            memories = self.db.query(WorkflowMemory).filter(
                WorkflowMemory.conversation_id == conversation_id
            ).all()
            
            for mem in memories:
                if mem.key == "history":
                    try:
                        self.memory.history = json.loads(mem.value) if mem.value else []
                    except json.JSONDecodeError:
                        self.memory.history = []
                else:
                    try:
                        self.memory._data[mem.key] = json.loads(mem.value) if mem.value and mem.value.strip() else mem.value
                    except json.JSONDecodeError:
                        self.memory._data[mem.key] = mem.value
                    self.memory._editable[mem.key] = mem.is_editable
            
            logger.info(f"Loaded {len(memories)} memory items for conversation {conversation_id}")
        
        if self.user_id and self.agent_id:
            try:
                from app.models.workflow_long_memory import WorkflowLongMemory
                long_memories = self.db.query(WorkflowLongMemory).filter(
                    WorkflowLongMemory.user_id == self.user_id,
                    WorkflowLongMemory.agent_id == self.agent_id
                ).all()
                
                for long_mem in long_memories:
                    try:
                        self.memory._long_memory[long_mem.key] = json.loads(long_mem.value) if long_mem.value and long_mem.value.strip() else long_mem.value
                    except json.JSONDecodeError:
                        self.memory._long_memory[long_mem.key] = long_mem.value
                
                logger.info(f"Loaded {len(long_memories)} long memory items for user {self.user_id}, agent {self.agent_id}")
            except Exception as e:
                logger.error(f"Failed to load long memories: {e}")
    
    def get_memory_data(self) -> Dict[str, Any]:
        data = {
            "history": self.memory.history,
            "variables": {}
        }
        for key, value in self.memory._data.items():
            data["variables"][key] = {
                "value": value,
                "is_editable": self.memory._editable.get(key, False)
            }
        return data
    
    def get_ui_config(self) -> Optional[Dict[str, Any]]:
        """
        获取工作流UI配置
        
        优先返回UI节点的配置，如果没有UI节点则返回动态添加的UI元素
        """
        for node_id, output in self.ctx.node_outputs.items():
            if isinstance(output, dict) and output.get("type") == "ui":
                return output
        
        ui_elements = self.ctx.get_ui_elements()
        if ui_elements["buttons"] or ui_elements["charts"] or ui_elements["modals"]:
            return ui_elements
        
        return None
    
    def get_saved_files(self) -> List[Dict[str, Any]]:
        """
        获取工作流保存的文件列表
        """
        return self.ctx._saved_files
    
    def set_verbose_queue(self, queue: asyncio.Queue):
        self._verbose_queue = queue
        self.ctx.set_verbose_queue(queue)
    
    def _emit_verbose(self, content: Any, node_name: str = ""):
        verbose_item = {
            "content": content,
            "node_name": node_name
        }
        self.verbose_outputs.append(verbose_item)
        
        if self._verbose_queue:
            try:
                self._verbose_queue.put_nowait(verbose_item)
                logger.debug(f"Verbose item 已放入队列: {content}")
            except Exception as e:
                logger.error(f"Failed to emit verbose: {e}")
        else:
            logger.warning(f"Verbose queue 为 None，跳过输出: {content}")
    
    def has_stream_node(self) -> bool:
        return self._stream_node is not None
    
    def get_stream_generator(self) -> Optional[AsyncGenerator]:
        return self._stream_generator
    
    async def execute(self, nodes: Dict[str, Any], **kwargs):
        self._kwargs = kwargs
        
        input_data = kwargs.get("input_data") or kwargs.get("query") or ""
        if input_data:
            self.memory.history.append({
                "role": "user",
                "content": str(input_data)
            })
            logger.debug(f"已添加用户输入到 history: {str(input_data)[:100]}...")
        
        self.workflow_logger.info(f"=== 开始执行工作流 ===")
        logger.info(f"=== 开始执行工作流 ===")
        logger.debug(f"节点数量: {len(nodes)}")
        logger.debug(f"输入数据: {kwargs}")
        logger.debug(f"节点详情: {nodes}")
        
        result = await self._execute_from_node(nodes)
        
        if self.ctx._background_tasks:
            self.workflow_logger.info(f"等待 {len(self.ctx._background_tasks)} 个后台任务完成...")
            logger.info(f"等待 {len(self.ctx._background_tasks)} 个后台任务完成...")
            await asyncio.gather(*self.ctx._background_tasks.values(), return_exceptions=True)
            self.workflow_logger.info("所有后台任务已完成")
            logger.info("所有后台任务已完成")
        
        final_result = self.ctx.get_final_result() or result or "工作流执行完成"
        self.workflow_logger.info(f"=== 工作流执行完成 ===")
        logger.info(f"=== 工作流执行完成 ===")
        logger.debug(f"最终结果: {final_result if not self._stream_generator else '[流式输出]'}")
        
        def safe_serialize(obj):
            if hasattr(obj, '__aiter__'):
                return '<async_generator>'
            elif isinstance(obj, dict):
                return {k: safe_serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [safe_serialize(item) for item in obj]
            elif isinstance(obj, DictObject):
                return obj.__dict__
            return obj
        
        logger.debug(f"节点输出: {json.dumps(safe_serialize(self.ctx.node_outputs), ensure_ascii=False)}")
        logger.debug(f"变量: {json.dumps(self.ctx.variables, ensure_ascii=False)}")
        
        verbose_outputs = self.get_verbose_outputs()
        if verbose_outputs:
            self.workflow_logger.info(f"Verbose 输出: {json.dumps(verbose_outputs, ensure_ascii=False, default=str)}")
        
        self.workflow_logger.flush()
        
        return final_result
    
    async def _execute_from_node(self, nodes: Dict[str, Any], start_from: Optional[str] = None) -> Any:
        node_order = self._get_node_order(nodes)
        
        if start_from:
            if start_from in nodes:
                current_index = node_order.index(start_from)
            else:
                logger.warning(f"起始节点 {start_from} 不存在，从头开始执行")
                current_index = 0
        else:
            current_index = 0
        
        while current_index < len(node_order):
            node_key = node_order[current_index]
            
            if node_key.endswith('_code'):
                code_block = nodes[node_key]
                base_node_id = node_key[:-5]
                logger.debug(f"执行代码块: {code_block[:200]}..." if len(str(code_block)) > 200 else f"执行代码块: {code_block}")
                
                token = _current_node_id.set(base_node_id)
                try:
                    await self._execute_code_block(code_block)
                finally:
                    _current_node_id.reset(token)
                
                if self.ctx.should_return():
                    logger.info("代码块返回 final_return，终止工作流")
                    result = self.ctx.get_final_result()
                    return result
                
                goto_targets = self.ctx.get_goto_targets()
                if goto_targets:
                    self.ctx.clear_goto_targets()
                    
                    if len(goto_targets) > 1:
                        logger.info(f"并行跳转到 {len(goto_targets)} 个目标: {goto_targets}")
                        results = await self._execute_parallel_targets(nodes, goto_targets)
                        return results
                    else:
                        target_key = str(goto_targets[0])
                        if target_key in nodes:
                            current_index = node_order.index(target_key)
                            continue
                        else:
                            logger.warning(f"跳转目标节点 {target_key} 不存在")
                
                current_index += 1
                continue
            
            node_str = nodes[node_key]
            node = self._parse_node_string(node_str)
            
            if not node:
                logger.warning(f"无法解析节点: {node_key}")
                current_index += 1
                continue
            
            node_id = node.get('id') or node_key
            node_type = node.get('node')
            
            self.workflow_logger.set_node_context(str(node_id), node_type)
            self.workflow_logger.info(f"--- 执行节点 [{node_key}] {node_id} (类型: {node_type}) ---")
            logger.info(f"--- 执行节点 [{node_key}] {node_id} (类型: {node_type}) ---")
            logger.debug(f"节点详情: {json.dumps(node, ensure_ascii=False, indent=2)}")
            
            max_loops = node.get('max_loops', 10)
            current_loop = self.ctx.get_loop_count(node_id)
            
            self.ctx.increment_loop_count(node_id)
            
            token = _current_node_id.set(node_id)
            try:
                is_async_node = node.get('async', False)
                wait_nodes = node.get('wait', [])
                
                if wait_nodes:
                    logger.info(f"节点 {node_id} 等待后台节点: {wait_nodes}")
                    await self.ctx.wait_for_nodes(*wait_nodes)
                
                timeout = node.get('timeout', 60)
                
                if is_async_node:
                    logger.info(f"节点 {node_id} 设置为后台执行")
                    task = asyncio.create_task(
                        self._execute_node_async_wrapper(node, timeout, node_id)
                    )
                    self.ctx._background_tasks[str(node_id)] = task
                    current_index += 1
                    continue
                
                is_last = self._is_last_node(nodes, node_key, node)
                if current_loop < max_loops:
                    logger.debug(f"节点 {node_id} 未达到最大执行次数 {max_loops}")
                    output = await self._execute_node(node, timeout, is_last)
                    logger.debug(f"节点 {node_id} 输出类型: {type(output).__name__}")
                
                    if output is not None:
                        self.ctx.node_outputs[str(node_id)] = output
                    
                    if self._stream_generator:
                        logger.info(f"节点 {node_id} 是流式输出节点，立即返回")
                        return output
                    
                    verbose = node.get('verbose', False)
                    if verbose and output is not None:
                        verbose_content = "[流式输出]" if hasattr(output, '__aiter__') else output
                        self._emit_verbose(verbose_content, node.get('name', '') or str(node_id))
                        logger.info(f"Verbose 输出 [{node_id}]: [流式输出]" if hasattr(output, '__aiter__') else f"Verbose 输出 [{node_id}]: {output}")
                    
                    history = node.get('history', False)
                    if is_last and output is not None:
                        logger.info(f"节点 {node_id} 是最后一个节点，自动设置 final_return")
                        self.ctx.final_return(output, history=True)
                        return output
                    elif history and output is not None:
                        self.ctx._add_to_history(output)
                else:
                    logger.warning(f"节点 {node_id} 已达到最大执行次数 {max_loops}")        
                
                next_nodes = node.get('next')
                if next_nodes:
                    if isinstance(next_nodes, str):
                        next_nodes = [next_nodes]
                    if isinstance(next_nodes, int):
                        next_nodes = [str(next_nodes)]
                    
                    logger.debug(f"跳转到节点: {next_nodes}")
                    
                    if len(next_nodes) > 1:
                        logger.info(f"并行跳转到 {len(next_nodes)} 个节点: {next_nodes}")
                        results = await self._execute_parallel_targets(nodes, next_nodes)
                        return results
                    else:
                        target_key = str(next_nodes[0])
                        if target_key in nodes:
                            current_index = node_order.index(target_key)
                            continue
                        else:
                            logger.warning(f"跳转目标节点 {target_key} 不存在")
                            current_index += 1
                            continue
                
                current_index += 1
            finally:
                _current_node_id.reset(token)
        
        return None
    
    def _get_node_order(self, nodes: Dict[str, Any]) -> List[str]:
        order = []
        if 'start' in nodes:
            order.append('start')
        
        for key in nodes:
            if key != 'start':
                order.append(key)
        
        return order
    
    def _is_last_node(self, nodes: Dict[str, Any], current_node_key: str, node: Dict) -> bool:
        if node.get('end', False):
            return True
        if node.get('next'):
            return False
        
        node_order = self._get_node_order(nodes)
        
        if not node_order:
            return False
        
        return node_order[-1] == current_node_key
    
    def _parse_node_string(self, node_str: str) -> Optional[Dict]:
        if isinstance(node_str, dict):
            return node_str
        
        try:
            clean_str = node_str.rstrip(';').strip()
            node_json = '{' + clean_str + '}'
            node = json.loads(node_json)
            return node
        except json.JSONDecodeError as e:
            logger.error(f"解析节点失败: {e}, node_str: {node_str}")
            return None
    
    async def _execute_parallel_targets(self, nodes: Dict[str, Any], target_ids: List) -> Dict[str, Any]:
        logger.info(f"开始并行执行 {len(target_ids)} 个分支")
        
        tasks = []
        target_info = []
        
        for target_id in target_ids:
            target_key = str(target_id)
            if target_key in nodes:
                target_info.append(target_id)
                tasks.append(self._execute_from_node(nodes, start_from=target_key))
            else:
                logger.warning(f"并行跳转目标节点未找到: {target_id}")
        
        if not tasks:
            logger.warning("没有有效的并行跳转目标")
            return {}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        parallel_results = {}
        for i, target_id in enumerate(target_info):
            result = results[i]
            if isinstance(result, Exception):
                logger.error(f"并行分支 {target_id} 执行失败: {result}")
                parallel_results[str(target_id)] = {"error": str(result)}
            else:
                parallel_results[str(target_id)] = result
        
        logger.info(f"并行执行完成，结果: {json.dumps(parallel_results, ensure_ascii=False, default=str)}")
        
        return parallel_results
    
    async def _execute_node_async_wrapper(self, node: Dict, timeout: int, node_id: Union[int, str]):
        logger.debug(f"后台执行节点 {node_id}")
        try:
            output = await self._execute_node(node, timeout)
            self.ctx.node_outputs[str(node_id)] = output
            logger.debug(f"后台节点 {node_id} 执行完成，输出类型: {type(output).__name__}")
            
            verbose = node.get('verbose', False)
            if verbose and output is not None:
                verbose_content = "[流式输出]" if hasattr(output, '__aiter__') else output
                self._emit_verbose(verbose_content, node.get('name', '') or str(node_id))
            
            history = node.get('history', False)
            if history and output is not None:
                self.ctx._add_to_history(output)
            
            return output
        except Exception as e:
            logger.error(f"后台节点 {node_id} 执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    async def _execute_node(self, node: Dict, timeout: int = 60, is_last_node: bool = False):
        node_type = node.get('node')
        logger.debug(f"_execute_node: node_type={node_type}, is_last_node={is_last_node}")
        
        if node_type == 'start':
            return self._execute_start_node(node)
        elif node_type == 'model':
            return await self._execute_model_node(node, timeout, is_last_node)
        elif node_type == 'knowledgebase':
            return await self._execute_knowledgebase_node(node)
        elif node_type == 'agent':
            return await self._execute_agent_node(node, is_last_node)
        elif node_type == 'ui':
            return self._execute_ui_node(node)
        
        logger.warning(f"未知节点类型: {node_type}")
        return None
    
    def _execute_start_node(self, node: Dict):
        logger.debug("执行开始节点")
        self.ctx.set("current_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"设置当前时间: {self.ctx.get('current_time')}")
        if 'params' in node:
            params = node['params']
            for param in params:
                param_name = param.get('name')
                param_type = param.get('type', 'str')
                param_value = self._kwargs.get(param_name)
                
                if param_value is None:
                    param_value = param.get('default')
                
                if param_value is not None:
                    param_value = self._convert_param_type(param_value, param_type)
                
                if param_name:
                    self.ctx.set(param_name, param_value)
                    logger.debug(f"设置参数: {param_name}={param_value} (type={param_type})")
        else:
            logger.warning("开始节点没有参数")
        logger.debug(f"开始节点执行完成")
        return {"status": "started"}
    
    def _convert_param_type(self, value: Any, param_type: str) -> Any:
        try:
            return convert_param_type(value, param_type)
        except Exception as e:
            logger.warning(f"参数类型转换失败: {e}")
            return value
    
    async def _execute_model_node(self, node: Dict, timeout: int = 60, is_last_node: bool = False):
        logger.debug(f"执行模型节点: {node.get('id')}, is_last_node={is_last_node}")
        
        model_id = node.get('model_id')
        logger.debug(f"模型ID: {model_id}")
        
        config = self.ctx._get_api_config(model_id)
        
        if not config:
            logger.error("未找到模型配置")
            return {"error": "未找到模型配置，请先配置API"}
        
        logger.debug(f"使用模型配置: id={config.id}, name={config.name}, code={config.code}")
        
        messages = node.get('messages', [])
        processed_messages = []
        
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                if "__expr__" in msg:
                    processed_msg = self.ctx._eval_expression(msg["__expr__"])
                    if isinstance(processed_msg, dict):
                        if "role" in processed_msg:
                            processed_messages.append(processed_msg)
                        else:
                            processed_messages.append({
                                "role": "user",
                                "content": str(processed_msg)
                            })
                    elif isinstance(processed_msg, list):
                        for item in processed_msg:
                            if isinstance(item, dict) and "role" in item:
                                processed_messages.append(item)
                            else:
                                processed_messages.append({
                                    "role": "user",
                                    "content": str(item)
                                })
                    else:
                        processed_messages.append({
                            "role": "user",
                            "content": str(processed_msg)
                        })
                    logger.debug(f"消息[{i}] (表达式): {str(processed_msg)[:100]}...")
                else:
                    content = msg.get('content')
                    if content:
                        content = self.ctx._process_value(content)
                        if not isinstance(content, str):
                            content = str(content)
                    else:
                        content = ""
                    role = msg.get('role', 'user')
                    processed_messages.append({
                        "role": role,
                        "content": content
                    })
                    logger.debug(f"消息[{i}]: role={role}, content={content[:100]}..." if len(str(content)) > 100 else f"消息[{i}]: role={role}, content={content}")
            elif isinstance(msg, str):
                processed_msg = self.ctx._eval_expression(msg)
                if isinstance(processed_msg, dict):
                    if "role" in processed_msg:
                        processed_messages.append(processed_msg)
                    else:
                        processed_messages.append({
                            "role": "user",
                            "content": str(processed_msg)
                        })
                else:
                    processed_messages.append({
                        "role": "user",
                        "content": str(processed_msg)
                    })
                logger.debug(f"消息[{i}] (字符串): {str(processed_msg)[:100]}...")
            else:
                processed_messages.append({
                    "role": "user",
                    "content": str(msg)
                })
                logger.debug(f"消息[{i}] (其他): {str(msg)[:100]}...")
        
        stream = node.get('stream', False)
        verbose = node.get('verbose', True)
        output_format = node.get('output_format', 'text')
        tools = node.get('tools', [])
        enable_search = node.get('enable_search', None)
        
        call_model_id = int(model_id) if model_id is not None else None
        
        if stream and is_last_node:
            if not verbose:
                logger.info(f"节点 {node.get('id')} 是最后一个节点，强制流式输出到前端")
            self._stream_node = str(node.get('id'))
            
            stream_generator = await self.ctx.call_model(
                model_id=call_model_id,
                messages=processed_messages,
                tools=tools,
                enable_search=enable_search,
                stream=True,
                output_format=output_format,
                timeout=timeout
            )
            
            self._stream_generator = self.ctx._wrap_stream_with_history(stream_generator)
            return self._stream_generator
        
        result = await self.ctx.call_model(
            model_id=call_model_id,
            messages=processed_messages,
            tools=tools,
            enable_search=enable_search,
            stream=stream,
            output_format=output_format,
            timeout=timeout
        )
        
        if stream:
            full_content = ""
            stream_gen: AsyncGenerator = result  # type: ignore[assignment]
            async for chunk in stream_gen:
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
                        if verbose and self._verbose_queue:
                            verbose_item = {
                                "content": content,
                                "node_name": node.get('name', '') or str(node.get('id')),
                                "type": "stream_chunk"
                            }
                            self._verbose_queue.put_nowait(verbose_item)
            logger.debug(f"流式响应完成，内容长度: {len(full_content)}")
            if output_format == 'json':
                try:
                    parsed_content = json.loads(full_content) if isinstance(full_content, str) else full_content
                    if isinstance(parsed_content, dict):
                        return DictObject(parsed_content)
                    return parsed_content
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败，返回原始内容: {e}")
                    return full_content
            return full_content
        
        return result
    
    async def _execute_knowledgebase_node(self, node: Dict):
        logger.info(f"执行知识库节点: {node.get('id')}")
        
        baselist = node.get('baselist', [])
        query = node.get('query')
        file_paths = node.get('file_paths', [])
        
        if query:
            query = self.ctx._process_value(query)
            if not isinstance(query, str):
                query = str(query) if query is not None else None
        
        if file_paths and not isinstance(file_paths, list):
            file_paths = [str(self.ctx._process_value(file_paths))]
        else:
            file_paths = [str(self.ctx._process_value(fp)) for fp in file_paths] if file_paths else []
        
        logger.info(f"知识库列表: {baselist}")
        logger.info(f"查询内容: {query}")
        logger.info(f"文件路径: {file_paths}")
        
        fp_list: Optional[List[str]] = file_paths if file_paths else None
        result = await self.ctx.knowledgebase(baselist, query, fp_list)
        
        if isinstance(result, dict) and result.get('context'):
            context_str = str(result.get('context'))
            if len(context_str) > 200:
                logger.info(f"知识库结果: context长度={len(context_str)}, sources={result.get('sources')}")
            else:
                logger.info(f"知识库结果: {result}")
        else:
            logger.info(f"知识库结果: {result}")
        
        output_fields = node.get('output', ['context', 'error', 'sources'])
        
        output_result = {}
        for field in output_fields:
            if field in result:
                output_result[field] = result[field]
        
        return output_result
    
    async def _execute_agent_node(self, node: Dict, is_last_node: bool = False):
        logger.info(f"执行智能体节点: {node.get('id')}")
        
        agent_id = node.get('agent_id')
        agent_type = node.get('agent_type')
        params = node.get('params', {})
        verbose_return = node.get('verbose_return', False)
        
        if not agent_id:
            logger.error("智能体节点没有指定 agent_id")
            return {"error": "智能体节点没有指定 agent_id"}
        
        agent_id = self.ctx._process_value(agent_id)
        if agent_type:
            agent_type = self.ctx._process_value(agent_type)
        params = self.ctx._process_value(params)
        
        if not isinstance(agent_id, (int, str)):
            logger.error(f"agent_id 类型错误: {type(agent_id)}")
            return {"error": f"agent_id 类型错误，应为 int 或 str，实际为 {type(agent_id).__name__}"}
        
        if agent_type is not None and not isinstance(agent_type, str):
            logger.error(f"agent_type 类型错误: {type(agent_type)}")
            return {"error": f"agent_type 类型错误，应为 str 或 None，实际为 {type(agent_type).__name__}"}
        
        logger.info(f"调用智能体: agent_id={agent_id}, agent_type={agent_type}, verbose_return={verbose_return}")
        logger.debug(f"智能体参数: {params}")
        
        query = self._kwargs.get("input_data") or self._kwargs.get("query") or ""
        
        call_kwargs = {"query": query}
        if isinstance(params, dict):
            call_kwargs.update(params)
        
        result = await self.ctx.call_agent(
            agent_id=agent_id,
            agent_type=agent_type,
            verbose_return=verbose_return,
            **call_kwargs
        )
        
        logger.info(f"智能体节点执行完成: {node.get('id')}, 结果类型: {type(result).__name__}")
        
        return result
    
    def _execute_ui_node(self, node: Dict):
        """
        执行UI节点，返回UI配置
        
        UI节点的显示一定在最后，此方法收集所有UI元素并返回配置
        """
        logger.info(f"执行UI节点: {node.get('id')}")
        
        default_layout = {
            "direction": "column",
            "gap": "16px",
            "padding": "12px"
        }
        
        ui_config = {
            "type": "ui",
            "node_id": node.get('id'),
            "name": node.get('name', ''),
            "buttons": [],
            "charts": [],
            "modals": [],
            "layout": node.get('layout', default_layout),
            "show_in_modal": node.get('show_in_modal', False)
        }
        
        node_buttons = node.get('buttons', [])
        for btn in node_buttons:
            processed_btn = self.ctx._process_value(btn)
            ui_config["buttons"].append(processed_btn)
        
        node_charts = node.get('charts', [])
        for chart in node_charts:
            processed_chart = self.ctx._process_value(chart)
            ui_config["charts"].append(processed_chart)
        
        node_modals = node.get('modals', [])
        for modal in node_modals:
            processed_modal = self.ctx._process_value(modal)
            ui_config["modals"].append(processed_modal)
        
        dynamic_ui = self.ctx.get_ui_elements()
        
        for btn in dynamic_ui.get("buttons", []):
            btn_copy = btn.copy()
            btn_copy.pop("type", None)
            ui_config["buttons"].append(btn_copy)
        
        for chart in dynamic_ui.get("charts", []):
            chart_copy = chart.copy()
            chart_copy.pop("type", None)
            if "chart_type" in chart_copy:
                chart_copy["type"] = chart_copy.pop("chart_type")
            ui_config["charts"].append(chart_copy)
        
        for modal in dynamic_ui.get("modals", []):
            modal_copy = modal.copy()
            modal_copy.pop("type", None)
            ui_config["modals"].append(modal_copy)
        
        logger.info(f"UI节点配置: buttons={len(ui_config['buttons'])}, charts={len(ui_config['charts'])}, modals={len(ui_config['modals'])}")
        
        return ui_config
    
    async def _execute_code_block(self, code_block: str):
        logger.debug(f"执行代码块: {code_block[:100]}..." if len(code_block) > 100 else f"执行代码块: {code_block}")
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
        except ImportError:
            plt = None
        
        local_vars = {
            'ctx': self.ctx,
            'memory': self.memory,
            'logger': logger,
            'workflow_logger': self.workflow_logger
        }
        
        if plt:
            local_vars['plt'] = plt
        
        global_vars = {"__builtins__": __builtins__}
        global_vars.update(local_vars)
        
        wrapped_code = "async def __async_exec__():\n" + "\n".join("    " + line if line.strip() else "" for line in code_block.split("\n"))
        
        try:
            exec(wrapped_code, global_vars, local_vars)
            await local_vars['__async_exec__']()
        except GotoExit as e:
            logger.info(f"代码块触发 goto 跳转: {e}")
            self.workflow_logger.info(f"代码块触发 goto 跳转: {e}")
        except FinalReturnExit as e:
            logger.info(f"代码块触发 final_return: {e}")
            self.workflow_logger.info(f"代码块触发 final_return: {e}")
        except Exception as e:
            logger.error(f"代码执行错误: {e}")
            self.workflow_logger.error(f"代码执行错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def get_verbose_outputs(self) -> List[Dict]:
        ctx_verbose = self.ctx.get_verbose_outputs()
        return self.verbose_outputs + ctx_verbose
