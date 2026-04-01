import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

log = logging.getLogger(__name__)

# Lifespan handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # --- Startup Logic ---
    log.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"Debug mode: {settings.DEBUG}")
    yield

    # --- Shutdown Logic ---
    log.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CapMed-Sci: A Medical Research Chat API - Answer medical questions with coted research papers",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan # Pass lifespan to FastAPI
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" 
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )