from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from backend.core.deps import get_current_user
from backend.models.user import User
from backend.schemas.user import UserRegister, UserLogin, UserPrivate, Token, TokenRefresh

router = APIRouter()


# ── POST /api/auth/register ───────────────────────────────────────────────────
@router.post("/register", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check uniqueness
    if db.query(User).filter(User.username == payload.username.lower()).first():
        raise HTTPException(status_code=409, detail="Username already taken.")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        username        = payload.username.lower(),
        email           = payload.email.lower(),
        hashed_password = hash_password(payload.password),
        display_name    = payload.display_name or payload.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── POST /api/auth/login ──────────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    # Accept email or username
    identifier = payload.identifier.lower().strip()
    user = (
        db.query(User).filter(User.email == identifier).first()
        or db.query(User).filter(User.username == identifier).first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")

    token_data = {"sub": str(user.id)}
    return Token(
        access_token  = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
    )


# ── POST /api/auth/refresh ────────────────────────────────────────────────────
@router.post("/refresh", response_model=Token)
def refresh_token(payload: TokenRefresh, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data is None or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == int(data["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found.")

    token_data = {"sub": str(user.id)}
    return Token(
        access_token  = create_access_token(token_data),
        refresh_token = create_refresh_token(token_data),
    )


# ── GET /api/auth/me ──────────────────────────────────────────────────────────
@router.get("/me", response_model=UserPrivate)
def me(current_user: User = Depends(get_current_user)):
    return current_user
