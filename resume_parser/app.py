import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from database.connection import engine
from database.models import Base
from routers.auth import router as auth_router
from routers.resume import router as resume_router, upload_alias_router
from routers.users import router as users_router, profiles_router
from resume_parser.routes.upload import router as upload_router
from routers.internships import router as internships_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AI Internship Agent Backend",
    description="Hybrid resume parsing with RAG-based internship matching.",
    version="2.0.0",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(resume_router)
app.include_router(upload_alias_router)
app.include_router(upload_router)
app.include_router(internships_router)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            existing_columns = {column["name"] for column in inspector.get_columns("users")}
            required_columns = {"id", "full_name", "hashed_password", "reset_token_hash", "reset_token_expires_at"}
            if not required_columns.issubset(existing_columns):
                logger.warning("Detected an outdated users table schema. Rebuilding database tables.")
                Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception:
        logger.exception("Failed to initialize database tables during startup")
        raise

    # Verify and initialize internship vector index
    try:
        from resume_parser.services.internship_matcher import build_internship_index
        build_internship_index()
        logger.info("Internship vector index initialized and verified on startup.")
    except Exception as exc:
        logger.warning("Could not auto-initialize internship index on startup: %s", exc)
