"""Manage Fish Audio voices — fetch via SDK, save locally, test playback.

Usage:
  python fish_audio_voices.py list               # Fetch & save to data/
  python fish_audio_voices.py test <voice_id>    # Test a specific voice
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOICE_FILE = PROJECT_ROOT / "data" / "fish_audio_voices.json"

import httpx
from kuakua_agent.config import settings


def get_api_key() -> str:
    key = os.getenv("FISH_AUDIO_API_KEY") or getattr(settings, "fish_audio_api_key", "")
    if not key:
        print("请先在 .env 中设置 FISH_AUDIO_API_KEY=你的key")
        sys.exit(1)
    return key


async def list_via_sdk(api_key: str):
    """Fetch voices using the fish-audio-sdk and save to local JSON."""
    try:
        from fishaudio import FishAudio
    except ImportError:
        try:
            from fish_audio_sdk import Session  # type: ignore
        except ImportError:
            print("❌ fish-audio-sdk 未安装。请运行: pip install fish-audio-sdk")
            return
        else:
            print("⚠️  旧版 SDK，尝试 HTTP 方式...")
            await list_via_http(api_key)
            return

    print("正在通过 SDK 拉取音色列表...")
    client = FishAudio(api_key=api_key)
    try:
        result = client.voices.list(page_size=50, language="zh")
        items = result.items
    except Exception as e:
        print(f"SDK 调用失败: {e}")
        return

    if not items:
        print("API 返回为空。")
        return

    voices = [
        {
            "id": getattr(v, "id", ""),
            "title": getattr(v, "title", "") or getattr(v, "id", ""),
            "tags": list(getattr(v, "tags", []) or []),
        }
        for v in items
    ]

    _save_and_display(voices)


async def list_via_http(api_key: str):
    """Fallback: try raw HTTP to known endpoints."""
    urls = [
        "https://api.fish.audio/v1/models",
        "https://api.fish.audio/v1/voices",
    ]
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    params={"page_size": 50},
                )
                if resp.status_code == 404:
                    continue
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", []) or data.get("data", []) or []
                if items:
                    voices = [
                        {
                            "id": v.get("id") or v.get("voice_id", ""),
                            "title": v.get("title") or v.get("name", v.get("id", "")),
                            "tags": v.get("tags", []) or [],
                        }
                        for v in items
                    ]
                    _save_and_display(voices)
                    return
        except Exception:
            continue
    print("HTTP 方式也失败了。请手动编辑 data/fish_audio_voices.json。")


def _save_and_display(voices: list[dict]):
    print(f"\n找到 {len(voices)} 个音色：\n")
    for i, v in enumerate(voices):
        tags_str = f" ({', '.join(v['tags'][:4])})" if v.get("tags") else ""
        print(f"  [{i}] {v['id'][:24]}...  —  {v['title']}{tags_str}")

    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_FILE.write_text(json.dumps(voices, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已保存到: {VOICE_FILE}")
    print("重启后端后，设置页面下拉框自动加载。")


async def test_voice(api_key: str, voice_id: str):
    text = "你好呀，我是你的专属夸夸助手，今天过得怎么样呀？"
    print(f"\n正在合成 [{voice_id}]: {text}")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.fish.audio/v1/tts",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"text": text, "reference_id": voice_id, "format": "wav"},
        )
        if resp.status_code != 200:
            print(f"  API {resp.status_code}: {resp.text[:200]}")
            return
        audio = resp.content

    out = PROJECT_ROOT / "data" / "tts_samples" / f"{voice_id[:12]}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"  已保存: {out}  ({len(audio)} bytes)")

    try:
        subprocess.run(["start", str(out)], shell=True, timeout=10)
        print("  应在默认播放器中打开了")
    except Exception:
        print(f"  请手动打开: {out}")


async def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python fish_audio_voices.py list              # 拉取音色列表并保存到本地")
        print("  python fish_audio_voices.py test <voice_id>   # 试听指定音色")
        return

    api_key = get_api_key()
    cmd = sys.argv[1]

    if cmd == "list":
        await list_via_sdk(api_key)
    elif cmd == "test":
        if len(sys.argv) < 3:
            print("请提供 voice_id")
            return
        await test_voice(api_key, sys.argv[2])


if __name__ == "__main__":
    asyncio.run(main())
