from typing import TypedDict


class PraiseState(TypedDict):
    """LangGraph workflow state for praise generation."""

    milestone: dict  # Current milestone being processed
    context: str  # Context string for the prompt
    messages: list[dict]  # Message history for the workflow
    draft_praise: str  # Draft praise generated
    evaluation: str  # Self-evaluation result
    final_praise: str  # Final approved praise
    refine_history: list[str]  # List of refined drafts (max 3)
