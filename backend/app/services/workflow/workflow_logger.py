import logging
import json
from datetime import datetime
from typing import Optional, List
from queue import Queue
from threading import Lock

from app.database import SessionLocal
from app.models.workflow_log import WorkflowLog


class DatabaseLogHandler(logging.Handler):
    """将日志写入数据库的 Handler"""
    
    def __init__(self, user_id: Optional[int], agent_id: Optional[int] = None):
        super().__init__()
        self.user_id = user_id
        self.agent_id = agent_id
        self._buffer: List[dict] = []
        self._lock = Lock()
    
    def emit(self, record: logging.LogRecord):
        try:
            log_entry = {
                "user_id": self.user_id,
                "agent_id": self.agent_id,
                "level": record.levelname,
                "message": self.format(record),
                "node_id": getattr(record, "node_id", None),
                "node_type": getattr(record, "node_type", None),
                "extra_data": getattr(record, "extra_data", None),
                "created_at": datetime.fromtimestamp(record.created)
            }
            
            with self._lock:
                self._buffer.append(log_entry)
        except Exception:
            self.handleError(record)
    
    def flush_to_db(self):
        """将缓冲区的日志写入数据库"""
        with self._lock:
            if not self._buffer:
                return
            
            logs_to_write = self._buffer.copy()
            self._buffer.clear()
        
        db = SessionLocal()
        try:
            for log_entry in logs_to_write:
                log = WorkflowLog(
                    user_id=log_entry["user_id"],
                    agent_id=log_entry["agent_id"],
                    level=log_entry["level"],
                    message=log_entry["message"],
                    node_id=log_entry["node_id"],
                    node_type=log_entry["node_type"],
                    extra_data=log_entry["extra_data"],
                    created_at=log_entry["created_at"]
                )
                db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Failed to flush logs to database: {e}")
        finally:
            db.close()


class WorkflowLogger:
    """工作流日志记录器"""
    
    def __init__(self, user_id: Optional[int], agent_id: Optional[int] = None):
        self.user_id = user_id
        self.agent_id = agent_id
        
        self.logger = logging.getLogger(f"workflow.{user_id}.{agent_id or 'default'}")
        self.logger.setLevel(logging.DEBUG)
        
        self.db_handler = DatabaseLogHandler(user_id, agent_id)
        self.db_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(message)s')
        self.db_handler.setFormatter(formatter)
        
        if self.db_handler not in self.logger.handlers:
            self.logger.addHandler(self.db_handler)
        
        self._current_node_id: Optional[str] = None
        self._current_node_type: Optional[str] = None
    
    def set_node_context(self, node_id: Optional[str], node_type: Optional[str] = None):
        """设置当前节点上下文"""
        self._current_node_id = node_id
        self._current_node_type = node_type
    
    def _log(self, level: str, message: str, extra_data: Optional[dict] = None):
        """内部日志方法"""
        extra = {}
        if self._current_node_id:
            extra["node_id"] = self._current_node_id
        if self._current_node_type:
            extra["node_type"] = self._current_node_type
        if extra_data:
            extra["extra_data"] = json.dumps(extra_data, ensure_ascii=False)
        
        log_record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.upper()),
            "",
            0,
            message,
            (),
            None
        )
        for key, value in extra.items():
            setattr(log_record, key, value)
        
        self.logger.handle(log_record)
    
    def debug(self, message: str, extra_data: Optional[dict] = None):
        self._log("DEBUG", message, extra_data)
    
    def info(self, message: str, extra_data: Optional[dict] = None):
        self._log("INFO", message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[dict] = None):
        self._log("WARNING", message, extra_data)
    
    def error(self, message: str, extra_data: Optional[dict] = None):
        self._log("ERROR", message, extra_data)
    
    def critical(self, message: str, extra_data: Optional[dict] = None):
        self._log("CRITICAL", message, extra_data)
    
    def flush(self):
        """将日志写入数据库"""
        self.db_handler.flush_to_db()
    
    def close(self):
        """关闭日志记录器"""
        self.flush()
        self.logger.removeHandler(self.db_handler)
