import pytest
from datetime import datetime
from kuakua_agent.services.monitor.scheduler.rules import TriggerRule, TimeCondition, BehaviorCondition


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


def test_time_moment_first_awake():
    rule = TriggerRule(
        name="test",
        time_conditions=[TimeCondition(type="moment", moment="first_awake")],
    )
    # 5-9 AM should match first_awake
    assert rule.evaluate_time(datetime(2026, 4, 27, 6, 0)) is True
    assert rule.evaluate_time(datetime(2026, 4, 27, 8, 59)) is True
    # outside range should not match
    assert rule.evaluate_time(datetime(2026, 4, 27, 10, 0)) is False
    assert rule.evaluate_time(datetime(2026, 4, 27, 4, 0)) is False


def test_behavior_app_category():
    rule = TriggerRule(
        name="test",
        behavior_conditions=[BehaviorCondition(type="app_category", category="development", min_minutes=30)],
    )
    assert rule.evaluate_behavior({"category_minutes": {"development": 45}}) is True
    assert rule.evaluate_behavior({"category_minutes": {"development": 15}}) is False
    assert rule.evaluate_behavior({"category_minutes": {"other": 100}}) is False


def test_behavior_event_type():
    rule = TriggerRule(
        name="test",
        behavior_conditions=[BehaviorCondition(type="event_type", event_type="focus")],
    )
    assert rule.evaluate_behavior({"last_event": "focus"}) is True
    assert rule.evaluate_behavior({"last_event": "coding"}) is False