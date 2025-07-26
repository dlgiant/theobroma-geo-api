"""
Service layer for Theobroma Geo API
Database operations and business logic
"""

import random
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database import Farm, Lot, Tree
from models import (
    AnalyticsResponse,
    LotsResponse,
    LotSummary,
    ProductionMetrics,
    SecurityEvent,
    SecurityEventsResponse,
    SecurityLevel,
    TreeLocation,
    WeatherCondition,
    WeatherData,
    WeatherResponse,
)


class FarmService:
    """Service for farm-related operations"""

    @staticmethod
    def get_all_farms(db: Session) -> List[dict]:
        """Get all farms with basic information using batch fetching"""
        # Batch fetch all farms with their locations in a single query
        farms_with_locations = db.execute(
            text(
                """
            SELECT
                f.id, f.name, f.slug, f.total_area_hectares, f.established_date,
                ST_Y(f.location::geometry) as lat,
                ST_X(f.location::geometry) as lng
            FROM farms f
            ORDER BY f.name
        """
            )
        ).fetchall()

        result = []
        for farm_data in farms_with_locations:
            result.append(
                {
                    "id": farm_data.id,
                    "name": farm_data.name,
                    "slug": farm_data.slug,
                    "location": {
                        "latitude": float(farm_data.lat) if farm_data.lat else 0,
                        "longitude": float(farm_data.lng) if farm_data.lng else 0,
                    },
                    "total_area_hectares": (
                        float(farm_data.total_area_hectares)
                        if farm_data.total_area_hectares
                        else 0
                    ),
                    "established_date": (
                        farm_data.established_date.isoformat()
                        if farm_data.established_date
                        else None
                    ),
                }
            )

        return result

    @staticmethod
    def get_farm_by_slug(db: Session, farm_slug: str) -> Optional[Farm]:
        """Get farm by slug"""
        return db.query(Farm).filter(Farm.slug == farm_slug).first()

    @staticmethod
    def validate_farm_exists(db: Session, farm_id: str) -> Farm:
        """Validate that farm exists, raise HTTPException if not"""
        from fastapi import HTTPException

        farm = db.query(Farm).filter(Farm.slug == farm_id).first()
        if not farm:
            available_farms = [f.slug for f in db.query(Farm).all()]
            raise HTTPException(
                status_code=404,
                detail=f"Farm '{farm_id}' not found. Available farms: {available_farms}",
            )
        return farm


class LotService:
    """Service for lot-related operations"""

    @staticmethod
    def get_lots_summary(
        db: Session,
        farm: Farm,
        limit: Optional[int] = None,
        min_maturity: Optional[float] = None,
    ) -> LotsResponse:
        """Get lots summary for a farm using batch fetching"""

        # Batch fetch all lot data with tree metrics in a single query
        base_query = text(
            """
            SELECT
                l.id as lot_db_id,
                l.lot_number,
                l.area_hectares,
                COUNT(t.id) as tree_count,
                COUNT(CASE WHEN t.health_status IN ('healthy', 'excellent', 'good') THEN 1 END) as healthy_trees,
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat,
                COALESCE(SUM(t.security_events_count), 0) as security_events
            FROM lots l
            LEFT JOIN trees t ON l.id = t.lot_id
            WHERE l.farm_id = :farm_id
            GROUP BY l.id, l.lot_number, l.area_hectares
            ORDER BY l.lot_number
        """
        )

        lots_data = db.execute(base_query, {"farm_id": farm.id}).fetchall()

        lot_summaries = []
        total_trees = 0
        total_area = 0

        for lot_data in lots_data:
            avg_maturity = float(lot_data.avg_maturity) if lot_data.avg_maturity else 0

            # Apply maturity filter
            if min_maturity and avg_maturity < min_maturity:
                continue

            lot_summary = LotSummary(
                lot_id=lot_data.lot_number,
                total_trees=int(lot_data.tree_count) if lot_data.tree_count else 0,
                healthy_trees=(
                    int(lot_data.healthy_trees) if lot_data.healthy_trees else 0
                ),
                security_events=(
                    int(lot_data.security_events) if lot_data.security_events else 0
                ),
                avg_maturity=avg_maturity,
                avg_fungal_threat=(
                    float(lot_data.avg_fungal_threat)
                    if lot_data.avg_fungal_threat
                    else 0
                ),
                area_hectares=float(lot_data.area_hectares),
                last_inspection=datetime.now(),  # Mock data - could be updated with real inspection dates
            )

            lot_summaries.append(lot_summary)
            total_trees += lot_summary.total_trees
            total_area += float(lot_data.area_hectares)

            # Apply limit
            if limit and len(lot_summaries) >= limit:
                break

        return LotsResponse(
            lots=lot_summaries,
            total_lots=len(lot_summaries),
            total_area=total_area,
            total_trees=total_trees,
        )


