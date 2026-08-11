from app.routers.auth import router as auth_router
from app.routers.api_config import router as api_config_router
from app.routers.chat import router as chat_router
from app.routers.conversation import router as conversation_router
from app.routers.agent import router as agent_router
from app.routers.file import router as file_router
from app.routers.knowledge_base import router as knowledge_base_router
from app.routers.test_case import router as test_case_router
from app.routers.test_chat import router as test_chat_router
from app.routers.workflow_agent import router as workflow_agent_router
from app.routers.unified_agent_chat import router as unified_agent_chat_router
from app.routers.code_tool import router as code_tool_router
from app.routers.workflow_test import router as workflow_test_router
from app.routers.workflow_ai import router as workflow_ai_router
from app.routers.functional_model import router as functional_model_router
from app.routers.rag import router as rag_router
from app.routers.rag_chat import router as rag_chat_router
from app.routers.workflow_files import router as workflow_files_router

__all__ = [
    "auth_router",
    "api_config_router",
    "chat_router",
    "conversation_router",
    "agent_router",
    "file_router",
    "knowledge_base_router",
    "test_case_router",
    "test_chat_router",
    "workflow_agent_router",
    "unified_agent_chat_router",
    "code_tool_router",
    "workflow_test_router",
    "workflow_ai_router",
    "functional_model_router",
    "rag_router",
    "rag_chat_router",
    "workflow_files_router"
]
