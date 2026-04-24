import asyncio
import hashlib
import httpx
import sys
import tempfile
from pathlib import Path

from kuakua_agent.config import settings
from kuakua_agent.services.output.base import OutputChannel, OutputResult
from kuakua_agent.services.memory import PreferenceStore


class FishTTS(OutputChannel):
    DEFAULT_API_URL = "https://api.fish.audio/v1/tts"
    DEFAULT_MODEL = "s2-pro"

    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._cache_dir = Path(tempfile.gettempdir()) / "kuakua_tts"
        self._cache_dir.mkdir(exist_ok=True)

    def supports(self, channel_type: str) -> bool:
        return channel_type in ("tts", "voice", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        if not self._pref.get_bool("tts_enable"):
            return OutputResult(success=False, channel="tts", content=content, error="TTS未开启")

        api_key = self._pref.get("fish_audio_api_key") or getattr(settings, "fish_audio_api_key", "")
        if not api_key:
            return OutputResult(success=False, channel="tts", content=content, error="Fish Audio API Key 未配置")

        voice_id = self._pref.get("tts_voice") or ""
        if not voice_id or voice_id == "default":
            return OutputResult(success=False, channel="tts", content=content, error="Fish Audio Voice ID 未配置")

        api_url = (metadata or {}).get("api_url", self.DEFAULT_API_URL)
        speed = self._pref.get_float("tts_speed", 1.0)
        model = self._pref.get("fish_audio_model") or self.DEFAULT_MODEL

        cache_key = hashlib.md5(f"{content}:{voice_id}:{speed}:{model}".encode()).hexdigest()
        cached = self._cache_dir / f"{cache_key}.wav"

        try:
            if not cached.exists():
                audio_data = await self._fetch_tts(
                    text=content,
                    api_url=api_url,
                    api_key=api_key,
                    voice_id=voice_id,
                    speed=speed,
                    model=model,
                )
                try:
                    cached.write_bytes(audio_data)
                except OSError:
                    pass

            await self._play_audio(str(cached))
            return OutputResult(success=True, channel="tts", content=content)
        except Exception as e:
            return OutputResult(success=False, channel="tts", content=content, error=f"Fish Audio 播放失败: {e}")

    async def _fetch_tts(
        self,
        *,
        text: str,
        api_url: str,
        api_key: str,
        voice_id: str,
        speed: float,
        model: str,
    ) -> bytes:
        payload = {
            "text": text,
            "reference_id": voice_id,
            "format": "wav",
            "latency": "normal",
            "speed": speed,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "model": model,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Fish Audio API 失败: {response.status_code} - {response.text[:200]}")
        return response.content

    async def _play_audio(self, filepath: str) -> None:
        if sys.platform == "win32":
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                f'(New-Object System.Media.SoundPlayer "{filepath}").PlaySync()',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        elif sys.platform == "darwin":
            proc = await asyncio.create_subprocess_exec(
                "afplay",
                filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        else:
            proc = await asyncio.create_subprocess_exec(
                "mpg123",
                filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
