import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from app.services.workflow.executor import WorkflowExecutor
from app.services.workflow.context import WorkflowContext, Memory


class TestWorkflowExecutor:
    """WorkflowExecutor 单元测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def executor(self, mock_db):
        """创建 WorkflowExecutor 实例"""
        return WorkflowExecutor(db=mock_db, user_id=1)

    @pytest.fixture
    def simple_nodes(self):
        """简单的节点列表"""
        return [
            {"id": "start", "node": "start"},
            {"id": "node1", "node": "model", "model_id": 1, "messages": [{"role": "user", "content": "hello"}]},
        ]

    @pytest.fixture
    def parallel_nodes(self):
        """包含并行跳转的节点列表"""
        return [
            {"id": "start", "node": "start"},
            {"id": "node1", "node": "model", "next": ["node2", "node3"]},
            {"id": "node2", "node": "model"},
            {"id": "node3", "node": "model"},
        ]

    @pytest.mark.asyncio
    async def test_executor_init(self, executor):
        """测试执行器初始化"""
        assert executor.db is not None
        assert executor.user_id == 1
        assert executor.ctx is not None
        assert executor.memory is not None
        assert isinstance(executor.ctx, WorkflowContext)
        assert isinstance(executor.memory, Memory)

    @pytest.mark.asyncio
    async def test_execute_start_node(self, executor):
        """测试执行开始节点"""
        nodes = [{"id": "start", "node": "start"}]
        
        with patch.object(executor, '_execute_start_node', return_value={"status": "started"}) as mock_start:
            result = await executor.execute(nodes, input_data="test input")
            
            mock_start.assert_called_once()
            assert executor.ctx.get("input") == "test input"

    @pytest.mark.asyncio
    async def test_execute_with_params(self, executor):
        """测试带参数的执行"""
        nodes = [
            {
                "id": "start",
                "node": "start",
                "params": [
                    {"name": "input", "default": "default_value"},
                    {"name": "custom_param", "default": "custom_value"}
                ]
            }
        ]
        
        result = await executor.execute(nodes, input_data="user_input")
        
        assert executor.ctx.get("input") == "user_input"
        assert executor.ctx.get("custom_param") == "custom_value"

    @pytest.mark.asyncio
    async def test_process_variables(self, executor):
        """测试变量处理"""
        executor.ctx.set("test_var", "test_value")
        executor.ctx.set("input", "user_input")
        
        text = "ctx.get('test_var') and ctx.input"
        result = executor._process_variables(text)
        
        assert "test_value" in result
        assert "user_input" in result

    @pytest.mark.asyncio
    async def test_find_node_by_id(self, executor):
        """测试查找节点"""
        nodes = [
            {"id": "node1", "name": "First Node"},
            {"id": "node2", "name": "Second Node"},
        ]
        
        found = executor._find_node_by_id(nodes, "node1")
        assert found["id"] == "node1"
        
        found = executor._find_node_by_id(nodes, "Second Node")
        assert found["id"] == "node2"
        
        not_found = executor._find_node_by_id(nodes, "nonexistent")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_eval_expression(self, executor):
        """测试表达式求值"""
        executor.ctx.set("num", 10)
        
        result = executor._eval_expression("self.ctx.get('num') + 5")
        assert result == 15

    @pytest.mark.asyncio
    async def test_add_to_history(self, executor):
        """测试添加到历史记录"""
        executor._add_to_history("test message")
        
        assert len(executor.memory.history) == 1
        assert executor.memory.history[0]["role"] == "assistant"
        assert executor.memory.history[0]["content"] == "test message"

    @pytest.mark.asyncio
    async def test_add_dict_to_history(self, executor):
        """测试添加字典到历史记录"""
        data = {"key": "value", "number": 123}
        executor._add_to_history(data)
        
        assert len(executor.memory.history) == 1
        assert '"key": "value"' in executor.memory.history[0]["content"]

    @pytest.mark.asyncio
    async def test_get_verbose_outputs(self, executor):
        """测试获取详细输出"""
        executor.verbose_outputs = [
            {"node_id": "node1", "node_name": "Test", "output": "result"}
        ]
        
        outputs = executor.get_verbose_outputs()
        assert len(outputs) == 1
        assert outputs[0]["node_id"] == "node1"


class TestWorkflowContext:
    """WorkflowContext 单元测试"""

    @pytest.fixture
    def context(self):
        """创建 WorkflowContext 实例"""
        return WorkflowContext(db=None, user_id=1)

    def test_context_set_get(self, context):
        """测试上下文变量存取"""
        context.set("key", "value")
        assert context.get("key") == "value"
        assert context.get("nonexistent") is None

    def test_context_node_output(self, context):
        """测试节点输出存储"""
        context.node_outputs["node1"] = "output1"
        context.node_outputs["node2"] = "output2"
        
        assert context.output("node1") == "output1"
        
        # 测试多节点输出
        result = context.output(["node1", "node2"])
        assert result == {"node1": "output1", "node2": "output2"}
        
        # 测试 list 模式
        result = context.output(["node1", "node2"], join_mode="list")
        assert result == ["output1", "output2"]
        
        # 测试 str 模式
        result = context.output(["node1", "node2"], join_mode="str")
        assert "output1" in result
        assert "output2" in result

    def test_context_goto(self, context):
        """测试跳转功能"""
        # 测试单次跳转
        result = context.goto("node1")
        assert result is True
        assert context.get_goto_targets() == ["node1"]
        
        context.clear_goto_targets()
        assert context.get_goto_targets() == []

    def test_context_goto_multiple(self, context):
        """测试多目标跳转"""
        result = context.goto("node1", "node2", "node3")
        assert result is True
        assert context.get_goto_targets() == ["node1", "node2", "node3"]

    def test_context_goto_loop_protection(self, context):
        """测试循环保护"""
        # 模拟达到最大循环次数
        context._loop_counts["node1"] = 10
        result = context.goto("node1", max_loops=10)
        assert result is False

    def test_context_final_return(self, context):
        """测试最终返回"""
        context.final_return("final result", history=True)
        
        assert context.should_return() is True
        assert context.get_final_result() == "final result"
        assert context.is_history_enabled() is True

    def test_context_loop_count(self, context):
        """测试循环计数"""
        assert context.get_loop_count("node1") == 0
        
        context.increment_loop_count("node1")
        assert context.get_loop_count("node1") == 1
        
        context.increment_loop_count("node1")
        assert context.get_loop_count("node1") == 2


class TestMemory:
    """Memory 单元测试"""

    @pytest.fixture
    def memory(self):
        """创建 Memory 实例"""
        return Memory()

    def test_memory_set_get(self, memory):
        """测试记忆存取"""
        memory.set("key", "value")
        assert memory.get("key") == "value"
        assert memory.get("nonexistent") is None

    def test_memory_editable(self, memory):
        """测试可编辑标记"""
        memory.set("editable_key", "value", is_editable=True)
        memory.set("readonly_key", "value", is_editable=False)
        
        assert memory._editable["editable_key"] is True
        assert memory._editable["readonly_key"] is False

    def test_memory_history(self, memory):
        """测试历史记录"""
        memory.history.append({"role": "user", "content": "hello"})
        assert len(memory.history) == 1
        assert memory.history[0]["role"] == "user"


class TestParallelExecution:
    """并行执行功能测试"""

    @pytest.fixture
    def executor(self):
        """创建 WorkflowExecutor 实例"""
        return WorkflowExecutor(db=None, user_id=1)

    @pytest.mark.asyncio
    async def test_parallel_goto_execution(self, executor):
        """测试并行跳转执行"""
        nodes = [
            {"id": "start", "node": "start"},
            {"id": "branch_a", "node": "model"},
            {"id": "branch_b", "node": "model"},
        ]
        
        # 模拟执行分支
        with patch.object(executor, '_execute_node', new_callable=AsyncMock) as mock_execute:
            mock_execute.side_effect = [
                "result_a",  # branch_a
                "result_b",  # branch_b
            ]
            
            result = await executor._execute_parallel_targets(
                nodes, ["branch_a", "branch_b"], set()
            )
            
            assert "branch_a" in result
            assert "branch_b" in result

    @pytest.mark.asyncio
    async def test_parallel_execution_with_exception(self, executor):
        """测试并行执行异常处理"""
        nodes = [
            {"id": "node1", "node": "model"},
            {"id": "node2", "node": "model"},
        ]
        
        async def mock_execute(node, timeout=60):
            if node["id"] == "node1":
                return "success"
            raise Exception("Test error")
        
        with patch.object(executor, '_execute_node', side_effect=mock_execute):
            result = await executor._execute_parallel_targets(
                nodes, ["node1", "node2"], set()
            )
            
            assert result["node1"] == "success"
            assert "error" in result["node2"]

    @pytest.mark.asyncio
    async def test_parallel_execution_invalid_target(self, executor):
        """测试并行执行无效目标"""
        nodes = [{"id": "node1", "node": "model"}]
        
        result = await executor._execute_parallel_targets(
            nodes, ["nonexistent"], set()
        )
        
        assert result == {}


class TestCodeBlockExecution:
    """代码块执行测试"""

    @pytest.fixture
    def executor(self):
        """创建 WorkflowExecutor 实例"""
        return WorkflowExecutor(db=None, user_id=1)

    def test_execute_code_block_set_variable(self, executor):
        """测试代码块设置变量"""
        code = "ctx.set('test_key', 'test_value')"
        executor._execute_code_block(code)
        
        assert executor.ctx.get("test_key") == "test_value"

    def test_execute_code_block_memory(self, executor):
        """测试代码块操作记忆"""
        code = "memory.set('mem_key', 'mem_value')"
        executor._execute_code_block(code)
        
        assert executor.memory.get("mem_key") == "mem_value"

    def test_execute_code_block_goto(self, executor):
        """测试代码块跳转"""
        code = "ctx.goto('target_node')"
        executor._execute_code_block(code)
        
        assert executor.ctx.get_goto_targets() == ["target_node"]

    def test_execute_code_block_final_return(self, executor):
        """测试代码块最终返回"""
        code = "ctx.final_return('final result')"
        executor._execute_code_block(code)
        
        assert executor.ctx.should_return() is True
        assert executor.ctx.get_final_result() == "final result"

    def test_execute_code_block_error(self, executor):
        """测试代码块执行错误"""
        code = "invalid_python_syntax!!!"
        
        # 不应该抛出异常，而是记录错误
        executor._execute_code_block(code)
        # 如果执行到这里，说明异常被正确处理了


class TestHTTPMethod:
    """HTTP 方法测试"""

    @pytest.fixture
    def context(self):
        """创建 WorkflowContext 实例"""
        return WorkflowContext(db=None, user_id=1)

    @pytest.mark.asyncio
    async def test_http_get(self, context):
        """测试 HTTP GET 请求"""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"result": "ok"}'
            mock_response.headers = {"content-type": "application/json"}
            
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=None)
            mock_client.return_value.get.return_value = mock_response
            
            status, text, headers = context.http("https://api.example.com/test")
            
            assert status == 200
            assert text == '{"result": "ok"}'

    @pytest.mark.asyncio
    async def test_http_post(self, context):
        """测试 HTTP POST 请求"""
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.text = "created"
            mock_response.headers = {}
            
            mock_client.return_value.__enter__ = Mock(return_value=mock_client.return_value)
            mock_client.return_value.__exit__ = Mock(return_value=None)
            mock_client.return_value.post.return_value = mock_response
            
            status, text, headers = context.http(
                "https://api.example.com/test",
                method="POST",
                headers={"Authorization": "Bearer token"},
                body='{"data": "value"}'
            )
            
            assert status == 201
            assert text == "created"

    @pytest.mark.asyncio
    async def test_http_error(self, context):
        """测试 HTTP 错误处理"""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__ = Mock(side_effect=Exception("Connection error"))
            
            status, text, headers = context.http("https://api.example.com/test")
            
            assert status == 500
            assert "Connection error" in text
