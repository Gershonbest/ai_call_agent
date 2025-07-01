from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import os
from dotenv import load_dotenv

from app.models.database import create_tables, get_db
from app.api.routes import agents, tools, calls, phone_numbers, knowledge_base
from app.core.call_manager import CallManager

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Voice Agent API",
    description="A comprehensive API for managing voice agents, tools, and calls",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
app.include_router(calls.router, prefix="/api/v1/calls", tags=["Calls"])
app.include_router(phone_numbers.router, prefix="/api/v1/phone-numbers", tags=["Phone Numbers"])
app.include_router(knowledge_base.router, prefix="/api/v1/knowledge-bases", tags=["Knowledge Bases"])


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    create_tables()
    print("Database tables created successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Voice Agent API is running"}


@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint"""
    return {"status": "healthy", "message": "API is operational"}


def main():
    """Main function for running the application"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


if __name__ == "__main__":
    main() 