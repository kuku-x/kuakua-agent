from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TriggerType(Enum):
    SCHEDULED = "scheduled"
    BEHAVIOR_DETECTED = "behavior_detected"
    FIRST_AWAKE = "first_awake"
    FOCUS_MILESTONE = "focus_milestone"
    CUSTOM = "custom"


@dataclass
class SchedulerEvent:
    trigger_type: TriggerType
    occurred_at: datetime
    data: dict | None = None
    rule_name: str | None = None