import codecs
import json
import time
import httpx
from kuakua_agent.config import settings
from kuakua_agent.core.logging import get_logger
from kuakua_agent.services.storage_layer import PreferenceStore

logger = get_logger(__name__)


class ModelAdapter:
    def __init__(self):
        pref = PreferenceStore()
        self.base_url = settings.llm_base_url.rstrip("/")
        raw_key = pref.get_sync("model_api_key") or settings.llm_api_key
        self.api_key = raw_key.strip() if raw_key else ""
        self.model_id = settings.llm_model_id.strip()

    def _require_api_key(self) -> None:
        """Raise if no API key is configured, so the error surfaces at call time
        rather than during scheduler / service construction."""
        if not self.api_key:
            raise ValueError(
                "API key is not configured. "
                "Please set DEEPSEEK_API_KEY / LLM_API_KEY / ARK_API_KEY "
                "in your environment or .env file."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def complete(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        self._require_api_key()
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
        self._require_api_key()
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
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def complete_async(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500) -> str:
        self._require_api_key()
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

    async def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.8,
        max_tokens: int = 500,
    ) -> str:
        """带工具调用的生成，处理多轮 Tool Calling"""
        self._require_api_key()
        started = time.perf_counter()

        all_messages = list(messages)
        tool_call_count = 0
        max_tool_calls = 10  # 防止无限循环

        while tool_call_count < max_tool_calls:
            payload = {
                "model": self.model_id,
                "messages": all_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "tools": tools,
            }
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )

            if response.status_code != 200:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")

            result = response.json()
            assistant_message = result["choices"][0]["message"]

            # 如果没有 tool_calls，返回最终内容
            if "tool_calls" not in assistant_message:
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "llm_complete_with_tools_finished",
                    extra={
                        "module_name": "llm",
                        "event": "complete_with_tools",
                        "duration_ms": duration_ms,
                        "tool_call_count": tool_call_count,
                        "model_id": self.model_id,
                    },
                )
                return assistant_message["content"].strip()

            # 有 tool_calls，处理每一轮
            all_messages.append(assistant_message)

            for tool_call in assistant_message["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                # 解析参数（可能是 JSON 字符串）
                try:
                    arguments = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
                except json.JSONDecodeError:
                    arguments = {}

                # 调用 MCP Client
                from kuakua_agent.services.mcp.client import MCPClient
                mcp_client = MCPClient()
                try:
                    tool_result = await mcp_client.call_tool(tool_name, arguments)
                    result_text = tool_result if isinstance(tool_result, str) else str(tool_result)
                except Exception as e:
                    logger.error(f"Tool call failed: {tool_name}, error: {e}")
                    result_text = f"工具调用失败: {str(e)}"

                # 将工具结果添加到消息列表
                all_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result_text,
                })
                tool_call_count += 1

        # 达到最大调用次数，返回最后的内容
        logger.warning(f"Max tool calls ({max_tool_calls}) reached")
        return all_messages[-1].get("content", "")

    async def stream_complete_async(self, messages: list[dict], temperature: float = 0.8, max_tokens: int = 500):
        """异步流式生成，返回可迭代对象，逐字产出无缓冲"""
        self._require_api_key()
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
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
