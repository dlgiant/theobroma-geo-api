import os
import time
from datetime import datetime
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import (
    Farm,
    Lot,
    Tree,
    disable_detailed_query_logging,
    enable_detailed_query_logging,
    get_db,
    get_query_stats,
    reset_query_stats,
    test_connection,
)
from models import (
    AnalyticsResponse,
    ErrorResponse,
    HealthResponse,
    LotsResponse,
    SecurityEventsResponse,
    SecurityLevel,
)
from models import Tree as TreeModel
from models import (
    WeatherResponse,
)
from services import (
    AnalyticsService,
    FarmService,
    LotService,
    SecurityService,
    WeatherService,
)

# Load environment variables
load_dotenv()

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
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()


# Database startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    if not test_connection():
        raise Exception("Failed to connect to database")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Theobroma Digital API",
        "version": "1.0.0",
        "description": "Microservice for cocoa plantation monitoring",
        "endpoints": [
            "/lots - Get plantation lots summary",
            "/security/events - Get security events",
            "/weather - Get weather data",
            "/analytics/production - Get production analytics",
            "/health - Health check",
        ],
        "documentation": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to monitor API status
    """
    uptime = time.time() - start_time
    return HealthResponse(uptime_seconds=round(uptime, 2))


@app.get("/farms/{farm_id}/lots", response_model=LotsResponse, tags=["Plantation"])
async def get_lots_summary(
    farm_id: str = Path(..., description="Farm identifier"),
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Limit number of lots returned"
    ),
    min_maturity: Optional[float] = Query(
        None, ge=0, le=100, description="Filter by minimum maturity percentage"
    ),
    db: Session = Depends(get_db),
):
    """
    Get summary information for all plantation lots in a specific farm

    Returns aggregated data including:
    - Total trees per lot
    - Health status
    - Security events count
    - Average maturity and fungal threat levels
    """
    try:
        farm = FarmService.validate_farm_exists(db, farm_id)
        return LotService.get_lots_summary(db, farm, limit, min_maturity)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching lots data: {str(e)}"
        )


@app.get(
    "/farms/{farm_id}/security/events",
    response_model=SecurityEventsResponse,
    tags=["Security"],
)
async def get_security_events(
    farm_id: str = Path(..., description="Farm identifier"),
    lot_id: Optional[int] = Query(None, ge=1, description="Filter by specific lot ID"),
    severity: Optional[SecurityLevel] = Query(
        None, description="Filter by severity level"
    ),
    unresolved_only: bool = Query(False, description="Show only unresolved events"),
    limit: Optional[int] = Query(
        50, ge=1, le=500, description="Limit number of events returned"
    ),
    db: Session = Depends(get_db),
):
    """
    Get security events from a specific farm's plantation

    Security events include:
    - Pest infestations
    - Disease outbreaks
    - Weather damage
    - Theft attempts
    - Equipment malfunctions
    """
    try:
        farm = FarmService.validate_farm_exists(db, farm_id)
        return SecurityService.get_security_events(
            db, farm, lot_id, severity, unresolved_only, limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching security events: {str(e)}"
        )


@app.get("/farms/{farm_id}/weather", response_model=WeatherResponse, tags=["Weather"])
async def get_weather_data(
    farm_id: str = Path(..., description="Farm identifier"),
    lot_ids: Optional[List[int]] = Query(
        None, description="Specific lot IDs to get weather for"
    ),
    db: Session = Depends(get_db),
):
    """
    Get current weather conditions for a specific farm's plantation lots

    Provides real-time weather data including:
    - Temperature and humidity
    - Rainfall measurements
    - Wind conditions
    - Weather condition classification
    """
    try:
        farm = FarmService.validate_farm_exists(db, farm_id)
        return WeatherService.get_weather_data(db, farm, lot_ids)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching weather data: {str(e)}"
        )


@app.get(
    "/farms/{farm_id}/analytics/production",
    response_model=AnalyticsResponse,
    tags=["Analytics"],
)
async def get_production_analytics(
    farm_id: str = Path(..., description="Farm identifier"),
    ready_threshold: float = Query(
        80.0, ge=0, le=100, description="Harvest readiness threshold percentage"
    ),
    db: Session = Depends(get_db),
):
    """
    Get production analytics and harvest predictions for a specific farm

    Provides insights into:
    - Estimated yield per lot
    - Harvest readiness assessment
    - Quality scores
    - Optimal harvest timing
    """
    try:
        farm = FarmService.validate_farm_exists(db, farm_id)
        return AnalyticsService.get_production_analytics(db, farm, ready_threshold)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating production analytics: {str(e)}"
        )


# Query profiling and performance monitoring endpoints
@app.get("/debug/query-stats", response_model=dict, tags=["Debug"])
async def get_query_performance_stats():
    """
    Get database query performance statistics

    Returns metrics about query execution times, slow queries, and overall performance
    """
    stats = get_query_stats()
    return {
        "query_performance": stats,
        "timestamp": datetime.now().isoformat(),
        "note": "Use this endpoint to monitor query performance and identify bottlenecks",
    }


@app.post("/debug/reset-query-stats", response_model=dict, tags=["Debug"])
async def reset_query_performance_stats():
    """
    Reset query performance statistics

    Clears all collected query performance data and starts fresh monitoring
    """
    reset_query_stats()
    return {
        "message": "Query performance statistics have been reset",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/debug/enable-detailed-logging", response_model=dict, tags=["Debug"])
async def enable_query_logging():
    """
    Enable detailed SQL query logging

    This will log all database queries with their execution times for debugging purposes.
    WARNING: This can generate a lot of log output and should only be used for debugging.
    """
    enable_detailed_query_logging()
    return {
        "message": "Detailed query logging has been enabled",
        "warning": "This will generate verbose logs. Use disable-detailed-logging to turn off.",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/debug/disable-detailed-logging", response_model=dict, tags=["Debug"])
async def disable_query_logging():
    """
    Disable detailed SQL query logging

    Returns to normal logging mode where only slow queries (>500ms) are logged
    """
    disable_detailed_query_logging()
    return {
        "message": "Detailed query logging has been disabled",
        "note": "Only slow queries (>500ms) will be logged now",
        "timestamp": datetime.now().isoformat(),
    }


# Additional utility endpoints
@app.get("/farms", response_model=dict, tags=["System"])
async def list_farms(db: Session = Depends(get_db)):
    """List all available farms"""
    farms_data = FarmService.get_all_farms(db)
    farms = [
        farm["slug"] for farm in farms_data
    ]  # Return slugs for backward compatibility
    return {
        "farms": farms,
        "total_farms": len(farms),
        "farms_data": farms_data,  # Include full farm data
    }


@app.get(
    "/farms/{farm_id}/lots/{lot_id}/trees", response_model=dict, tags=["Plantation"]
)
async def get_lot_trees(
    farm_id: str = Path(..., description="Farm identifier"),
    lot_id: int = Path(..., description="Lot identifier"),
    limit: Optional[int] = Query(
        None, ge=1, le=1000, description="Limit number of trees returned"
    ),
    db: Session = Depends(get_db),
):
    """Get detailed tree data for a specific lot in a farm"""
    try:
        farm = FarmService.validate_farm_exists(db, farm_id)

        # Get the lot
        lot = (
            db.query(Lot)
            .filter(Lot.farm_id == farm.id, Lot.lot_number == lot_id)
            .first()
        )

        if not lot:
            raise HTTPException(
                status_code=404, detail="Lot {lot_id} not found in farm {farm_id}"
            )

        # Batch fetch trees with their locations in a single query
        trees_query = text(
            """
            SELECT
                t.tree_code, t.variety, t.health_status,
                t.maturity_index, t.height_meters, t.age_years,
                ST_Y(t.location::geometry) as lat,
                ST_X(t.location::geometry) as lng
            FROM trees t
            WHERE t.lot_id = :lot_id
            ORDER BY t.tree_code
            {:limit_clause}
        """.replace(
                "{:limit_clause}", "LIMIT {limit}" if limit else ""
            )
        )

        trees_with_locations = db.execute(trees_query, {"lot_id": lot.id}).fetchall()

        # Convert to response format
        trees_data = []
        for tree_data in trees_with_locations:
            tree_info = {
                "id": tree_data.tree_code,
                "variety": tree_data.variety,
                "health_status": tree_data.health_status,
                "maturity_index": (
                    float(tree_data.maturity_index) if tree_data.maturity_index else 0
                ),
                "height_meters": (
                    float(tree_data.height_meters) if tree_data.height_meters else 0
                ),
                "age_years": tree_data.age_years,
                "location": {
                    "latitude": float(tree_data.lat) if tree_data.lat else 0,
                    "longitude": float(tree_data.lng) if tree_data.lng else 0,
                },
            }
            trees_data.append(tree_info)

        return {
            "trees": trees_data,
            "total_trees": len(trees_data),
            "lot_id": lot_id,
            "farm_id": farm_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching trees data: {str(e)}"
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
