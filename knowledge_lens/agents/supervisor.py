from ..llm.client import LLMClient
from ..graph.state import AgentState
from ..memory.semantic import memory


def create_plan(state: AgentState, llm: LLMClient) -> dict:
    past = memory.query(state["task"])
    memory_context = ""
    if past:
        memory_context = "\n\nSimilar past task outputs for reference:\n" + "\n---\n".join(past[:2])

    prompt = f"""You are a task supervisor. Decompose the following task into a step-by-step execution plan.

Task: {state['task']}{memory_context}

Return a JSON array of steps, each with:
- "step": step number
- "agent": one of "researcher", "analyst", "writer"
- "description": what this step should do

Example:
[
  {{"step": 1, "agent": "researcher", "description": "Research the topic and gather key facts"}},
  {{"step": 2, "agent": "analyst", "description": "Analyze the findings and identify patterns"}},
  {{"step": 3, "agent": "writer", "description": "Write the final document"}}
]

Return ONLY the JSON array, no other text."""

    result = llm.generate(prompt)
    return {"plan": result}
