from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional
import base64, imghdr

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.models.post import Post
from backend.schemas.user import UserPublic, UserPrivate, UserProfileUpdate
from backend.schemas.post import PostOut
from backend.routers.posts import _enrich_post, _optional_user

router = APIRouter()

MAX_AVATAR_BYTES = 2 * 1024 * 1024   # 2 MB


# ── GET /api/users/{username} ─────────────────────────────────────────────────
@router.get("/{username}", response_model=UserPublic)
def get_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ── PATCH /api/users/me ───────────────────────────────────────────────────────
@router.patch("/me", response_model=UserPrivate)
def update_profile(
    payload: UserProfileUpdate,
    db:   Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.bio is not None:
        current_user.bio = payload.bio
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url

    db.commit()
    db.refresh(current_user)
    return current_user


# ── POST /api/users/me/avatar ─────────────────────────────────────────────────
@router.post("/me/avatar", response_model=UserPrivate)
async def upload_avatar(
    file: UploadFile = File(...),
    db:   Session    = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=413, detail="Avatar must be ≤ 2 MB.")

    fmt = imghdr.what(None, content)
    if fmt not in ("jpeg", "png", "gif", "webp"):
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, GIF, WEBP allowed.")

    data_uri = f"data:image/{fmt};base64,{base64.b64encode(content).decode()}"
    current_user.avatar_url = data_uri
    db.commit()
    db.refresh(current_user)
    return current_user


# ── GET /api/users/{username}/posts ───────────────────────────────────────────
@router.get("/{username}/posts", response_model=list[PostOut])
def user_posts(
    username: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(_optional_user),
):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    posts = (
        db.query(Post)
        .filter(Post.author_id == user.id, Post.is_deleted == False)
        .order_by(Post.created_at.desc())
        .offset(skip).limit(limit)
        .all()
    )
    return [_enrich_post(p, current_user) for p in posts]
