from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.core.security import decode_token
from backend.models.user import User
from backend.models.post import Post
from backend.models.comment import Comment
from backend.models.vote import Vote
from backend.schemas.post import PostCreate, PostUpdate, PostOut

router = APIRouter()

# Optional auth: reads the token if present but never raises a 401
_optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def _optional_user(
    token: Optional[str] = Depends(_optional_oauth2),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return user if user and user.is_active else None


# ── Shared helper: attach computed fields ────────────────────────────────────
def _enrich_post(post: Post, current_user: Optional[User]) -> dict:
    score = sum(v.direction for v in post.votes)
    comment_count = len([c for c in post.comments if not c.is_deleted])
    user_vote = None
    if current_user:
        for v in post.votes:
            if v.user_id == current_user.id:
                user_vote = v.direction
                break
    return {
        **post.__dict__,
        "score":         score,
        "comment_count": comment_count,
        "user_vote":     user_vote,
        "author":        post.author,
    }


# ── GET /api/posts — feed ──────────────────────────────────────────────────
@router.get("/", response_model=list[PostOut])
def list_posts(
    skip:  int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort:  str = Query("new", pattern="^(new|top)$"),
    db:    Session = Depends(get_db),
    current_user: Optional[User] = Depends(_optional_user),
):
    query = db.query(Post).filter(Post.is_deleted == False)
    posts = query.order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

    if sort == "top":
        posts.sort(key=lambda p: sum(v.direction for v in p.votes), reverse=True)

    return [_enrich_post(p, current_user) for p in posts]


# ── POST /api/posts ────────────────────────────────────────────────────────
@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    payload:      PostCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    if not payload.body and not payload.link_url:
        raise HTTPException(status_code=422, detail="Post must have either a body or a link URL.")

    post = Post(
        title     = payload.title,
        body      = payload.body,
        link_url  = payload.link_url,
        author_id = current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _enrich_post(post, current_user)


# ── GET /api/posts/{post_id} ───────────────────────────────────────────────
@router.get("/{post_id}", response_model=PostOut)
def get_post(
    post_id: int,
    db:      Session = Depends(get_db),
    current_user: Optional[User] = Depends(_optional_user),
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return _enrich_post(post, current_user)


# ── PATCH /api/posts/{post_id} ─────────────────────────────────────────────
@router.patch("/{post_id}", response_model=PostOut)
def update_post(
    post_id:      int,
    payload:      PostUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    if payload.title is not None:
        post.title = payload.title
    if payload.body is not None:
        post.body = payload.body

    db.commit()
    db.refresh(post)
    return _enrich_post(post, current_user)


# ── DELETE /api/posts/{post_id} ────────────────────────────────────────────
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized.")

    post.is_deleted = True
    db.commit()
