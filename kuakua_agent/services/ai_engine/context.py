import json
from datetime import datetime

from kuakua_agent.config import settings

from kuakua_agent.services.storage_layer import (
    MilestoneStore,
    PraiseHistoryStore,
    PreferenceStore,
    ProfileStore,
)
from kuakua_agent.services.ai_engine.prompt import PraisePromptManager
from kuakua_agent.services.user_behavior.daily_summary_db import DailyUsageSummaryDb
from kuakua_agent.services.notification.weather import WeatherService


def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return "早间"
    if 9 <= hour < 18:
        return "日间"
    return "晚间"


def summarize_praise_history(history: list, max_chars: int = 300) -> str:
    if not history:
        return "暂无最近夸夸记录"
    parts = []
    seen_styles: set[str] = set()
    for h in history[:10]:
        style_key = h.content[:10]
        if style_key in seen_styles:
            continue
        seen_styles.add(style_key)
        parts.append(f"- {h.content[:80]}")
    summary = "\n".join(parts)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    return summary


def deduplicate_milestones(milestones: list) -> list:
    seen: dict = {}
    for m in milestones:
        key = (m.event_type, m.occurred_at.replace(minute=0, second=0, microsecond=0))
        if key not in seen or m.occurred_at > seen[key][1]:
            seen[key] = (m, m.occurred_at)
    return [v[0] for v in seen.values()]


