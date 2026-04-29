import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_weather_tool() -> dict:
    """Return weather tool definition."""
    return {
        "name": "get_weather",
        "description": "查询用户所在地的当前天气",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "位置，默认 Shanghai"}
            }
        }
    }

async def handle_weather(arguments: dict) -> Any:
    """Handle get_weather tool call."""
    location = arguments.get("location", "Shanghai")
    try:
        from kuakua_agent.services.notification.weather import WeatherService
        weather = WeatherService()
        summary = weather.get_weather_summary()
        return f"当前{location}天气：{summary}"
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        return f"获取天气失败: {str(e)}"
