import logging
from langgraph.graph import StateGraph, END

from kuakua_agent.services.ai_engine.graph.state import PraiseState
from kuakua_agent.services.ai_engine.graph.nodes import (
    gather_context_node,
    generate_draft_node,
    self_evaluate_node,
    refine_praise_node,
    format_output_node,
)
from kuakua_agent.services.ai_engine.graph.edges import should_refine

logger = logging.getLogger(__name__)


def build_praise_graph() -> StateGraph:
    """
    Build the LangGraph praise generation workflow.

    Flow:
        gather_context → generate_draft → self_evaluate
                                                    ↓
                               should_refine → {refine: refine_praise, approve: format_output}
                                                    ↓
                    refine_praise → generate_draft (loop back)
                                                    ↓
                               format_output → END
    """
    workflow = StateGraph(PraiseState)

    # Add nodes
    workflow.add_node("gather_context", gather_context_node)
    workflow.add_node("generate_draft", generate_draft_node)
    workflow.add_node("self_evaluate", self_evaluate_node)
    workflow.add_node("refine_praise", refine_praise_node)
    workflow.add_node("format_output", format_output_node)

    # Set entry point
    workflow.set_entry_point("gather_context")

    # Normal edges
    workflow.add_edge("gather_context", "generate_draft")
    workflow.add_edge("generate_draft", "self_evaluate")
    workflow.add_edge("format_output", END)

    # Conditional edge from self_evaluate
    workflow.add_conditional_edges(
        "self_evaluate",
        should_refine,
        {
            "refine": "refine_praise",
            "approve": "format_output",
        },
    )

    # Loop edge: refine_praise → generate_draft
    workflow.add_edge("refine_praise", "generate_draft")

    return workflow


# Singleton compiled graph instance
_compiled_graph = None


def get_praise_graph() -> StateGraph:
    """Get the compiled praise graph singleton."""
    global _compiled_graph
    if _compiled_graph is None:
        builder = build_praise_graph()
        _compiled_graph = builder.compile()
    return _compiled_graph


async def run_praise_workflow(milestone: dict) -> str:
    """
    Run the praise generation workflow with the given milestone.

    Args:
        milestone: A dict containing milestone information (event_type, title, etc.)

    Returns:
        The final generated praise string.
    """
    graph = get_praise_graph()

    initial_state: PraiseState = {
        "milestone": milestone,
        "context": "",
        "messages": [],
        "draft_praise": "",
        "evaluation": "",
        "final_praise": "",
        "refine_history": [],
    }

    try:
        result = await graph.ainvoke(initial_state)
        return result.get("final_praise", "")
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        return ""
