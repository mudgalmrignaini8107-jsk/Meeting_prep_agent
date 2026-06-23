# app/main.py

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Import DB and Models
from app.database import engine
from app.models import Base

# Import Routers
from app.api import auth, dashboard, meetings, briefs, copilot, transcripts
from app.config import settings

# Configure logging
logger.add("app_run.log", rotation="10 MB", serialize=False)

# Initialize database schema automatically on startup (convenient for MVP/Docker)
try:
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database tables: {e}")

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    description="MVP Backend API for AI Meeting Preparation Agent coordinating Calendar sync, RAG, and LangGraph dossiers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for frontend dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

# System health endpoint moved to /api/health
@app.get("/api/health", tags=["System Health"])
def system_health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "database": "connected" if engine else "error",
        "version": "1.0.0"
    }

# Wire up routers with dual-mounting (both at root and /api/v1 for compatibility)
for prefix in ["", "/api/v1"]:
    app.include_router(auth.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(meetings.router, prefix=prefix)
    app.include_router(briefs.router, prefix=prefix)
    app.include_router(copilot.router, prefix=prefix)
    app.include_router(transcripts.router, prefix=prefix)

# Dynamically mount frontend files if FRONTEND_DIR exists
frontend_path = os.path.abspath(settings.FRONTEND_DIR)
if os.path.exists(frontend_path):
    logger.info(f"Serving static frontend files from {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}. Running in pure API mode.")
