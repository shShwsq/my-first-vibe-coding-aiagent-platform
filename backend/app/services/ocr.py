import base64
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(
        self,
        api_key: str,
        url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        call_type: str = "OpenAI Chat"
    ):
        self.api_key = api_key
        self.url = url.rstrip("/")
        self.model = model
        self.call_type = call_type

    async def extract_text_from_image(self, image_data: bytes, image_format: str = "jpeg") -> str:
        try:
            base64_image = base64.b64encode(image_data).decode("utf-8")
            mime_type = self._get_mime_type(image_format)

            if self.call_type == "OpenAI Chat" or self.call_type == "OpenAI Responses":
                return await self._call_openai_vision(base64_image, mime_type)
            elif self.call_type == "DashScope SDK":
                return await self._call_dashscope_vision(base64_image, mime_type)
            elif self.call_type == "Anthropic":
                return await self._call_anthropic_vision(base64_image, mime_type)
            else:
                return await self._call_openai_vision(base64_image, mime_type)
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    async def _call_openai_vision(self, base64_image: str, mime_type: str) -> str:
        try:
            if self.url.endswith("/v1"):
                api_url = f"{self.url}/chat/completions"
            elif self.url.endswith("com"):
                api_url = f"{self.url}/v1/chat/completions"
            else:
                api_url = f"{self.url}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "请提取图片中的所有文字内容，保持原有的排版顺序。如果图片中没有文字，请回复'图片中无文字内容'。"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "max_tokens": 4000,
                        "stream": False,
                        "enable_thinking": False
                    },
                    timeout=120.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OCR API error: {response.status_code} - {response.text}")
                    return ""
        except Exception as e:
            logger.error(f"Error calling OpenAI vision API: {e}")
            return ""

    async def _call_dashscope_vision(self, base64_image: str, mime_type: str) -> str:
        try:
            if self.url.endswith("/v1"):
                api_url = f"{self.url}/services/aigc/multimodal-generation/generation"
            elif self.url.endswith("com"):
                api_url = f"{self.url}/v1/services/aigc/multimodal-generation/generation"
            else:
                api_url = f"{self.url}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-OssResourceResolve": "enable"
                    },
                    json={
                        "model": self.model,
                        "input": {
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"text": "请提取图片中的所有文字内容，保持原有的排版顺序。如果图片中没有文字，请回复'图片中无文字内容'。"},
                                        {"image": f"data:{mime_type};base64,{base64_image}"}
                                    ]
                                }
                            ]
                        },
                        "enable_thinking": False
                    },
                    timeout=120.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["output"]["choices"][0]["message"]["content"][0]["text"]
                else:
                    logger.error(f"DashScope OCR API error: {response.status_code} - {response.text}")
                    return ""
        except Exception as e:
            logger.error(f"Error calling DashScope vision API: {e}")
            return ""

    async def _call_anthropic_vision(self, base64_image: str, mime_type: str) -> str:
        try:
            if self.url.endswith("/v1"):
                api_url = f"{self.url}/messages"
            else:
                api_url = f"{self.url}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers={
                        "x-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4000,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "请提取图片中的所有文字内容，保持原有的排版顺序。如果图片中没有文字，请回复'图片中无文字内容'。"
                                    },
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": mime_type,
                                            "data": base64_image
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    timeout=120.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"Anthropic OCR API error: {response.status_code} - {response.text}")
                    return ""
        except Exception as e:
            logger.error(f"Error calling Anthropic vision API: {e}")
            return ""

    def _get_mime_type(self, image_format: str) -> str:
        format_map = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp"
        }
        return format_map.get(image_format.lower(), "image/jpeg")
