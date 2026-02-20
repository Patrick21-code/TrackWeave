from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from backend.schemas.user import UserPublic


# ── Request schemas ───────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    body:      str           = Field(..., min_length=1, max_length=10_000)
    parent_id: Optional[int] = None   # If replying to another comment


class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=10_000)


# ── Response schemas ──────────────────────────────────────────────────────────

class CommentOut(BaseModel):
    id:        int
    body:      str
    author:    UserPublic
    post_id:   int
    parent_id: Optional[int]
    score:     int
    user_vote: Optional[int] = None
    replies:   List["CommentOut"] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Allow self-referential type
CommentOut.model_rebuild()
