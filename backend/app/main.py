import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import Base, engine
from app.config import settings
from app.routers import users, reviews, comments, search, feedback, analytics


def init_db():
    Base.metadata.create_all(bind=engine)
    if settings.auto_seed:
        from app.seed import run_seed

        run_seed()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Агрегатор рейтингов китайских производителей",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(comments.router)
app.include_router(search.router)
app.include_router(feedback.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
