from typing import TypedDict


class AgentState(TypedDict):
    task: str
    plan: str
    research_results: str
    analysis: str
    document: str
    review_score: int
    review_feedback: str
    review_passed: bool
    iterations: int
    max_iterations: int
