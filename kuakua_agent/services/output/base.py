import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OutputResult:
    success: bool
    channel: str
    content: str
    error: str | None = None


class OutputChannel(ABC):
    @abstractmethod
    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        ...

    @abstractmethod
    def supports(self, channel_type: str) -> bool:
        ...


class OutputManager:
    def __init__(self):
        self._channels: list[OutputChannel] = []

    def register(self, channel: OutputChannel) -> None:
        self._channels.append(channel)

    async def dispatch(self, content: str, channel_types: list[str] | None = None, metadata: dict | None = None) -> list[OutputResult]:
        results = []
        tasks = []
        for ch in self._channels:
            if channel_types and not any(ch.supports(ct) for ct in channel_types):
                continue
            tasks.append(self._safe_send(ch, content, metadata or {}))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if isinstance(r, OutputResult)
            else OutputResult(success=False, channel="unknown", content=content, error=str(r))
            for r in results
        ]

    async def _safe_send(self, channel: OutputChannel, content: str, metadata: dict) -> OutputResult:
        try:
            return await channel.send(content, metadata)
        except Exception as e:
            return OutputResult(success=False, channel=type(channel).__name__, content=content, error=str(e))