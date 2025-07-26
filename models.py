from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TreeStatus(str, Enum):
    HEALTHY = "healthy"
    DISEASED = "diseased"
    DAMAGED = "damaged"
    MATURE = "mature"
    YOUNG = "young"


class WeatherCondition(str, Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"


# Tree Models
class TreeLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    altitude: Optional[float] = Field(None, description="Altitude in meters")


class TreeMetrics(BaseModel):
    maturity_index: float = Field(
        ..., ge=0, le=100, description="Maturity percentage (0-100)"
    )
    security_events: int = Field(
        default=0, ge=0, description="Number of security events"
    )
    fungal_threat: float = Field(
        ..., ge=0, le=100, description="Fungal threat level (0-100)"
    )
    canopy_grading: float = Field(..., ge=0, le=100, description="Canopy grade (0-100)")
    tree_age: int = Field(..., ge=1, description="Tree age in years")
    tree_density: float = Field(..., ge=0, le=100, description="Tree density (0-100)")


class Tree(BaseModel):
    id: str = Field(..., description="Unique tree identifier")
    farm_id: str = Field(..., description="Farm identifier")
    lot_id: int = Field(..., ge=1, description="Lot number")
    location: TreeLocation
    metrics: TreeMetrics
    status: TreeStatus
    last_updated: datetime = Field(default_factory=datetime.now)


# Lot Models
class LotSummary(BaseModel):
    lot_id: int = Field(..., ge=1, description="Lot identifier")
    total_trees: int = Field(..., ge=0)
    healthy_trees: int = Field(..., ge=0)
    security_events: int = Field(..., ge=0)
    avg_maturity: float = Field(..., ge=0, le=100)
    avg_fungal_threat: float = Field(..., ge=0, le=100)
    area_hectares: float = Field(..., gt=0)
    last_inspection: datetime


class LotsResponse(BaseModel):
    lots: List[LotSummary]
    total_lots: int
    total_area: float
    total_trees: int


# Security Models
class SecurityEvent(BaseModel):
    id: str = Field(..., description="Event identifier")
    tree_id: str = Field(..., description="Affected tree ID")
    lot_id: int = Field(..., ge=1)
    event_type: str = Field(..., description="Type of security event")
    severity: SecurityLevel
    description: str
    location: TreeLocation
    timestamp: datetime
    resolved: bool = Field(default=False)


class SecurityEventsResponse(BaseModel):
    events: List[SecurityEvent]
    total_events: int
    critical_events: int
    unresolved_events: int


# Weather Models
class WeatherData(BaseModel):
    lot_id: int = Field(..., ge=1)
    condition: WeatherCondition
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    rainfall: float = Field(..., ge=0, description="Rainfall in mm")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    timestamp: datetime


class WeatherResponse(BaseModel):
    current_weather: List[WeatherData]
    favorable_conditions: int = Field(
        ..., description="Number of lots with favorable conditions"
    )
    weather_alerts: int = Field(..., description="Number of weather-related alerts")


# Analytics Models
class ProductionMetrics(BaseModel):
    lot_id: int
    estimated_yield: float = Field(..., ge=0, description="Estimated yield in kg")
    harvest_readiness: float = Field(
        ..., ge=0, le=100, description="Harvest readiness percentage"
    )
    quality_score: float = Field(..., ge=0, le=100, description="Quality score")
    optimal_harvest_date: Optional[datetime] = Field(
        None, description="Optimal harvest date"
    )


class AnalyticsResponse(BaseModel):
    production_metrics: List[ProductionMetrics]
    total_estimated_yield: float
    average_quality_score: float
    lots_ready_for_harvest: int


# General Response Models
class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    uptime_seconds: float
    database: Optional[str] = None
    environment: Optional[str] = None
    database_url_set: Optional[bool] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
