import sys
import logging
import signal
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, dispose_engine
from app.http_client import http_client_manager
from app.logging_config import setup_logging
from app.routers import (
    auth_router,
    api_config_router,
    chat_router,
    conversation_router,
    agent_router,
    file_router,
    knowledge_base_router,
    test_case_router,
    test_chat_router,
    workflow_agent_router,
    unified_agent_chat_router,
    code_tool_router,
    workflow_test_router,
    workflow_ai_router,
    functional_model_router,
    rag_router,
    rag_chat_router,
    workflow_files_router
)

setup_logging()
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    await http_client_manager.init()
    try:
        yield
    finally:
        logger.info("Application shutting down...")
        await http_client_manager.close()
        dispose_engine()
        logger.info("Cleanup complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="shwsq's aiagent后端API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(api_config_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(functional_model_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(knowledge_base_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(rag_chat_router, prefix="/api")
app.include_router(test_case_router, prefix="/api")
app.include_router(test_chat_router, prefix="/api")
app.include_router(workflow_agent_router, prefix="/api")
app.include_router(unified_agent_chat_router, prefix="/api")
app.include_router(code_tool_router, prefix="/api")
app.include_router(workflow_files_router, prefix="/api")
app.include_router(workflow_test_router, prefix="/api")
app.include_router(workflow_ai_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "shwsq's aiagent API", "version": settings.APP_VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        timeout_graceful_shutdown=5
    )
