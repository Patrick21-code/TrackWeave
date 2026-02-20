from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from backend.core.database import engine, Base
from backend.routers import auth, users, posts, comments, votes

# Create all tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="TrackWeave API",
    description="Backend API for the TrackWeave music social platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (served from a different port in dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten this to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(users.router,    prefix="/api/users",    tags=["Users"])
app.include_router(posts.router,    prefix="/api/posts",    tags=["Posts"])
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
app.include_router(votes.router,    prefix="/api/votes",    tags=["Votes"])

# Serve the frontend static files from /frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
