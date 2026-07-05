from fastapi import FastAPI
from pydantic import BaseModel

from knowledge_lens.cli import run_task

app = FastAPI(title="Knowledge Lens")


class RunRequest(BaseModel):
    task: str
    provider: str = "groq"


class RunResponse(BaseModel):
    document: str
    review_score: int
    review_feedback: str
    iterations: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    result = run_task(req.task, provider=req.provider)
    return RunResponse(
        document=result["document"],
        review_score=result["review_score"],
        review_feedback=result.get("review_feedback", ""),
        iterations=result["iterations"],
    )
