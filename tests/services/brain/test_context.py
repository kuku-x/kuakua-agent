import pytest
from datetime import datetime
from kuakua_agent.services.memory.models import Milestone, PraiseHistory
from kuakua_agent.config import settings
from kuakua_agent.services.brain.context import ContextBuilder, deduplicate_milestones, summarize_praise_history


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


def test_technical_question_uses_direct_prompt_and_skips_history():
    builder = ContextBuilder()

    messages, enriched_prompt = builder.build_user_context("你用的哪个大模型")

    assert builder.should_use_chat_history("你用的哪个大模型") is False
    assert enriched_prompt == "你用的哪个大模型"
    assert len(messages) == 3
    assert messages[-1] == {"role": "user", "content": "你用的哪个大模型"}
    assert settings.llm_model_id in messages[1]["content"]


def test_identity_question_keeps_praise_context():
    builder = ContextBuilder()

    messages, enriched_prompt = builder.build_user_context("你是谁", weather="晴")

    assert builder.should_use_chat_history("你是谁") is True
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "我是你的专属夸夸呀" in enriched_prompt