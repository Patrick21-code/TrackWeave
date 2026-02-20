from sqlalchemy import Column, Integer, ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.core.database import Base


class Vote(Base):
    """
    A vote can target either a post OR a comment (not both).
    direction: +1 (upvote) or -1 (downvote).
    One user can only cast one vote per post / comment.
    """
    __tablename__ = "votes"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    post_id    = Column(Integer, ForeignKey("posts.id",    ondelete="CASCADE"), nullable=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    direction  = Column(SmallInteger, nullable=False)   # +1 or -1

    # Relationships
    user    = relationship("User",    back_populates="votes")
    post    = relationship("Post",    back_populates="votes")
    comment = relationship("Comment", back_populates="votes")

    __table_args__ = (
        # One vote per (user, post)
        UniqueConstraint("user_id", "post_id",    name="uq_vote_user_post"),
        # One vote per (user, comment)
        UniqueConstraint("user_id", "comment_id", name="uq_vote_user_comment"),
    )
