import sys

from .graph.state import AgentState
from .graph.workflow import build_workflow
from .llm.client import LLMClient


def run_task(task: str, provider: str = "groq") -> dict:
    llm = LLMClient(provider=provider)
    graph = build_workflow(llm)

    initial_state: AgentState = {
        "task": task,
        "plan": "",
        "research_results": "",
        "analysis": "",
        "document": "",
        "review_score": 0,
        "review_feedback": "",
        "review_passed": False,
        "iterations": 0,
        "max_iterations": 3,
        "_human_retry": False,
    }

    return graph.invoke(initial_state)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <task description>")
        print("   or: python main.py --interactive")
        sys.exit(1)

    if sys.argv[1] == "--interactive":
        while True:
            try:
                task = input("\nEnter your task (or 'quit' to exit): ")
            except (EOFError, KeyboardInterrupt):
                break
            if task.lower() in ("quit", "exit", "q"):
                break
            if not task.strip():
                continue
            result = run_task(task)
            print("\n" + "=" * 60)
            print("RESULT:")
            print(result.get("document", "No document produced"))
            print("=" * 60)
            print(f"Review score: {result.get('review_score', 'N/A')}/10")
            print(f"Iterations: {result.get('iterations', 0)}")
            if result.get("review_feedback"):
                print(f"Review feedback: {result['review_feedback']}")
    else:
        task = " ".join(sys.argv[1:])
        result = run_task(task)
        print("\n" + "=" * 60)
        print("RESULT:")
        print(result.get("document", "No document produced"))
        print("=" * 60)
        print(f"Review score: {result.get('review_score', 'N/A')}/10")
        print(f"Iterations: {result.get('iterations', 0)}")
        if result.get("review_feedback"):
            print(f"Review feedback: {result['review_feedback']}")
