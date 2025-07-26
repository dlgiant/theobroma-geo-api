import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="Theobroma Digital API",
    description="Microservice for cocoa plantation monitoring and management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Theobroma Digital API",
        "version": "1.0.0",
        "description": "Microservice for cocoa plantation monitoring",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint to monitor API status
    """
    uptime = time.time() - start_time
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
    }


@app.get("/farms")
async def get_farms():
    """Test farms endpoint"""
    return {
        "farms": [
            {
                "id": "farm_001",
                "name": "Test Farm",
                "location": "Test Location",
                "total_lots": 5,
                "total_trees": 1000,
                "status": "healthy",
            }
        ],
        "total_farms": 1,
    }


@app.get("/trees")
async def get_trees():
    """Test trees endpoint"""
    return {
        "trees": [
            {
                "id": "tree_001",
                "farm_id": "farm_001",
                "lot_id": 1,
                "status": "healthy",
                "maturity": 75.5,
            }
        ],
        "total_trees": 1,
    }


@app.get("/lots")
async def get_lots():
    """Test lots endpoint"""
    return {
        "lots": [
            {
                "lot_id": 1,
                "farm_id": "farm_001",
                "total_trees": 200,
                "healthy_trees": 180,
                "avg_maturity": 75.5,
            }
        ],
        "total_lots": 1,
    }


@app.get("/security-events")
async def get_security_events():
    """Test security events endpoint"""
    return {
        "events": [
            {
                "id": "event_001",
                "type": "test_event",
                "severity": "low",
                "timestamp": datetime.now().isoformat(),
                "resolved": False,
            }
        ],
        "total_events": 1,
    }


@app.get("/metrics")
async def get_metrics():
    """Test metrics endpoint"""
    return {
        "api_version": "1.0.0",
        "uptime_seconds": round(time.time() - start_time, 2),
        "status": "healthy",
        "requests_processed": 42,
        "timestamp": datetime.now().isoformat(),
    }
