from typing import Optional, Literal
from pydantic import BaseModel, field_validator


class VoteIn(BaseModel):
    direction:  Literal[1, -1, 0]   # 0 = remove existing vote
    post_id:    Optional[int] = None
    comment_id: Optional[int] = None

    @field_validator("post_id", "comment_id", mode="before")
    @classmethod
    def exactly_one_target(cls, v, info):
        # Cross-field validation is done in the router instead
        return v


class VoteOut(BaseModel):
    message:   str
    new_score: int