class ContextBuilder:
    TECH_QUESTION_PATTERNS = [
        "你用的哪个",
        "你用哪个",
        "用的什么模型",
        "用什么模型",
        "模型是什么",
        "哪个大模型",
        "大模型",
        "api",
        "api_key",
        "key",
        "token",
        "base_url",
        "deepseek",
        "openai",
        "claude",
        "gpt",
        "你是怎么实现的",
        "你怎么",
        "什么原理",
        "怎么做的",
        "如何实现",
        "请问",
        "多少",
        "在哪里",
        "是什么",
    ]

    def __init__(
        self,
        milestone_store=None,
        history_store=None,
        pref_store=None,
        profile_store=None,
        weather_service=None,
    ):
        self._ms = milestone_store or MilestoneStore()
        self._hs = history_store or PraiseHistoryStore()
        self._pref = pref_store or PreferenceStore()
        self._profile = profile_store or ProfileStore()
        self._weather = weather_service or WeatherService(self._pref)
        self._prompt_mgr = PraisePromptManager()

    def _is_technical_question(self, user_message: str) -> bool:
        normalized = user_message.strip().lower()
        return any(pattern in normalized for pattern in self.TECH_QUESTION_PATTERNS)

    def should_use_chat_history(self, user_message: str) -> bool:
        return not self._is_technical_question(user_message)

    def _build_technical_prompt(self, user_message: str) -> str:
        normalized = user_message.strip().lower()
        if any(token in normalized for token in ["模型", "大模型", "deepseek", "gpt", "claude", "openai"]):
            return (
                "用户在询问当前项目使用的大模型或模型配置。"
                "请直接、明确回答，不要转成夸夸话术，不要结合行为数据。"
                f"当前配置的模型 ID 是：{settings.llm_model_id}。"
                f"当前配置的 LLM Base URL 是：{settings.llm_base_url}。"
                "如果用户问“你用的哪个大模型”，优先直接回答模型 ID；"
                "如果合适，再补一句这是项目当前配置，实际也可能被环境变量覆盖。"
            )
        return (
            "用户在询问技术或配置信息。"
            "请直接、简洁、准确回答，不要转成夸夸话术，不要结合行为数据。"
        )

    async def build_user_context(
        self,
        user_message: str,
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        if self._is_technical_question(user_message):
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个友善的技术助手。"
                        "请直接、简洁、准确地回答用户的问题。"
                        "不要使用夸夸语气，不要结合行为数据发挥。"
                    ),
                },
                {"role": "system", "content": self._build_technical_prompt(user_message)},
                {"role": "user", "content": user_message},
            ]
            return messages, user_message

        if weather == "未知":
            weather = self._weather.get_weather_summary()

        time_of_day = get_time_of_day()
        recent = await self._ms.get_recent(hours=72, limit=10)
        recent = deduplicate_milestones(recent)
        recent_str = (
            "\n".join(f"- [{m.event_type}] {m.title}: {m.description or ''}" for m in recent)
            or "暂无近期行为里程碑"
        )
        history = await self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)
        profiles = await self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "通用陪伴"
        scene_context = f"主要场景: {top_scene}"
        recent_highlight = await self._build_recent_highlight(recent)
        reply_directive = self._build_reply_directive(user_message, recent_highlight)
        recent_usage_summary = self._build_recent_usage_summary(days=7)

        user_prompt_text = self._prompt_mgr.build_user_prompt(
            user_message=user_message,
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_str,
            praise_history_summary=history_summary,
            recent_highlight=recent_highlight,
            recent_usage_summary=recent_usage_summary,
            reply_directive=reply_directive,
            weather=weather,
        )
        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text

    async def build_proactive_context(
        self,
        trigger_type: str,
        env_context: str = "",
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        if weather == "未知":
            weather = self._weather.get_weather_summary()

        time_of_day = get_time_of_day()
        unrecalled = await self._ms.get_recent(hours=72, limit=10)
        unrecalled_str = (
            "\n".join(f"- [{m.event_type}] {m.title}: {m.description or ''}" for m in unrecalled)
            or "暂无新鲜行为里程碑"
        )
        history = await self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)
        profiles = await self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "通用陪伴"
        scene_context = f"主要场景: {top_scene}"
        _recent_milestones = unrecalled if unrecalled else await self._ms.get_recent(hours=72, limit=10)
        recent_highlight = await self._build_recent_highlight(_recent_milestones)
        recent_usage_summary = self._build_recent_usage_summary(days=7)

        # 构建向量检索上下文（跨时间上下文联想）
        vector_context = await self._build_vector_context(unrecalled)

        user_prompt_text = self._prompt_mgr.build_proactive_prompt(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_str,
            praise_history_summary=history_summary,
            env_context=env_context,
            recent_highlight=recent_highlight,
            recent_usage_summary=recent_usage_summary,
            weather=weather,
            vector_context=vector_context,
        )
        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text

    async def _build_vector_context(self, milestones: list) -> str:
        """构建向量检索上下文，检索历史相似成就"""
        if not milestones:
            return ""
        try:
            from kuakua_agent.services.ai_engine.vector_store import VectorStoreManager
            vector_store = VectorStoreManager()
            # 使用最近的 milestone 构建索引
            milestone_dicts = [
                {
                    "id": m.id,
                    "occurred_at": m.occurred_at.isoformat() if hasattr(m.occurred_at, 'isoformat') else str(m.occurred_at),
                    "event_type": m.event_type,
                    "description": m.description or "",
                }
                for m in milestones[:20]  # 限制数量
            ]
            if milestone_dicts:
                vector_store.build_milestone_index(milestone_dicts)
                # 使用最新的 milestone 检索相似成就
                current = milestone_dicts[0]
                recent = milestone_dicts[1:6]  # 最近5个作为 recent
                return vector_store.build_praise_context(current, recent)
        except Exception:
            # 向量检索失败时静默降级
            pass
        return ""

    async def _build_recent_highlight(self, milestones: list) -> str:
        if not milestones:
            return "最近也在稳稳推进自己的事情。"

        latest = milestones[0]
        description = latest.description or latest.title
        event_type = latest.event_type

        if event_type == "coding":
            return f"最近你有明显的编码投入，比如：{description}"
        if event_type == "focus":
            return f"最近你有一段很扎实的专注表现，比如：{description}"
        if event_type == "discipline":
            return f"最近你在自律推进上很亮眼，比如：{description}"
        return f"最近你有一个值得被夸的行为亮点：{description}"

    def _build_reply_directive(self, user_message: str, recent_highlight: str) -> str:
        normalized = user_message.strip().lower().replace("？", "?")
        identity_phrases = [
            "你是谁",
            "你叫什么",
            "你是干嘛的",
            "你是谁?",
            "who are you",
        ]
        if any(phrase in normalized for phrase in identity_phrases):
            return (
                "这次用户是在问你的身份。请用“我是你的专属夸夸呀😊！”开头，"
                f"并结合这条最近行为亮点做自我介绍：{recent_highlight}。"
                "语气要软萌真诚，结尾要补一句鼓励。"
            )
        return (
            "请优先结合最近行为亮点来夸，回复要元气、软萌、具体，"
            "并在结尾补一句鼓励，让用户更有动力继续保持。"
        )

    def _build_recent_usage_summary(self, days: int = 7, max_chars: int = 900) -> str:
        try:
            items = DailyUsageSummaryDb().list_recent(days=days)
        except Exception:
            return "暂无使用节奏画像摘要"

        if not items:
            return "暂无使用节奏画像摘要"

        lines: list[str] = []
        for item in reversed(items):
            try:
                payload = json.loads(item.payload_json)
                d = payload.get("date", item.date)
                combined = payload.get("combined", {}) or {}
                total_h = round((combined.get("total_seconds", 0) or 0) / 3600, 1)
                work_h = round((combined.get("work_seconds", 0) or 0) / 3600, 1)
                ent_h = round((combined.get("entertainment_seconds", 0) or 0) / 3600, 1)
                phone_top = (payload.get("phone", {}) or {}).get("top_apps", []) or []
                comp_top = (payload.get("computer", {}) or {}).get("top_apps", []) or []
                top_names = []
                for x in (comp_top[:2] + phone_top[:1]):
                    name = x.get("name")
                    if name:
                        top_names.append(str(name))
                top_str = ", ".join(top_names) if top_names else "N/A"
                lines.append(f"- {d[5:]}：总活跃 {total_h}h（工作 {work_h}h / 娱乐 {ent_h}h）Top: {top_str}")
            except Exception:
                lines.append(f"- {item.date[5:]}：已生成日画像摘要")

        text = "## 最近使用节奏画像（最近7天）\n" + "\n".join(lines)
        if len(text) > max_chars:
            return text[:max_chars] + "..."
        return text
