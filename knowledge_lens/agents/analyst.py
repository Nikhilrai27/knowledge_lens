from ..llm.client import LLMClient
from ..graph.state import AgentState


def analyze(state: AgentState, llm: LLMClient) -> dict:
    prompt = f"""You are an analyst. Given the following research findings, provide a structured analysis.

Research Findings:
{state['research_results']}

Identify:
1. Key themes and patterns
2. Important relationships and connections
3. Caveats and uncertainties
4. Key takeaways

Format as a structured analysis report."""

    result = llm.generate(prompt)
    return {"analysis": result}