class SecurityService:
    """Service for security-related operations"""

    @staticmethod
    def get_security_events(
        db: Session,
        farm: Farm,
        lot_id: Optional[int] = None,
        severity: Optional[SecurityLevel] = None,
        unresolved_only: bool = False,
        limit: int = 50,
    ) -> SecurityEventsResponse:
        """Get security events for a farm"""

        # Build optimized query to get all needed data in one go
        query = text(
            """
            SELECT
                t.id, t.tree_code, t.security_events_count, t.lot_id,
                l.lot_number,
                ST_Y(t.location::geometry) as lat,
                ST_X(t.location::geometry) as lng
            FROM trees t
            JOIN lots l ON t.lot_id = l.id
            WHERE t.farm_id = :farm_id
                AND t.security_events_count > 0
                AND (:lot_id IS NULL OR l.lot_number = :lot_id)
            LIMIT 200  -- Limit trees to prevent excessive processing
        """
        )

        trees_data = db.execute(
            query, {"farm_id": farm.id, "lot_id": lot_id}
        ).fetchall()

        all_events = []

        # Generate mock security events based on tree data
        for tree_data in trees_data:
            # Limit events per tree to keep response manageable
            events_to_generate = min(tree_data.security_events_count, 2)

            for i in range(events_to_generate):
                event_types = [
                    "Pest infestation",
                    "Disease outbreak",
                    "Weather damage",
                    "Equipment malfunction",
                ]
                severities = [
                    SecurityLevel.LOW,
                    SecurityLevel.MEDIUM,
                    SecurityLevel.HIGH,
                    SecurityLevel.CRITICAL,
                ]

                selected_severity = random.choice(severities)
                if severity and selected_severity != severity:
                    continue

                is_resolved = random.choice([True, False])
                if unresolved_only and is_resolved:
                    continue

                event = SecurityEvent(
                    id="evt_{tree_data.id}_{i+1}",
                    tree_id=tree_data.tree_code,
                    lot_id=tree_data.lot_number,
                    event_type=random.choice(event_types),
                    severity=selected_severity,
                    description="Security event detected on tree {tree_data.tree_code}",
                    location=TreeLocation(
                        latitude=float(tree_data.lat) if tree_data.lat else 0,
                        longitude=float(tree_data.lng) if tree_data.lng else 0,
                    ),
                    timestamp=datetime.now(),
                    resolved=is_resolved,
                )
                all_events.append(event)

                # Early exit if we have enough events
                if len(all_events) >= limit * 2:  # Allow some buffer for filtering
                    break

            if len(all_events) >= limit * 2:
                break

        # Sort by severity and timestamp
        all_events.sort(
            key=lambda x: (x.severity == SecurityLevel.CRITICAL, x.timestamp),
            reverse=True,
        )

        # Apply limit
        limited_events = all_events[:limit] if limit else all_events

        # Calculate stats
        critical_events = len(
            [e for e in all_events if e.severity == SecurityLevel.CRITICAL]
        )
        unresolved_events = len([e for e in all_events if not e.resolved])

        return SecurityEventsResponse(
            events=limited_events,
            total_events=len(all_events),
            critical_events=critical_events,
            unresolved_events=unresolved_events,
        )


