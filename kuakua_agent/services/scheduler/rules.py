from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class TimeCondition:
    type: Literal["time_range", "moment"]
    start: str | None = None
    end: str | None = None
    days: list[int] | None = None
    moment: str | None = None


@dataclass
class BehaviorCondition:
    type: Literal["focus_duration", "app_category", "event_type"]
    min_minutes: int = 0
    category: str | None = None
    event_type: str | None = None


@dataclass
class TriggerRule:
    name: str
    time_conditions: list[TimeCondition] = field(default_factory=list)
    behavior_conditions: list[BehaviorCondition] = field(default_factory=list)
    cooldown_minutes: int = 30
    max_per_day: int = 10
    enabled: bool = True

    def evaluate_time(self, now: datetime) -> bool:
        if not self.time_conditions:
            return True
        return all(self._eval_single_time(tc, now) for tc in self.time_conditions)

    def _eval_single_time(self, tc: TimeCondition, now: datetime) -> bool:
        if tc.type == "time_range":
            if tc.days and now.isoweekday() not in tc.days:
                return False
            start_t = datetime.strptime(tc.start, "%H:%M").time()
            end_t = datetime.strptime(tc.end, "%H:%M").time()
            cur = now.time()
            if start_t <= end_t:
                return start_t <= cur <= end_t
            else:
                return cur >= start_t or cur <= end_t
        if tc.type == "moment":
            if tc.moment == "first_awake":
                return 5 <= now.hour < 9
        return True

    def evaluate_behavior(self, behavior_data: dict) -> bool:
        if not self.behavior_conditions:
            return True
        return all(self._eval_single_behavior(bc, behavior_data) for bc in self.behavior_conditions)

    def _eval_single_behavior(self, bc: BehaviorCondition, data: dict) -> bool:
        if bc.type == "focus_duration":
            return data.get("focus_minutes", 0) >= bc.min_minutes
        if bc.type == "app_category":
            return data.get("category_minutes", {}).get(bc.category, 0) >= bc.min_minutes
        if bc.type == "event_type":
            return data.get("last_event") == bc.event_type
        return True


DEFAULT_RULES = [
    TriggerRule(
        name="早间专注夸",
        time_conditions=[
            TimeCondition(type="time_range", start="07:00", end="09:00", days=[1, 2, 3, 4, 5]),
            TimeCondition(type="moment", moment="first_awake"),
        ],
        behavior_conditions=[
            BehaviorCondition(type="focus_duration", min_minutes=30),
        ],
        cooldown_minutes=60,
    ),
    TriggerRule(
        name="午后工作鼓励",
        time_conditions=[
            TimeCondition(type="time_range", start="13:00", end="14:00", days=[1, 2, 3, 4, 5]),
        ],
        behavior_conditions=[
            BehaviorCondition(type="focus_duration", min_minutes=60),
        ],
        cooldown_minutes=120,
    ),
    TriggerRule(
        name="晚间休息提醒",
        time_conditions=[
            TimeCondition(type="time_range", start="18:00", end="20:00"),
        ],
        behavior_conditions=[
            BehaviorCondition(type="app_category", category="development", min_minutes=45),
        ],
        cooldown_minutes=45,
    ),
]