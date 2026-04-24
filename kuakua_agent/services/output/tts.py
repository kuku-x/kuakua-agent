import asyncio
import hashlib
import httpx
import sys
import tempfile
from pathlib import Path
from kuakua_agent.services.output.base import OutputChannel, OutputResult
from kuakua_agent.services.memory import PreferenceStore


class FishTTS(OutputChannel):
    DEFAULT_API_URL = "https://api.fish.audio/v1/tts"

    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._cache_dir = Path(tempfile.gettempdir()) / "kuakua_tts"
        self._cache_dir.mkdir(exist_ok=True)

    def supports(self, channel_type: str) -> bool:
        return channel_type in ("tts", "voice", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        if not self._pref.get_bool("tts_enable"):
            return OutputResult(success=False, channel="tts", content=content, error="TTS未开启")

        api_url = (metadata or {}).get("api_url", self.DEFAULT_API_URL)
        voice_id = self._pref.get("tts_voice") or "default"
        speed = self._pref.get_float("tts_speed", 1.0)

        cache_key = hashlib.md5(f"{content}:{voice_id}:{speed}".encode()).hexdigest()
        cached = self._cache_dir / f"{cache_key}.mp3"

        try:
            if cached.exists():
                await self._play_audio(str(cached))
            else:
                audio_data = await self._fetch_tts(content, api_url, voice_id, speed)
                cached.write_bytes(audio_data)
                await self._play_audio(str(cached))
            return OutputResult(success=True, channel="tts", content=content)
        except Exception as e:
            # 静默兜底：TTS异常降级为纯通知，不向主流程抛异常
            return OutputResult(success=False, channel="tts", content=content, error=f"TTS静默失败: {e}")

    async def _fetch_tts(self, text: str, api_url: str, voice_id: str, speed: float) -> bytes:
        payload = {
            "model": voice_id,
            "text": text,
            "speed": speed,
        }
        headers = {"Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fish Audio API失败: {response.status_code}")
        return response.content

    async def _play_audio(self, filepath: str) -> None:
        if sys.platform == "win32":
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                f'(New-Object System.Media.SoundPlayer "{filepath}").PlaySync()',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        elif sys.platform == "darwin":
            proc = await asyncio.create_subprocess_exec(
                "afplay", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        else:
            proc = await asyncio.create_subprocess_exec(
                "mpg123", filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()