class WeatherService:
    """Service for weather-related operations"""

    @staticmethod
    def get_weather_data(
        db: Session, farm: Farm, lot_ids: Optional[List[int]] = None
    ) -> WeatherResponse:
        """Get weather data for farm lots"""

        lots_query = db.query(Lot).filter(Lot.farm_id == farm.id)

        if lot_ids:
            lots_query = lots_query.filter(Lot.lot_number.in_(lot_ids))

        lots = lots_query.all()
        weather_data = []
        favorable_conditions = 0
        weather_alerts = 0

        conditions = [
            WeatherCondition.SUNNY,
            WeatherCondition.CLOUDY,
            WeatherCondition.RAINY,
        ]

        for lot in lots:
            # Generate mock weather data
            temperature = random.uniform(18, 35)
            humidity = random.uniform(40, 90)
            rainfall = random.uniform(0, 25)
            wind_speed = random.uniform(5, 45)

            weather = WeatherData(
                lot_id=lot.lot_number,
                condition=random.choice(conditions),
                temperature=temperature,
                humidity=humidity,
                rainfall=rainfall,
                wind_speed=wind_speed,
                timestamp=datetime.now(),
            )
            weather_data.append(weather)

            # Check for favorable conditions
            if 24 <= temperature <= 30 and 65 <= humidity <= 85 and rainfall < 10:
                favorable_conditions += 1

            # Check for weather alerts
            if temperature > 35 or temperature < 18 or rainfall > 30 or wind_speed > 40:
                weather_alerts += 1

        return WeatherResponse(
            current_weather=weather_data,
            favorable_conditions=favorable_conditions,
            weather_alerts=weather_alerts,
        )


class AnalyticsService:
    """Service for analytics and production metrics"""

    @staticmethod
    def get_production_analytics(
        db: Session, farm: Farm, ready_threshold: float = 80.0
    ) -> AnalyticsResponse:
        """Get production analytics for a farm using batch fetching"""

        # Batch fetch all lot analytics data in a single query
        analytics_query = text(
            """
            SELECT
                l.lot_number,
                l.area_hectares,
                COUNT(t.id) as tree_count,
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.height_meters), 0) as avg_height,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat
            FROM lots l
            LEFT JOIN trees t ON l.id = t.lot_id
            WHERE l.farm_id = :farm_id
            GROUP BY l.id, l.lot_number, l.area_hectares
            ORDER BY l.lot_number
        """
        )

        lots_analytics = db.execute(analytics_query, {"farm_id": farm.id}).fetchall()

        production_metrics = []
        total_estimated_yield = 0
        quality_scores = []
        lots_ready_for_harvest = 0

        for lot_data in lots_analytics:
            tree_count = int(lot_data.tree_count) if lot_data.tree_count else 0
            avg_maturity = float(lot_data.avg_maturity) if lot_data.avg_maturity else 0
            avg_fungal_threat = (
                float(lot_data.avg_fungal_threat) if lot_data.avg_fungal_threat else 0
            )

            # Calculate estimated yield (mock calculation)
            area_hectares = float(lot_data.area_hectares)
            yield_per_hectare = max(
                0, (avg_maturity / 100) * tree_count * 0.5
            )  # Mock formula
            estimated_yield = area_hectares * yield_per_hectare

            # Calculate quality score
            quality_score = max(0, 100 - avg_fungal_threat + (avg_maturity * 0.5))
            quality_score = min(100, quality_score)  # Cap at 100

            metrics = ProductionMetrics(
                lot_id=lot_data.lot_number,
                estimated_yield=estimated_yield,
                harvest_readiness=avg_maturity,
                quality_score=quality_score,
                optimal_harvest_date=(
                    datetime.now() if avg_maturity >= ready_threshold else None
                ),
            )

            production_metrics.append(metrics)
            total_estimated_yield += estimated_yield
            quality_scores.append(quality_score)

            if avg_maturity >= ready_threshold:
                lots_ready_for_harvest += 1

        average_quality_score = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        )

        return AnalyticsResponse(
            production_metrics=production_metrics,
            total_estimated_yield=round(total_estimated_yield, 1),
            average_quality_score=round(average_quality_score, 1),
            lots_ready_for_harvest=lots_ready_for_harvest,
        )
