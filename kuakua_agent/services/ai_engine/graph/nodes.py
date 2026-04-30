import logging

from kuakua_agent.services.ai_engine.graph.state import PraiseState
from kuakua_agent.services.ai_engine import ContextBuilder, ModelAdapter
from kuakua_agent.services.notification.weather import WeatherService

logger = logging.getLogger(__name__)


async def gather_context_node(state: PraiseState) -> PraiseState:
    """Collect context for proactive praise generation."""
    context_builder = ContextBuilder()
    weather = WeatherService()

    milestone = state.get("milestone", {})
    trigger_type = milestone.get("event_type", "scheduled")

    # Build env_context string with trend data if available
    parts = [str(milestone.get("data", {}))]
    trend = milestone.get("trend", "")
    if trend:
        parts.append(f"\n近期趋势：\n{trend}")
    env_context = "\n".join(parts)

    messages, context_str = await context_builder.build_proactive_context(
        trigger_type=trigger_type,
        env_context=env_context,
        weather=weather.get_weather_summary(),
    )

    return {
        "context": context_str,
        "messages": messages,
    }


async def generate_draft_node(state: PraiseState) -> PraiseState:
    """Generate draft praise using the model."""
    model = ModelAdapter()
    messages = state["messages"]

    try:
        draft = await model.complete_async(messages, temperature=0.8, max_tokens=500)
    except Exception as e:
        logger.error(f"Failed to generate draft praise: {e}")
        draft = ""

    return {"draft_praise": draft}


EVALUATION_PROMPT_TEMPLATE = """你是一个严格的夸夸质量评审员。请评估以下夸夸内容是否符合标准：

待评估夸夸：
---
{draft}
---

请从以下三个维度评分（每个维度1-5分）：
1. 相关性：是否紧密围绕用户真实行为？
2. 真诚度：是否自然不套话？
3. 多样性：是否避免了重复的表达方式？

最后给出总结：
- 如果通过，给出"APPROVE"并简要说明理由
- 如果不通过，给出"FAIL"及具体原因

请用中文回复。"""


async def self_evaluate_node(state: PraiseState) -> PraiseState:
    """Self-evaluate the draft praise for quality control."""
    model = ModelAdapter()
    draft = state.get("draft_praise", "")

    if not draft:
        return {"evaluation": "FAIL: 空内容"}

    eval_messages = [
        {"role": "system", "content": "你是一个严格的评审员，请公正评分。"},
        {"role": "user", "content": EVALUATION_PROMPT_TEMPLATE.format(draft=draft)},
    ]

    try:
        evaluation = await model.complete_async(eval_messages, temperature=0.3, max_tokens=300)
    except Exception as e:
        logger.error(f"Failed to evaluate draft: {e}")
        evaluation = "FAIL: 评估失败"

    return {"evaluation": evaluation}


REFINE_PROMPT_TEMPLATE = """请根据以下评估意见，重写夸夸内容：

原始夸夸：
---
{draft}
---

评估意见：
---
{evaluation}
---

请生成一个改进版本，确保：
1. 更好地结合用户真实行为
2. 语言真诚自然，不套话
3. 表达方式有新鲜感
4. 控制在80字以内
"""


async def refine_praise_node(state: PraiseState) -> PraiseState:
    """Refine the draft praise based on evaluation feedback."""
    model = ModelAdapter()
    draft = state.get("draft_praise", "")
    evaluation = state.get("evaluation", "")
    refine_history = state.get("refine_history", [])

    refine_messages = [
        {"role": "system", "content": "你是夸夸改进助手。"},
        {"role": "user", "content": REFINE_PROMPT_TEMPLATE.format(draft=draft, evaluation=evaluation)},
    ]

    try:
        refined = await model.complete_async(refine_messages, temperature=0.8, max_tokens=500)
    except Exception as e:
        logger.error(f"Failed to refine praise: {e}")
        refined = draft  # Fallback to original

    return {
        "draft_praise": refined,
        "refine_history": refine_history + [refined],
    }


FORMAT_SYSTEM_PROMPT = """你是一个输出格式化助手。请确保夸夸内容：
1. 控制在80字以内
2. 包含适量emoji但不过量
3. 语气温暖真诚
4. 结尾有鼓励话语"""


async def format_output_node(state: PraiseState) -> PraiseState:
    """Format the final praise output."""
    model = ModelAdapter()
    draft = state.get("draft_praise", "")

    if not draft:
        return {"final_praise": ""}

    format_messages = [
        {"role": "system", "content": FORMAT_SYSTEM_PROMPT},
        {"role": "user", "content": f"请确保以下内容格式正确：\n{draft}"},
    ]

    try:
        final = await model.complete_async(format_messages, temperature=0.5, max_tokens=200)
    except Exception as e:
        logger.error(f"Failed to format output: {e}")
        final = draft  # Fallback to draft

    return {"final_praise": final}
