import codecs
import time
import httpx
from kuakua_agent.config import settings
from kuakua_agent.core.logging import get_logger
from kuakua_agent.services.memory import PreferenceStore

logger = get_logger(__name__)


class ModelAdapter:
    def __init__(self):
        pref = PreferenceStore()
        self.base_url = settings.llm_base_url.rstrip("/")
        raw_key = pref.get_sync("model_api_key") or settings.llm_api_key
        self.api_key = raw_key.strip() if raw_key else ""
        if not self.api_key:
            raise ValueError("API key is not configured. Please set LLM_API_KEY or model_api_key.")
        self.model_id = settings.llm_model_id.strip()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        started = time.perf_counter()
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "llm_complete_finished",
            extra={
                "module_name": "llm",
                "event": "complete",
                "duration_ms": duration_ms,
                "model_id": self.model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    def stream_complete(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500):
        """流式生成，返回可迭代对象"""
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        with httpx.Client(timeout=settings.llm_timeout_seconds * 2) as client:
            with client.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=payload) as response:
                if response.status_code != 200:
                    raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        import json
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def complete_async(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        started = time.perf_counter()
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
        duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "llm_complete_async_finished",
            extra={
                "module_name": "llm",
                "event": "complete_async",
                "duration_ms": duration_ms,
                "model_id": self.model_id,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        if response.status_code != 200:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    async def stream_complete_async(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500):
        """异步流式生成，返回可迭代对象，逐字产出无缓冲"""
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds * 2) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=payload) as response:
                if response.status_code != 200:
                    raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
                buffer = b""

                async for raw_bytes in response.aiter_bytes(chunk_size=64):
                    if not raw_bytes:
                        continue
                    buffer += raw_bytes

                    # 尝试解析完整的 data: 开头的行
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            decoded_line = line.decode("utf-8")
                        except UnicodeDecodeError:
                            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
                            decoded_line = decoder.decode(line)

                        if not decoded_line.startswith("data: "):
                            continue
                        data = decoded_line[6:]
                        if data == "[DONE]":
                            return
                        import json as _json
                        try:
                            chunk = _json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except _json.JSONDecodeError:
                            continue
