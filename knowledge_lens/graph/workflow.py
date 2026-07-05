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

    def human_node(state: AgentState) -> dict:
        print("\n=== Human Approval Required ===")
        print(f"Review score: {state['review_score']}/10 (max iterations reached)")
        print(f"Feedback: {state['review_feedback']}")
        print("\nHow do you want to proceed?")
        print("  a - Approve and finish")
        print("  f - Provide feedback and retry writer")
        print("  r - Reject")
        choice = input("> ").strip().lower()

        if choice == "a":
            return {}
        if choice == "f":
            fb = input("Feedback for writer: ").strip()
            return {"review_feedback": fb, "_human_retry": True, "iterations": 0}
        return {"review_feedback": "Rejected by user."}

    def decide_next(state: AgentState) -> str:
        if state["review_passed"]:
            return "store"
        if state["iterations"] >= state["max_iterations"]:
            if state.get("human_gate", True):
                return "human"
            return "store"
        return "rewrite"

    builder = StateGraph(AgentState)

    builder.add_node("plan", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("write", write_node)
    builder.add_node("review", review_node)
    builder.add_node("human", human_node)
    builder.add_node("store", store_node)

    builder.set_entry_point("plan")

    builder.add_edge("plan", "research")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "write")
    builder.add_edge("write", "review")

    builder.add_conditional_edges(
        "review",
        decide_next,
        {"store": "store", "rewrite": "write", "human": "human"},
    )

    def after_human(state: AgentState) -> str:
        if state.get("_human_retry"):
            return "rewrite"
        return "store"

    builder.add_conditional_edges(
        "human",
        after_human,
        {"store": "store", "rewrite": "write"},
    )

    builder.add_edge("store", END)

    return builder.compile()
