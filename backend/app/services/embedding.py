import httpx
import logging
from typing import List, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(
        self,
        api_key: str,
        url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-ada-002",
        call_type: str = "OpenAI Chat",
        client: Optional[httpx.AsyncClient] = None
    ):
        self.api_key = api_key
        self.url = url.rstrip("/")
        self.model = model
        self.call_type = call_type
        self._external_client = client
    
    def _get_client(self) -> httpx.AsyncClient:
        """获取httpx客户端"""
        if self._external_client:
            return self._external_client
        raise RuntimeError("No httpx client available. Provide a client or use within an async context with a client.")
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        if not text or not text.strip():
            return None
        
        if self.call_type == "DashScope SDK":
            return await self._get_embedding_dashscope(text)
        else:
            return await self._get_embedding_openai(text)
    
    async def _get_embedding_openai(self, text: str) -> Optional[List[float]]:
        try:
            if self.url.endswith("/v1"):
                api_url = f"{self.url}/embeddings"
            elif self.url.endswith("com"):
                api_url = f"{self.url}/v1/embeddings"
            else:
                api_url = f"{self.url}"
            
            if self._external_client:
                client = self._external_client
                return await self._do_embedding_request(client, api_url, text)
            else:
                async with httpx.AsyncClient() as client:
                    return await self._do_embedding_request(client, api_url, text)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    async def _do_embedding_request(self, client: httpx.AsyncClient, api_url: str, text: str) -> Optional[List[float]]:
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "input": text
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"][0]["embedding"]
        else:
            logger.error(f"Embedding API error: {response.status_code} - {response.text}")
            return None
    
    async def _get_embedding_dashscope(self, text: str) -> Optional[List[float]]:
        try:
            import dashscope
            from dashscope import MultiModalEmbedding
            
            dashscope.api_key = self.api_key
            
            input_data: List[dict[str, str]] = [{'text': text}]
            
            resp = MultiModalEmbedding.call(
                model=self.model,
                input=input_data  # type: ignore[arg-type]
            )
            
            if resp.status_code == 200:
                embedding = resp.output['embeddings'][0]['embedding']
                return embedding
            else:
                logger.error(f"DashScope Embedding API error: {resp.status_code} - {resp.message}")
                return None
        except ImportError:
            logger.error("dashscope package not installed. Run: pip install dashscope")
            return None
        except Exception as e:
            logger.error(f"Error getting embedding from DashScope: {e}")
            return None
    
    async def get_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        if not texts:
            return []
        
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return [None] * len(texts)
        
        if self.call_type == "DashScope SDK":
            return await self._get_embeddings_dashscope(valid_texts)
        else:
            return await self._get_embeddings_openai(valid_texts)
    
    async def _get_embeddings_openai(self, texts: List[str]) -> List[Optional[List[float]]]:
        try:
            if self.url.endswith("/v1"):
                api_url = f"{self.url}/embeddings"
            elif self.url.endswith("com"):
                api_url = f"{self.url}/v1/embeddings"
            else:
                api_url = f"{self.url}"
            
            if self._external_client:
                client = self._external_client
                return await self._do_embeddings_request(client, api_url, texts)
            else:
                async with httpx.AsyncClient() as client:
                    return await self._do_embeddings_request(client, api_url, texts)
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return [None] * len(texts)
    
    async def _do_embeddings_request(self, client: httpx.AsyncClient, api_url: str, texts: List[str]) -> List[Optional[List[float]]]:
        response = await client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "input": texts
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            embeddings = {i: item["embedding"] for i, item in enumerate(data["data"])}
            return [embeddings.get(i) for i in range(len(texts))]
        else:
            logger.error(f"Embedding API error: {response.status_code} - {response.text}")
            return [None] * len(texts)
    
    async def _get_embeddings_dashscope(self, texts: List[str]) -> List[Optional[List[float]]]:
        try:
            import dashscope
            from dashscope import MultiModalEmbedding
            
            dashscope.api_key = self.api_key
            
            results: List[Optional[List[float]]] = []
            for text in texts:
                input_data: List[dict[str, str]] = [{'text': text}]
                
                resp = MultiModalEmbedding.call(
                    model=self.model,
                    input=input_data  # type: ignore[arg-type]
                )
                
                if resp.status_code == 200:
                    embedding = resp.output['embeddings'][0]['embedding']
                    results.append(embedding)
                else:
                    logger.error(f"DashScope Embedding API error for text: {resp.status_code} - {resp.message}")
                    results.append(None)
            
            return results
        except ImportError:
            logger.error("dashscope package not installed. Run: pip install dashscope")
            return [None] * len(texts)
        except Exception as e:
            logger.error(f"Error getting embeddings from DashScope: {e}")
            return [None] * len(texts)
