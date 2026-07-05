from ..llm.client import LLMClient
from ..graph.state import AgentState


def write(state: AgentState, llm: LLMClient) -> dict:
    prompt = f"""You are a writer. Given the following analysis, write a clear, well-organized document.

Analysis:
{state['analysis']}

Task: {state['task']}"""

    if state.get("review_feedback") and state.get("document"):
        prompt += f"""

The previous version of this document received this feedback:
{state['review_feedback']}

Please revise the document to address each piece of feedback. Here is the previous version:
{state['document']}"""

    prompt += "\n\nWrite a comprehensive document that addresses the original task. Use markdown formatting."

    result = llm.generate(prompt)
    return {"document": result}
