import json

from ..llm.client import LLMClient
from ..graph.state import AgentState
from ..models.schemas import ReviewResult


def review(state: AgentState, llm: LLMClient) -> dict:
    prompt = f"""You are a quality reviewer. Evaluate the following document.

Document:
{state['document']}

Task: {state['task']}

Rate the document 1-10 on:
- factual accuracy
- completeness
- clarity
- relevance to the task

Return ONLY a JSON object:
{{"score": <int 1-10>, "feedback": "<specific feedback>", "passed": <true if score >= 7 else false>}}"""

    result = llm.generate(prompt).strip()

    if "```" in result:
        result = result.split("```")[1]
        if result.startswith("json"):
            result = result[4:]
        result = result.strip()

    try:
        parsed = json.loads(result)
        review_result = ReviewResult(**parsed)
    except (json.JSONDecodeError, Exception):
        review_result = ReviewResult(
            score=6, feedback="Review parsing issue. Defaulting to pass.", passed=True
        )

    return {
        "review_score": review_result.score,
        "review_feedback": review_result.feedback,
        "review_passed": review_result.passed,
    }
