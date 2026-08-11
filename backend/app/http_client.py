import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class HTTPClientManager:
    """HTTP客户端管理器，使用连接池复用httpx.AsyncClient实例"""
    
    def __init__(
        self,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        timeout: float = 60.0,
        keepalive_expiry: float = 5.0
    ):
        self._client: Optional[httpx.AsyncClient] = None
        self._max_connections = max_connections
        self._max_keepalive_connections = max_keepalive_connections
        self._timeout = timeout
        self._keepalive_expiry = keepalive_expiry
    
    async def init(self):
        """初始化HTTP客户端连接池"""
        limits = httpx.Limits(
            max_connections=self._max_connections,
            max_keepalive_connections=self._max_keepalive_connections,
            keepalive_expiry=self._keepalive_expiry
        )
        timeout = httpx.Timeout(
            connect=10.0,
            read=self._timeout,
            write=self._timeout,
            pool=self._timeout
        )
        transport = httpx.AsyncHTTPTransport(
            retries=1,
            limits=limits
        )
        self._client = httpx.AsyncClient(
            transport=transport,
            timeout=timeout,
            http2=False,
            follow_redirects=True
        )
        logger.info(
            f"HTTP client pool initialized: "
            f"max_connections={self._max_connections}, "
            f"max_keepalive={self._max_keepalive_connections}"
        )
    
    @property
    def client(self) -> httpx.AsyncClient:
        """获取HTTP客户端实例"""
        if self._client is None:
            raise RuntimeError("HTTP client not initialized. Call init() first.")
        return self._client
    
    async def close(self):
        """关闭HTTP客户端连接池"""
        if self._client:
            try:
                await self._client.aclose()
                logger.info("HTTP client pool closed")
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    logger.warning("HTTP client close skipped: event loop already closed")
                else:
                    raise
            finally:
                self._client = None


http_client_manager = HTTPClientManager()
