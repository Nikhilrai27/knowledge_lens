from langgraph.graph import END, StateGraph

from ..agents.analyst import analyze
from ..agents.researcher import research
from ..agents.reviewer import review
from ..agents.supervisor import create_plan
from ..agents.writer import write
from ..llm.client import LLMClient
from ..memory.semantic import memory
from .state import AgentState


def build_workflow(llm: LLMClient):

    def plan_node(state: AgentState) -> dict:
        return create_plan(state, llm)

    def research_node(state: AgentState) -> dict:
        return research(state, llm)

    def analyze_node(state: AgentState) -> dict:
        return analyze(state, llm)

    def write_node(state: AgentState) -> dict:
        doc = write(state, llm)
        doc["iterations"] = state["iterations"] + 1
        return doc

    def review_node(state: AgentState) -> dict:
        return review(state, llm)

    def store_node(state: AgentState) -> dict:
        memory.store(
            task=state["task"],
            document=state.get("document", ""),
            score=state.get("review_score", 0),
        )
        return {}

    def decide_next(state: AgentState) -> str:
        if state["review_passed"] or state["iterations"] >= state["max_iterations"]:
            return "end"
        return "rewrite"

    builder = StateGraph(AgentState)

    builder.add_node("plan", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("write", write_node)
    builder.add_node("review", review_node)
    builder.add_node("store", store_node)

    builder.set_entry_point("plan")

    builder.add_edge("plan", "research")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.add_edge("write", "review")

    builder.add_conditional_edges(
        "review",
        decide_next,
        {"end": "store", "rewrite": "write"},
    )

    builder.add_edge("store", END)

    return builder.compile()
