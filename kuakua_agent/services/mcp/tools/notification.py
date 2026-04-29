import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_notification_tool() -> dict:
    """Return notification tool definition."""
    return {
        "name": "send_notification",
        "description": "发送系统通知",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "message": {"type": "string"}
            }
        }
    }

async def handle_notification(arguments: dict) -> Any:
    """Handle send_notification tool call."""
    title = arguments.get("title", "夸夸 Agent")
    message = arguments.get("message", "")
    try:
        from kuakua_agent.services.notification.notifier import SystemNotifier
        notifier = SystemNotifier()
        await notifier.send(message, metadata={"title": title})
        return f"通知已发送: {title}"
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        return f"通知发送失败: {str(e)}"

async def handle_tts(arguments: dict) -> Any:
    """Handle text_to_speech tool call."""
    text = arguments.get("text", "")
    try:
        from kuakua_agent.services.notification.tts import KokoroTTS
        tts = KokoroTTS()
        await tts.send(text, None)
        return f"语音播放中: {text[:20]}..."
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return f"语音播放失败: {str(e)}"
