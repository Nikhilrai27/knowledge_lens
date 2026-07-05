import sys

from ..llm.client import LLMClient
from ..graph.state import AgentState
from ..tools.web_search import web_search


def research(state: AgentState, llm: LLMClient) -> dict:
    prompt = f"""You are a research specialist. Given the following task, research the topic thoroughly.

Task: {state['task']}
Plan: {state.get('plan', '')[:500]}

Compile comprehensive findings including key facts, data points, and notable perspectives.
Format your findings as a well-structured research report."""

    try:
        search_results = web_search(state["task"])
        if search_results and search_results != "No search results found.":
            prompt += f"\n\nWeb search results:\n{search_results}\n\nIncorporate the above web search results into your findings."
    except Exception as e:
        print(f"Warning: Web search failed ({e}). Proceeding with LLM knowledge only.", file=sys.stderr)

    result = llm.generate(prompt)
    return {"research_results": result}
