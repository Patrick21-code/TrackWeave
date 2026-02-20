from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.models.post import Post
from backend.models.comment import Comment
from backend.models.vote import Vote
from backend.schemas.vote import VoteIn, VoteOut

router = APIRouter()


@router.post("/", response_model=VoteOut)
def cast_vote(
    payload:      VoteIn,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    # Validate: exactly one target
    if (payload.post_id is None) == (payload.comment_id is None):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of post_id or comment_id.",
        )

    # Verify the target exists
    if payload.post_id:
        target = db.query(Post).filter(Post.id == payload.post_id, Post.is_deleted == False).first()
        if not target:
            raise HTTPException(status_code=404, detail="Post not found.")
        existing = (
            db.query(Vote)
            .filter(Vote.user_id == current_user.id, Vote.post_id == payload.post_id)
            .first()
        )
    else:
        target = db.query(Comment).filter(Comment.id == payload.comment_id, Comment.is_deleted == False).first()
        if not target:
            raise HTTPException(status_code=404, detail="Comment not found.")
        existing = (
            db.query(Vote)
            .filter(Vote.user_id == current_user.id, Vote.comment_id == payload.comment_id)
            .first()
        )

    # direction=0 means remove the vote
    if payload.direction == 0:
        if existing:
            db.delete(existing)
            db.commit()
        message = "Vote removed."
    elif existing:
        existing.direction = payload.direction
        db.commit()
        message = "Vote updated."
    else:
        new_vote = Vote(
            user_id    = current_user.id,
            post_id    = payload.post_id,
            comment_id = payload.comment_id,
            direction  = payload.direction,
        )
        db.add(new_vote)
        db.commit()
        message = "Vote cast."

    # Compute new score
    if payload.post_id:
        db.refresh(target)
        new_score = sum(v.direction for v in target.votes)
    else:
        db.refresh(target)
        new_score = sum(v.direction for v in target.votes)

    return VoteOut(message=message, new_score=new_score)
