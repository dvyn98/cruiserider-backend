"""
CruiseRider - Automotive Content & Car Data Platform
FastAPI Backend - Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting CruiseRider API...")
    await create_tables()
    logger.info("Database tables ready")
    yield
    logger.info("Shutting down CruiseRider API...")


app = FastAPI(
    title="CruiseRider API",
    description="""
    ## CruiseRider - Automotive Content Platform API
    
    Full-stack backend for Priyanshu's automotive website featuring:
    - Car database with on-road prices across all Indian cities
    - YouTube video sync and embedding
    - Instagram feed integration  
    - AI-powered blog generation from video content
    - Car consultancy booking system
    - SEO-optimised article management
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS - Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount all API routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "running",
        "app": "CruiseRider API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "cruiserider-api"}
