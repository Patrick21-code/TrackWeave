from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ---------------------------------------------------------------------------
# Connection string — set DATABASE_URL in your environment, e.g.:
#   postgresql://trackweave_user:password@localhost:5432/trackweave_db
# A sensible local default is provided so dev works out of the box.
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://trackweave_user:trackweave_pass@localhost:5432/trackweave_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Reconnect gracefully after idle disconnects
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ---------------------------------------------------------------------------
# Dependency — inject a DB session into every route that needs it
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
