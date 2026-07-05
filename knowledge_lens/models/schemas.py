from pydantic import BaseModel, Field


class Subtask(BaseModel):
    step: int
    agent: str
    description: str


class TaskPlan(BaseModel):
    task: str
    subtasks: list[Subtask]


class ReviewResult(BaseModel):
    score: int = Field(ge=1, le=10)
    feedback: str
    passed: bool
