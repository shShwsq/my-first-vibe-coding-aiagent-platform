from typing import Any

from sqlalchemy import create_engine, event, text, exc
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings
import logging

logger = logging.getLogger(__name__)

engine_kwargs: dict[str, Any] = {
    "pool_pre_ping": True,
    "echo": False,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_size": 5,
    "max_overflow": 10,
}

if settings.is_mysql:
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["connect_args"] = {
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30
    }
elif settings.is_postgresql:
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_reset_on_return"] = "rollback"
    engine_kwargs["pool_use_lifo"] = True
    engine_kwargs["connect_args"] = {
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "options": "-c statement_timeout=60000 -c lock_timeout=10000 -c idle_in_transaction_session_timeout=60000"
    }

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

if settings.is_postgresql:
    @event.listens_for(engine, "connect")
    def set_timezone(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET TIME ZONE 'UTC'")
            dbapi_connection.commit()
        except Exception as e:
            dbapi_connection.rollback()
            logger.warning(f"Could not set timezone: {e}")
        finally:
            cursor.close()
    
    @event.listens_for(engine, "connect")
    def setup_pgvector(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            dbapi_connection.commit()
        except Exception as e:
            dbapi_connection.rollback()
            logger.warning(f"Could not create pgvector extension: {e}")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """
    创建一个短生命周期的数据库会话，用于非请求上下文中的数据库操作
    
    使用示例:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseSessionManager:
    """
    数据库会话管理器，用于在长时间运行的任务中管理数据库会话
    
    使用示例:
        manager = DatabaseSessionManager()
        
        # 在需要数据库操作时
        with manager.session() as db:
            user = db.query(User).first()
        
        # 会话会在 with 块结束后自动关闭
    """
    
    @staticmethod
    def get_session():
        """获取一个新的数据库会话"""
        return SessionLocal()
    
    @staticmethod
    def release_session(db: Session):
        """释放数据库会话"""
        if db:
            db.close()


def dispose_engine():
    logger.info("Disposing database engine...")
    engine.dispose()
    logger.info("Database engine disposed.")
