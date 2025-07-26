"""
Database configuration and models for Theobroma Geo API
PostgreSQL with PostGIS integration using SQLAlchemy
"""

import logging
import os
import time

from dotenv import load_dotenv
from geoalchemy2 import Geography
from sqlalchemy import (
    DECIMAL,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

# Load environment variables
load_dotenv()

# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://theobroma_admin:TheobromaGeo2024!@theobroma-geo-db-staging.cjnrvqevfppv.us-east-2.rds.amazonaws.com:5432/theobroma_geo_staging",
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Set to True for SQL query logging
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure logging for query profiling
logging.basicConfig()
query_logger = logging.getLogger("sqlalchemy.query_profiler")
query_logger.setLevel(logging.INFO)

# Query performance tracking
query_stats = {"total_queries": 0, "slow_queries": [], "query_times": []}


# SQLAlchemy event listeners for query profiling
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Record query start time"""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Record query end time and log slow queries"""
    total_time = time.time() - context._query_start_time

    # Update global stats
    query_stats["total_queries"] += 1
    query_stats["query_times"].append(total_time)

    # Define slow query threshold (500ms)
    slow_query_threshold = 0.5

    if total_time > slow_query_threshold:
        # Log slow queries
        slow_query_info = {
            "query": statement,
            "parameters": parameters,
            "execution_time": round(total_time, 4),
            "timestamp": time.time(),
        }

        query_stats["slow_queries"].append(slow_query_info)

        # Keep only last 50 slow queries to prevent memory issues
        if len(query_stats["slow_queries"]) > 50:
            query_stats["slow_queries"] = query_stats["slow_queries"][-50:]

        query_logger.warning(
            "SLOW QUERY ({total_time:.4f}s): {statement[:200]}{'...' if len(statement) > 200 else ''}"
        )

    # Log all queries if detailed logging is enabled
    if query_logger.level <= logging.DEBUG:
        query_logger.debug(
            "QUERY ({total_time:.4f}s): {statement[:100]}{'...' if len(statement) > 100 else ''}"
        )


def get_query_stats():
    """Get current query performance statistics"""
    total_queries = query_stats["total_queries"]
    query_times = query_stats["query_times"]

    if not query_times:
        return {
            "total_queries": 0,
            "avg_query_time": 0,
            "max_query_time": 0,
            "min_query_time": 0,
            "slow_queries_count": 0,
            "recent_slow_queries": [],
        }

    return {
        "total_queries": total_queries,
        "avg_query_time": round(sum(query_times) / len(query_times), 4),
        "max_query_time": round(max(query_times), 4),
        "min_query_time": round(min(query_times), 4),
        "slow_queries_count": len(query_stats["slow_queries"]),
        "recent_slow_queries": query_stats["slow_queries"][
            -10:
        ],  # Last 10 slow queries
    }


def reset_query_stats():
    """Reset query performance statistics"""
    global query_stats
    query_stats = {"total_queries": 0, "slow_queries": [], "query_times": []}


def enable_detailed_query_logging():
    """Enable detailed query logging for debugging"""
    query_logger.setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def disable_detailed_query_logging():
    """Disable detailed query logging"""
    query_logger.setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# Create declarative base
Base = declarative_base()


# Database dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# SQLAlchemy Models
class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    total_area_hectares = Column(DECIMAL(10, 2))
    established_date = Column(Date)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    lots = relationship("Lot", back_populates="farm", cascade="all, delete-orphan")
    trees = relationship("Tree", back_populates="farm", cascade="all, delete-orphan")


class Lot(Base):
    __tablename__ = "lots"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(
        Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    lot_number = Column(Integer, nullable=False)
    area_hectares = Column(DECIMAL(8, 2), nullable=False)
    tree_density = Column(Integer, default=0)
    soil_type = Column(String(100))
    elevation_meters = Column(Integer)
    boundary = Column(Geography(geometry_type="POLYGON", srid=4326))
    centroid = Column(Geography(geometry_type="POINT", srid=4326))
    planting_date = Column(Date)
    last_harvest = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farm = relationship("Farm", back_populates="lots")
    trees = relationship("Tree", back_populates="lot", cascade="all, delete-orphan")


class Tree(Base):
    __tablename__ = "trees"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(
        Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    lot_id = Column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    tree_code = Column(String(50), unique=True, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    variety = Column(String(100))
    planting_date = Column(Date)
    age_years = Column(Integer)
    height_meters = Column(DECIMAL(4, 2))
    trunk_diameter_cm = Column(DECIMAL(5, 2))
    health_status = Column(String(50), default="healthy")
    last_inspection = Column(Date)
    maturity_index = Column(DECIMAL(5, 2), default=0.0)
    fungal_threat_level = Column(DECIMAL(5, 2), default=0.0)
    security_events_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    farm = relationship("Farm", back_populates="trees")
    lot = relationship("Lot", back_populates="trees")


# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


# Test database connection
def test_connection():
    """Test database connectivity"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
