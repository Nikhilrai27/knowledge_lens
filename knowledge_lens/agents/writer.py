from ..llm.client import LLMClient
from ..graph.state import AgentState


def write(state: AgentState, llm: LLMClient) -> dict:
    prompt = f"""You are a writer. Given the following analysis, write a clear, well-organized document.

Analysis:
{state['analysis']}

Task: {state['task']}

Write a comprehensive document that addresses the original task. Use markdown formatting."""

    result = llm.generate(prompt)
    return {"document": result}
