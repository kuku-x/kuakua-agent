import logging
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp_server = FastMCP("kuakua-agent")

@mcp_server.tool()
async def get_weather(location: str = "Shanghai") -> str:
    """查询天气"""
    from .tools.weather import handle_weather
    result = await handle_weather({"location": location})
    return result

@mcp_server.tool()
async def send_notification(title: str, message: str) -> str:
    """发送通知"""
    from .tools.notification import handle_notification
    result = await handle_notification({"title": title, "message": message})
    return result

@mcp_server.tool()
async def text_to_speech(text: str) -> str:
    """文字转语音"""
    from .tools.notification import handle_tts
    result = await handle_tts({"text": text})
    return result
