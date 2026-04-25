import codecs
import httpx
from kuakua_agent.config import settings
from kuakua_agent.services.memory import PreferenceStore


class ModelAdapter:
    def __init__(self):
        pref = PreferenceStore()
        self.base_url = settings.ark_base_url
        self.api_key = pref.get("model_api_key") or settings.ark_api_key
        self.model_id = settings.ark_model_id

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
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
        with httpx.Client(timeout=120.0) as client:
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
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
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
        async with httpx.AsyncClient(timeout=120.0) as client:
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
                            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

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
