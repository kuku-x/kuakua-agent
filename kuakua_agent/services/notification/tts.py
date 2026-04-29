from __future__ import annotations

import asyncio
import hashlib
import httpx
import importlib.util
import io
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

from kuakua_agent.config import ROOT_DIR, settings
from kuakua_agent.services.storage_layer import PreferenceStore
from kuakua_agent.services.notification.base import OutputChannel, OutputResult


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
        if not await self._pref.get_bool("tts_enable"):
            return OutputResult(success=False, channel="tts", content=content, error="TTS not enabled")

        api_key = await self._pref.get("fish_audio_api_key") or getattr(settings, "fish_audio_api_key", "")
        if not api_key:
            return OutputResult(success=False, channel="tts", content=content, error="Fish Audio API key is not configured")

        voice_id = await self._pref.get("tts_voice") or ""
        if not voice_id or voice_id == "default":
            return OutputResult(success=False, channel="tts", content=content, error="Fish Audio voice id is not configured")

        api_url = (metadata or {}).get("api_url", self.DEFAULT_API_URL)
        speed = await self._pref.get_float("tts_speed", 1.0)
        model = await self._pref.get("fish_audio_model") or self.DEFAULT_MODEL

        cache_key = hashlib.md5(f"{content}:{voice_id}:{speed}:{model}".encode("utf-8")).hexdigest()
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
        except Exception as exc:
            return OutputResult(success=False, channel="tts", content=content, error=f"Fish Audio playback failed: {exc}")

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
            raise RuntimeError(f"Fish Audio API failed: {response.status_code} - {response.text[:200]}")
        return response.content

    async def _play_audio(self, filepath: str) -> None:
        await _play_audio(filepath)


class KokoroTTS(OutputChannel):
    DEFAULT_MODEL_SOURCE = "hexgrad/Kokoro-82M-v1.1-zh"
    DEFAULT_MODEL_PATH = "D:\project\External-ependencies\kokoro-v1.1"
    DEFAULT_VOICE = "zf_001"
    SAMPLE_RATE = 24000

    def __init__(self, pref_store=None):
        self._pref = pref_store or PreferenceStore()
        self._cache_dir = Path(tempfile.gettempdir()) / "kuakua_tts"
        self._cache_dir.mkdir(exist_ok=True)
        self._pipeline = None
        self._pipeline_source: str | None = None

    def supports(self, channel_type: str) -> bool:
        return channel_type in ("tts", "voice", "all")

    async def send(self, content: str, metadata: dict | None = None) -> OutputResult:
        if not await self._pref.get_bool("tts_enable"):
            return OutputResult(success=False, channel="tts", content=content, error="TTS not enabled")

        voice = await self._get_voice()
        speed = await self._pref.get_float("tts_speed", 1.0)
        model_source = self._get_model_source()

        cache_key = hashlib.md5(f"{content}:{voice}:{speed}:{model_source}".encode("utf-8")).hexdigest()
        cached = self._cache_dir / f"kokoro_{cache_key}.wav"

        try:
            if not cached.exists():
                audio_data = await asyncio.to_thread(self._generate_wav_bytes, content, voice, speed)
                try:
                    cached.write_bytes(audio_data)
                except OSError:
                    pass

            await _play_audio(str(cached))
            return OutputResult(success=True, channel="tts", content=content)
        except Exception as exc:
            return OutputResult(success=False, channel="tts", content=content, error=str(exc))

    def _generate_wav_bytes(self, text: str, voice: str, speed: float) -> bytes:
        pipeline = self._get_pipeline()
        generator = pipeline(text, voice=voice, speed=speed)
        chunks: list[np.ndarray] = []

        for item in generator:
            audio = _extract_audio_chunk(item)
            if audio is None:
                continue
            chunks.append(np.asarray(audio, dtype=np.float32).reshape(-1))

        if not chunks:
            raise RuntimeError("Kokoro generated no audio data")

        full_audio = np.concatenate(chunks)
        return _float_audio_to_wav_bytes(full_audio, self.SAMPLE_RATE)

    def _get_pipeline(self):
        model_source = self._get_model_source()
        if self._pipeline is not None and self._pipeline_source == model_source:
            return self._pipeline

        if importlib.util.find_spec("kokoro") is None:
            raise RuntimeError("Kokoro is not installed. Run `pip install kokoro misaki[zh]` first.")

        try:
            from kokoro import KPipeline
        except Exception as exc:
            raise RuntimeError(f"Failed to import Kokoro: {exc}") from exc

        try:
            self._pipeline = KPipeline(lang_code="z", repo_id=model_source)
        except TypeError:
            # Older package versions may not expose repo_id.
            self._pipeline = KPipeline(lang_code="z")
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize Kokoro pipeline from `{model_source}`: {exc}") from exc

        self._pipeline_source = model_source
        return self._pipeline

    async def _get_voice(self) -> str:
        voice = (await self._pref.get("kokoro_voice") or await self._pref.get("tts_voice") or self.DEFAULT_VOICE).strip()
        return voice or self.DEFAULT_VOICE

    def _get_model_source(self) -> str:
        raw_value = (self._pref.get_sync("kokoro_model_path") or self.DEFAULT_MODEL_PATH).strip()
        if not raw_value:
            raw_value = self.DEFAULT_MODEL_SOURCE

        candidate = Path(raw_value)
        if candidate.is_absolute():
            return str(candidate)

        project_path = (ROOT_DIR / candidate).resolve()
        if project_path.exists():
            return str(project_path)

        if candidate.exists():
            return str(candidate.resolve())

        # Fall back to the upstream repo id when the configured path is missing but
        # still looks like a repo identifier.
        if "/" in raw_value and not raw_value.startswith("."):
            return raw_value

        raise RuntimeError(
            "Kokoro model path is not ready. Expected a local directory like "
            f"`{(ROOT_DIR / self.DEFAULT_MODEL_PATH).resolve()}` or a valid repo id."
        )


def _extract_audio_chunk(item: object) -> np.ndarray | None:
    if item is None:
        return None
    if hasattr(item, "audio"):
        return np.asarray(getattr(item, "audio"), dtype=np.float32)
    if isinstance(item, tuple):
        if len(item) >= 3:
            return np.asarray(item[2], dtype=np.float32)
        if len(item) >= 2 and isinstance(item[1], tuple) and len(item[1]) >= 2:
            return np.asarray(item[1][1], dtype=np.float32)
    return None


def _float_audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    mono = np.asarray(audio, dtype=np.float32).reshape(-1)
    clipped = np.clip(mono, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return buffer.getvalue()


async def _play_audio(filepath: str) -> None:
    if sys.platform == "win32":
        proc = await asyncio.create_subprocess_exec(
            "powershell",
            "-Command",
            f'(New-Object System.Media.SoundPlayer "{filepath}").PlaySync()',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return

    if sys.platform == "darwin":
        proc = await asyncio.create_subprocess_exec(
            "afplay",
            filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return

    proc = await asyncio.create_subprocess_exec(
        "aplay",
        filepath,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()