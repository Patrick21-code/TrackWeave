from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.models.post import Post
from backend.models.comment import Comment
from backend.schemas.comment import CommentCreate, CommentUpdate, CommentOut

router = APIRouter()


def _enrich_comment(comment: Comment, current_user: Optional[User]) -> dict:
    score = sum(v.direction for v in comment.votes)
    user_vote = None
    if current_user:
        for v in comment.votes:
            if v.user_id == current_user.id:
                user_vote = v.direction
                break

    # Recursively enrich replies (only top-level replies for now)
    enriched_replies = [_enrich_comment(r, current_user) for r in comment.replies if not r.is_deleted]

    return {
        **comment.__dict__,
        "score":     score,
        "user_vote": user_vote,
        "author":    comment.author,
        "replies":   enriched_replies,
    }


# ── GET /api/comments/post/{post_id} ─────────────────────────────────────────
@router.get("/post/{post_id}", response_model=list[CommentOut])
def get_comments_for_post(
    post_id: int,
    db:      Session = Depends(get_db),
    current_user: User | None = None,
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    # Return only top-level comments; replies are nested inside
    top_level = (
        db.query(Comment)
        .filter(Comment.post_id == post_id, Comment.parent_id == None, Comment.is_deleted == False)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return [_enrich_comment(c, current_user) for c in top_level]


# ── POST /api/comments/post/{post_id} ─────────────────────────────────────────
@router.post("/post/{post_id}", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id:      int,
    payload:      CommentCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    if payload.parent_id:
        parent = db.query(Comment).filter(Comment.id == payload.parent_id).first()
        if not parent or parent.post_id != post_id:
            raise HTTPException(status_code=400, detail="Invalid parent comment.")

    comment = Comment(
        body      = payload.body,
        author_id = current_user.id,
        post_id   = post_id,
        parent_id = payload.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _enrich_comment(comment, current_user)


# ── PATCH /api/comments/{comment_id} ─────────────────────────────────────────
@router.patch("/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id:   int,
    payload:      CommentUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    comment.body = payload.body
    db.commit()
    db.refresh(comment)
    return _enrich_comment(comment, current_user)


# ── DELETE /api/comments/{comment_id} ────────────────────────────────────────
@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.is_deleted == False).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    comment.is_deleted = True
    db.commit()
