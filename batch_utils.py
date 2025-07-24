"""
Batch fetching utilities for Theobroma Geo API
Optimized database operations to eliminate N+1 query problems
"""

from typing import Any, Dict, List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from database import Farm, Lot, Tree


class BatchFetcher:
    """Utility class for batch fetching database records"""

    @staticmethod
    def get_farms_with_locations(
        db: Session, farm_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch fetch farms with their geographic locations

        Args:
            db: Database session
            farm_ids: Optional list of farm IDs to filter by

        Returns:
            List of farm dictionaries with location data
        """
        where_clause = ""
        params = {}

        if farm_ids:
            where_clause = "WHERE f.id = ANY(:farm_ids)"
            params["farm_ids"] = farm_ids

        query = text(
            """
            SELECT
                f.id, f.name, f.slug, f.total_area_hectares, f.established_date,
                f.contact_email, f.contact_phone,
                ST_Y(f.location::geometry) as lat,
                ST_X(f.location::geometry) as lng
            FROM farms f
            {where_clause}
            ORDER BY f.name
        """
        )

        return db.execute(query, params).fetchall()

    @staticmethod
    def get_lots_with_tree_metrics(
        db: Session, farm_id: int, lot_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch fetch lots with aggregated tree metrics

        Args:
            db: Database session
            farm_id: Farm ID to filter by
            lot_ids: Optional list of lot numbers to filter by

        Returns:
            List of lot dictionaries with tree metrics
        """
        where_clause = "WHERE l.farm_id = :farm_id"
        params = {"farm_id": farm_id}

        if lot_ids:
            where_clause += " AND l.lot_number = ANY(:lot_ids)"
            params["lot_ids"] = lot_ids

        query = text(
            """
            SELECT
                l.id as lot_db_id,
                l.lot_number,
                l.area_hectares,
                l.tree_density,
                l.soil_type,
                l.elevation_meters,
                l.planting_date,
                l.last_harvest,
                COUNT(t.id) as tree_count,
                COUNT(CASE WHEN t.health_status IN ('healthy', 'excellent', 'good') THEN 1 END) as healthy_trees,
                COUNT(CASE WHEN t.health_status IN ('poor', 'critical', 'dead') THEN 1 END) as unhealthy_trees,
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.height_meters), 0) as avg_height,
                COALESCE(AVG(t.trunk_diameter_cm), 0) as avg_diameter,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat,
                COALESCE(SUM(t.security_events_count), 0) as total_security_events,
                MAX(t.last_inspection) as last_tree_inspection
            FROM lots l
            LEFT JOIN trees t ON l.id = t.lot_id
            {where_clause}
            GROUP BY l.id, l.lot_number, l.area_hectares, l.tree_density,
                     l.soil_type, l.elevation_meters, l.planting_date, l.last_harvest
            ORDER BY l.lot_number
        """
        )

        return db.execute(query, params).fetchall()

    @staticmethod
    def get_trees_with_locations(
        db: Session,
        lot_id: int,
        tree_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Batch fetch trees with their geographic locations

        Args:
            db: Database session
            lot_id: Lot ID to filter by
            tree_ids: Optional list of tree codes to filter by
            limit: Optional limit on number of results

        Returns:
            List of tree dictionaries with location data
        """
        where_clause = "WHERE t.lot_id = :lot_id"
        params = {"lot_id": lot_id}

        if tree_ids:
            where_clause += " AND t.tree_code = ANY(:tree_ids)"
            params["tree_ids"] = tree_ids

        limit_clause = "LIMIT {limit}" if limit else ""

        query = text(
            """
            SELECT
                t.id, t.tree_code, t.variety, t.planting_date, t.age_years,
                t.height_meters, t.trunk_diameter_cm, t.health_status,
                t.last_inspection, t.maturity_index, t.fungal_threat_level,
                t.security_events_count,
                ST_Y(t.location::geometry) as lat,
                ST_X(t.location::geometry) as lng
            FROM trees t
            {where_clause}
            ORDER BY t.tree_code
            {limit_clause}
        """
        )

        return db.execute(query, params).fetchall()

    @staticmethod
    def get_security_trees_with_locations(
        db: Session,
        farm_id: int,
        lot_id: Optional[int] = None,
        min_security_events: int = 1,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Batch fetch trees with security events including their locations

        Args:
            db: Database session
            farm_id: Farm ID to filter by
            lot_id: Optional lot number to filter by
            min_security_events: Minimum number of security events
            limit: Optional limit on number of results

        Returns:
            List of tree dictionaries with security and location data
        """
        where_clause = (
            "WHERE t.farm_id = :farm_id AND t.security_events_count >= :min_events"
        )
        params = {"farm_id": farm_id, "min_events": min_security_events}

        if lot_id:
            where_clause += " AND l.lot_number = :lot_id"
            params["lot_id"] = lot_id

        limit_clause = "LIMIT {limit}" if limit else ""

        query = text(
            """
            SELECT
                t.id, t.tree_code, t.security_events_count, t.lot_id,
                t.health_status, t.maturity_index, t.last_inspection,
                l.lot_number, l.area_hectares,
                ST_Y(t.location::geometry) as lat,
                ST_X(t.location::geometry) as lng
            FROM trees t
            JOIN lots l ON t.lot_id = l.id
            {where_clause}
            ORDER BY t.security_events_count DESC, t.last_inspection DESC
            {limit_clause}
        """
        )

        return db.execute(query, params).fetchall()

    @staticmethod
    def get_farm_analytics_summary(db: Session, farm_id: int) -> Dict[str, Any]:
        """
        Get comprehensive farm analytics in a single query

        Args:
            db: Database session
            farm_id: Farm ID to get analytics for

        Returns:
            Dictionary with comprehensive farm analytics
        """
        query = text(
            """
            SELECT
                -- Farm basics
                f.name as farm_name,
                f.slug as farm_slug,
                f.total_area_hectares as farm_area,

                -- Lot aggregates
                COUNT(DISTINCT l.id) as total_lots,
                SUM(l.area_hectares) as total_lot_area,

                -- Tree aggregates
                COUNT(t.id) as total_trees,
                COUNT(CASE WHEN t.health_status IN ('healthy', 'excellent', 'good') THEN 1 END) as healthy_trees,
                COUNT(CASE WHEN t.health_status IN ('poor', 'critical', 'dead') THEN 1 END) as unhealthy_trees,

                -- Tree metrics
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.height_meters), 0) as avg_height,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat,
                COALESCE(SUM(t.security_events_count), 0) as total_security_events,

                -- Date aggregates
                MAX(t.last_inspection) as last_inspection,
                MIN(t.planting_date) as oldest_planting,
                MAX(t.planting_date) as newest_planting

            FROM farms f
            LEFT JOIN lots l ON f.id = l.farm_id
            LEFT JOIN trees t ON l.id = t.lot_id
            WHERE f.id = :farm_id
            GROUP BY f.id, f.name, f.slug, f.total_area_hectares
        """
        )

        result = db.execute(query, {"farm_id": farm_id}).fetchone()
        return dict(result) if result else {}


class BatchQueryOptimizer:
    """Utilities for optimizing batch queries"""

    @staticmethod
    def chunk_ids(ids: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """
        Split a list of IDs into smaller chunks for batch processing

        Args:
            ids: List of IDs to chunk
            chunk_size: Maximum size of each chunk

        Returns:
            List of ID chunks
        """
        return [ids[i : i + chunk_size] for i in range(0, len(ids), chunk_size)]

    @staticmethod
    def build_in_clause_params(ids: List[Any], param_name: str) -> Dict[str, Any]:
        """
        Build parameters for IN clause queries

        Args:
            ids: List of IDs for IN clause
            param_name: Parameter name for the query

        Returns:
            Dictionary of query parameters
        """
        if not ids:
            return {}
        return {param_name: ids}

    @staticmethod
    def optimize_join_query(
        base_query: str,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """
        Add common optimizations to a join query

        Args:
            base_query: Base SQL query string
            filters: Dictionary of filter conditions
            order_by: Optional ORDER BY clause
            limit: Optional LIMIT clause

        Returns:
            Optimized SQL query string
        """
        query_parts = [base_query]

        # Add WHERE conditions
        if filters:
            where_conditions = []
            for key, value in filters.items():
                if value is not None:
                    if isinstance(value, list):
                        where_conditions.append("{key} = ANY(:{key.replace('.', '_')})")
                    else:
                        where_conditions.append("{key} = :{key.replace('.', '_')}")

            if where_conditions:
                query_parts.append("WHERE {' AND '.join(where_conditions)}")

        # Add ORDER BY
        if order_by:
            query_parts.append("ORDER BY {order_by}")

        # Add LIMIT
        if limit:
            query_parts.append("LIMIT {limit}")

        return "\n".join(query_parts)


class BatchCache:
    """Simple in-memory cache for batch fetched data"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self.default_ttl = 300  # 5 minutes

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get cached value if it exists and hasn't expired

        Args:
            key: Cache key
            ttl: Time to live in seconds (uses default if None)

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        import time

        ttl = ttl or self.default_ttl
        if time.time() - self._cache_timestamps[key] > ttl:
            self.delete(key)
            return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Set cached value with current timestamp

        Args:
            key: Cache key
            value: Value to cache
        """
        import time

        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """
        Delete cached value

        Args:
            key: Cache key to delete
        """
        self._cache.pop(key, None)
        self._cache_timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values"""
        self._cache.clear()
        self._cache_timestamps.clear()


# Global cache instance for batch operations
batch_cache = BatchCache()
