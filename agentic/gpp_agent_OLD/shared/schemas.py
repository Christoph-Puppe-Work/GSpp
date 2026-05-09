from pydantic import BaseModel, Field

class ReviewCriteria(BaseModel):
    is_approved: bool = Field(description="Whether the artifact is approved or needs revision")
    feedback: str = Field(description="Detailed feedback if revision is required")
    score: float = Field(description="Quality score between 0.0 and 1.0")

class Savepoint(BaseModel):
    iv_id: str
    save_id: str
    data: dict
