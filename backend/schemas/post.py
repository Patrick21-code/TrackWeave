from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from backend.schemas.user import UserPublic


# ── Request schemas ───────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    title:    str            = Field(..., min_length=1, max_length=300)
    body:     Optional[str]  = Field(None, max_length=40_000)
    link_url: Optional[str]  = Field(None, max_length=2048)


class PostUpdate(BaseModel):
    title:    Optional[str] = Field(None, min_length=1, max_length=300)
    body:     Optional[str] = Field(None, max_length=40_000)


# ── Response schemas ──────────────────────────────────────────────────────────

class PostOut(BaseModel):
    id:            int
    title:         str
    body:          Optional[str]
    link_url:      Optional[str]
    author:        UserPublic
    score:         int          # computed: sum of vote directions
    comment_count: int          # computed
    user_vote:     Optional[int] = None   # +1, -1, or None if not authenticated
    created_at:    datetime
    updated_at:    datetime

    model_config = {"from_attributes": True}
