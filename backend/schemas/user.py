from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ── Request schemas (what the client sends) ──────────────────────────────────

class UserRegister(BaseModel):
    username:     str       = Field(..., min_length=3, max_length=30)
    email:        EmailStr
    password:     str       = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, max_length=60)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, numbers, and underscores.")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserLogin(BaseModel):
    identifier: str   # email OR username
    password:   str


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=60)
    bio:          Optional[str] = Field(None, max_length=500)
    avatar_url:   Optional[str] = Field(None, max_length=500)


# ── Response schemas (what the API returns) ───────────────────────────────────

class UserPublic(BaseModel):
    """Public-facing user info — safe to expose to anyone."""
    id:           int
    username:     str
    display_name: Optional[str]
    bio:          Optional[str]
    avatar_url:   Optional[str]
    created_at:   datetime

    model_config = {"from_attributes": True}


class UserPrivate(UserPublic):
    """Extended info returned only to the authenticated user themselves."""
    email:    str
    is_admin: bool

    model_config = {"from_attributes": True}


# ── Token schemas ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
