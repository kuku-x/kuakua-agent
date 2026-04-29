from typing import Literal

from kuakua_agent.services.ai_engine.graph.state import PraiseState


def should_refine(state: PraiseState) -> Literal["refine", "approve"]:
    """
    Determine whether to refine the draft or approve it.

    Returns:
        "refine" if refine_history has 3+ entries or evaluation contains FAIL/套话
        "approve" otherwise
    """
    refine_history = state.get("refine_history", [])
    evaluation = state.get("evaluation", "")

    # Check iteration limit (max 3 refinements)
    if len(refine_history) >= 3:
        return "approve"

    # Check evaluation for failure indicators
    evaluation_upper = evaluation.upper()
    if "FAIL" in evaluation_upper or "套话" in evaluation or "敷衍" in evaluation:
        return "refine"

    return "approve"
