from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id         = Column(Integer, primary_key=True, index=True)
    body       = Column(Text, nullable=False)
    author_id  = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    post_id    = Column(Integer, ForeignKey("posts.id",    ondelete="CASCADE"), nullable=False)
    parent_id  = Column(Integer, ForeignKey("comments.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    author  = relationship("User",    back_populates="comments")
    post    = relationship("Post",    back_populates="comments")
    replies = relationship("Comment", backref="parent", remote_side=[id])
    votes   = relationship("Vote",    back_populates="comment", cascade="all, delete-orphan")
