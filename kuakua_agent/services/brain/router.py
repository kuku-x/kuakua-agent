from enum import Enum
from dataclasses import dataclass


class Intent(Enum):
    CHAT = "chat"
    SETTING = "setting"
    QUERY_MEMORY = "query_memory"
    FEEDBACK = "feedback"
    PROACTIVE_PRAISE = "proactive_praise"
    UNKNOWN = "unknown"


@dataclass
class IntentRouter:
    def route(self, text: str) -> Intent:
        text = text.strip().lower()
        if text.startswith(("设置", "关闭", "开启", "配置")):
            return Intent.SETTING
        if any(k in text for k in ["查一下", "看看", "我的记录", "里程碑"]):
            return Intent.QUERY_MEMORY
        if any(k in text for k in ["喜欢", "不喜欢", "夸得好", "太敷衍"]):
            return Intent.FEEDBACK
        return Intent.CHAT

    def route_event(self, event_type: str) -> Intent:
        if event_type.startswith("proactive_"):
            return Intent.PROACTIVE_PRAISE
        return Intent.UNKNOWN