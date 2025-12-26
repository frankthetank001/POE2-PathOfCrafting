from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.models import Base, engine, SessionLocal, AdminUser
from app.core.security import hash_password


def init_database() -> None:
    """Initialize database tables and seed default admin user."""
    Base.metadata.create_all(bind=engine)

    # Seed default admin user if none exists
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).first()
        if admin is None:
            default_admin = AdminUser(
                username=settings.default_admin_username,
                password_hash=hash_password(settings.default_admin_password),
            )
            db.add(default_admin)
            db.commit()
            logger = get_logger(__name__)
            logger.info(f"Created default admin user: {settings.default_admin_username}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting PoE2 AI TradeCraft API")

    # Initialize database
    init_database()
    logger.info("Database initialized")

    yield
    logger.info("Shutting down PoE2 AI TradeCraft API")


app = FastAPI(
    title="PoE2 AI TradeCraft API",
    description="API for Path of Exile 2 build analysis and crafting theory",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root() -> dict:
    return {
        "message": "PoE2 AI TradeCraft API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}