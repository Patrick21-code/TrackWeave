from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from backend.core.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(30), unique=True, index=True, nullable=False)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    display_name  = Column(String(60), nullable=True)
    bio           = Column(Text, nullable=True)
    avatar_url    = Column(String(500), nullable=True)   # URL or base-64 data-uri

    # Account state
    is_active     = Column(Boolean, default=True, nullable=False)
    is_admin      = Column(Boolean, default=False, nullable=False)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    posts    = relationship("Post",    back_populates="author",  cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author",  cascade="all, delete-orphan")
    votes    = relationship("Vote",    back_populates="user",    cascade="all, delete-orphan")
