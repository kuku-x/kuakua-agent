from datetime import datetime, timedelta
from kuakua_agent.services.memory import (
    MilestoneStore,
    PraiseHistoryStore,
    PreferenceStore,
    ProfileStore,
)
from kuakua_agent.services.brain.prompt import PraisePromptManager


def get_time_of_day() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 9:
        return "早间"
    elif 9 <= hour < 18:
        return "日间"
    else:
        return "晚间"


def summarize_praise_history(history: list, max_chars: int = 300) -> str:
    if not history:
        return "暂无夸夸历史"
    parts = []
    seen_styles: set[str] = set()
    for h in history[:10]:
        style_key = h.content[:10]
        if style_key in seen_styles and len(seen_styles) >= 2:
            continue
        seen_styles.add(style_key)
        parts.append(f"- {h.content[:80]}")
    summary = "\n".join(parts)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."
    return summary


def deduplicate_milestones(milestones: list, within_hours: int = 1) -> list:
    seen: dict = {}
    for m in milestones:
        key = (m.event_type, m.occurred_at.replace(minute=0, second=0, microsecond=0))
        if key not in seen or m.occurred_at > seen[key][1]:
            seen[key] = (m, m.occurred_at)
    return [v[0] for v in seen.values()]


class ContextBuilder:
    def __init__(
        self,
        milestone_store=None,
        history_store=None,
        pref_store=None,
        profile_store=None,
    ):
        self._ms = milestone_store or MilestoneStore()
        self._hs = history_store or PraiseHistoryStore()
        self._pref = pref_store or PreferenceStore()
        self._profile = profile_store or ProfileStore()
        self._prompt_mgr = PraisePromptManager()

    def build_user_context(
        self,
        user_message: str,
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        time_of_day = get_time_of_day()
        recent = self._ms.get_recent(hours=72, limit=10)
        recent = deduplicate_milestones(recent)
        recent_str = (
            "\n".join(
                f"- [{m.event_type}] {m.title}: {m.description or ''}"
                for m in recent
            )
            or "暂无近期里程碑"
        )
        history = self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)
        profiles = self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "一般"
        scene_context = f"主要场景: {top_scene}"
        user_prompt_text = self._prompt_mgr.build_user_prompt(
            user_message=user_message,
            time_of_day=time_of_day,
            scene_context=scene_context,
            recent_milestones=recent_str,
            praise_history_summary=history_summary,
            weather=weather,
        )
        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text

    def build_proactive_context(
        self,
        trigger_type: str,
        env_context: str = "",
        weather: str = "未知",
    ) -> tuple[list[dict], str]:
        time_of_day = get_time_of_day()
        unrecalled = self._ms.get_unrecalled(hours=72, limit=5)
        unrecalled_str = (
            "\n".join(
                f"- [{m.event_type}] {m.title}: {m.description or ''}"
                for m in unrecalled
            )
            or "暂无新鲜里程碑"
        )
        history = self._hs.get_recent(limit=20)
        history_summary = summarize_praise_history(history)
        profiles = self._profile.get_all()
        top_scene = profiles[0].scene if profiles else "一般"
        scene_context = f"主要场景: {top_scene}"
        user_prompt_text = self._prompt_mgr.build_proactive_prompt(
            trigger_type=trigger_type,
            time_of_day=time_of_day,
            scene_context=scene_context,
            unrecalled_milestones=unrecalled_str,
            praise_history_summary=history_summary,
            env_context=env_context,
            weather=weather,
        )
        messages = [
            {"role": "system", "content": self._prompt_mgr.get_system_prompt()},
            {"role": "user", "content": user_prompt_text},
        ]
        return messages, user_prompt_text