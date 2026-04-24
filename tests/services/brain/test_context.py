import pytest
from datetime import datetime
from kuakua_agent.services.memory.models import Milestone, PraiseHistory
from kuakua_agent.services.brain.context import deduplicate_milestones, summarize_praise_history


def test_deduplicate_milestones_same_hour():
    now = datetime.now()
    milestones = [
        Milestone(1, "focus", "专注1", None, now, now, False),
        Milestone(2, "focus", "专注2", None, now, now, False),
        Milestone(3, "coding", "编码1", None, now, now, False),
    ]
    result = deduplicate_milestones(milestones)
    assert len(result) == 2
    assert result[0].title == "专注1"


def test_summarize_praise_history_dedup():
    history = [
        PraiseHistory(1, "你今天工作很努力", "active", None, datetime.now()),
        PraiseHistory(2, "你今天工作很努力", "active", None, datetime.now()),
        PraiseHistory(3, "休息一下吧", "proactive", None, datetime.now()),
    ]
    summary = summarize_praise_history(history, max_chars=200)
    lines = [l for l in summary.split("\n") if l.startswith("-")]
    assert len(lines) <= 3