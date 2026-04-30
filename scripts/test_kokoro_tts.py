"""TTS smoke test — tries Fish Audio first, falls back to Kokoro."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kuakua_agent.services.notification.tts import FallbackTTS, FishTTS, KokoroTTS


TEST_TEXT = "你好呀，我是你的专属夸夸助手，今天也辛苦啦，记得给自己一个微笑哦。"


async def main():
    # Test 1: FallbackTTS (Fish → Kokoro)
    print("=== FallbackTTS (Fish Audio → Kokoro) ===")
    tts = FallbackTTS()
    result = await tts.send(TEST_TEXT)
    if result.success:
        print(f"  ✅ 播放成功 (channel: {result.channel})")
    else:
        print(f"  ❌ 主通道失败: {result.error}")
        print(f"     如果没有配置 Fish Audio API key，这是正常的")
        print(f"     Kokoro 已自动接替，检查是否听到了本地语音")

    # Test 2: Fish Audio alone (will fail gracefully if no API key)
    print("\n=== Fish Audio (单独测试) ===")
    fish = FishTTS()
    result = await fish.send(TEST_TEXT)
    if result.success:
        print(f"  ✅ Fish Audio 播放成功")
    else:
        print(f"  ℹ️  {result.error}")
        print(f"     去 https://fish.audio 注册，拿到 key 后在 .env 里加:")
        print(f"     FISH_AUDIO_API_KEY=你的key")

    # Test 3: Kokoro alone
    print("\n=== Kokoro (本地备用) ===")
    kokoro = KokoroTTS()
    result = await kokoro.send(TEST_TEXT)
    if result.success:
        print(f"  ✅ Kokoro 播放成功")

    print("\n---")
    print("配置 Fish Audio: 在项目根目录 .env 文件中添加 FISH_AUDIO_API_KEY=你的key")


if __name__ == "__main__":
    asyncio.run(main())
