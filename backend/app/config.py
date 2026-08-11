from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

ENV_FILE_PATH = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "shwsq's aiagent API"
    APP_VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/agent_test"
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    
    CORS_ORIGINS: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略未定义的环境变量
        case_sensitive = False  # 环境变量名不区分大小写
    
    @property
    def database_type(self) -> str:
        if self.DATABASE_URL.startswith("postgresql"):
            return "postgresql"
        elif self.DATABASE_URL.startswith("mysql"):
            return "mysql"
        return "unknown"
    
    @property
    def is_postgresql(self) -> bool:
        return self.database_type == "postgresql"
    
    @property
    def is_mysql(self) -> bool:
        return self.database_type == "mysql"


settings = Settings()
