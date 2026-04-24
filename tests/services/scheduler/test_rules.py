import pytest
from datetime import datetime
from kuakua_agent.services.scheduler.rules import TriggerRule, TimeCondition, BehaviorCondition


def test_time_range_weekday():
    rule = TriggerRule(
        name="test",
        time_conditions=[
            TimeCondition(type="time_range", start="09:00", end="17:00", days=[1, 2, 3, 4, 5]),
        ],
    )
    monday_10 = datetime(2026, 4, 27, 10, 0)
    saturday_10 = datetime(2026, 4, 25, 10, 0)
    assert rule.evaluate_time(monday_10) is True
    assert rule.evaluate_time(saturday_10) is False


def test_behavior_focus_duration():
    rule = TriggerRule(
        name="test",
        behavior_conditions=[BehaviorCondition(type="focus_duration", min_minutes=60)],
    )
    assert rule.evaluate_behavior({"focus_minutes": 90}) is True
    assert rule.evaluate_behavior({"focus_minutes": 30}) is False


def test_combined_conditions():
    rule = TriggerRule(
        name="combined",
        time_conditions=[TimeCondition(type="time_range", start="09:00", end="17:00", days=[1, 2, 3, 4, 5])],
        behavior_conditions=[BehaviorCondition(type="focus_duration", min_minutes=30)],
    )
    monday = datetime(2026, 4, 27, 10, 0)
    assert rule.evaluate_time(monday) is True
    assert rule.evaluate_behavior({"focus_minutes": 60}) is True
    assert rule.evaluate_behavior({"focus_minutes": 10}) is False


def test_overnight_time_range():
    rule = TriggerRule(
        name="overnight",
        time_conditions=[TimeCondition(type="time_range", start="22:00", end="06:00")],
    )
    assert rule.evaluate_time(datetime(2026, 4, 27, 23, 0)) is True
    assert rule.evaluate_time(datetime(2026, 4, 27, 3, 0)) is True
    assert rule.evaluate_time(datetime(2026, 4, 27, 12, 0)) is False