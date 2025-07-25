#!/usr/bin/env python3
"""
Theobroma Geo API - Database Connection Test and Setup
Tests connection to the staging PostgreSQL database and sets up PostGIS with sample data
"""

import logging
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration - Use environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "theobroma_geo_dev"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

# Validate required environment variables
if not DB_CONFIG["password"]:
    logger.error("❌ Error: DB_PASSWORD environment variable is required")
    logger.error("💡 Usage: DB_PASSWORD='your-password' python test-db-connection.py")
    logger.error("💡 Or set all DB_* environment variables in your .env file")
    sys.exit(1)


def test_connection():
    """Test database connection"""
    try:
        logger.info("🔌 Testing database connection...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Test basic connectivity
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info("✅ Connected successfully!")
        logger.info("📊 PostgreSQL version: {version}")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error("❌ Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error("❌ Unexpected error: {e}")
        return False


def setup_postgis():
    """Enable PostGIS extension"""
    try:
        logger.info("🗺️  Setting up PostGIS extension...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Enable PostGIS extensions
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")

        # Check PostGIS version
        cursor.execute("SELECT PostGIS_Version();")
        postgis_version = cursor.fetchone()[0]
        logger.info("✅ PostGIS enabled! Version: {postgis_version}")

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error("❌ PostGIS setup failed: {e}")
        return False


def create_tables():
    """Create the database schema"""
    try:
        logger.info("🏗️  Creating database tables...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create farms table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                location GEOGRAPHY(POINT, 4326) NOT NULL,
                total_area_hectares DECIMAL(10,2),
                established_date DATE,
                contact_email VARCHAR(255),
                contact_phone VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Create lots table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lots (
                id SERIAL PRIMARY KEY,
                farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
                lot_number INTEGER NOT NULL,
                area_hectares DECIMAL(8,2) NOT NULL,
                tree_density INTEGER DEFAULT 0,
                soil_type VARCHAR(100),
                elevation_meters INTEGER,
                boundary GEOGRAPHY(POLYGON, 4326),
                centroid GEOGRAPHY(POINT, 4326),
                planting_date DATE,
                last_harvest DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_id, lot_number)
            );
        """
        )

        # Create trees table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trees (
                id SERIAL PRIMARY KEY,
                farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
                lot_id INTEGER REFERENCES lots(id) ON DELETE CASCADE,
                tree_code VARCHAR(50) UNIQUE NOT NULL,
                location GEOGRAPHY(POINT, 4326) NOT NULL,
                variety VARCHAR(100),
                planting_date DATE,
                age_years INTEGER,
                height_meters DECIMAL(4,2),
                trunk_diameter_cm DECIMAL(5,2),
                health_status VARCHAR(50) DEFAULT 'healthy',
                last_inspection DATE,
                maturity_index DECIMAL(5,2) DEFAULT 0.0,
                fungal_threat_level DECIMAL(5,2) DEFAULT 0.0,
                security_events_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        )

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIST(location);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lots_boundary ON lots USING GIST(boundary);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lots_centroid ON lots USING GIST(centroid);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trees_location ON trees USING GIST(location);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trees_farm_lot ON trees(farm_id, lot_id);"
        )

        conn.commit()
        logger.info("✅ Tables created successfully!")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error("❌ Table creation failed: {e}")
        return False


def insert_sample_data():
    """Insert sample farms and lots data"""
    try:
        logger.info("🌱 Inserting sample data...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Insert sample farms
        farms_data = [
            (
                "Fazenda Bahia",
                "fazenda-bahia",
                "POINT(-39.0639 -14.2350)",
                150.5,
                "2010-03-15",
                "contato@fazendabahia.com.br",
                "+55 73 3234-5678",
            ),
            (
                "Fazenda Espírito Santo",
                "fazenda-espirito-santo",
                "POINT(-40.3372 -19.1834)",
                87.3,
                "2008-06-20",
                "gestao@fazendaes.com.br",
                "+55 27 3345-6789",
            ),
            (
                "Fazenda Pará",
                "fazenda-para",
                "POINT(-49.2044 -2.5297)",
                203.8,
                "2012-09-10",
                "admin@fazendapara.com.br",
                "+55 91 3456-7890",
            ),
        ]

        for farm in farms_data:
            cursor.execute(
                """
                INSERT INTO farms (name, slug, location, total_area_hectares, established_date, contact_email, contact_phone)
                VALUES (%s, %s, ST_GeogFromText(%s), %s, %s, %s, %s)
                ON CONFLICT (slug) DO NOTHING;
            """,
                (
                    farm[0],
                    farm[1],
                    "SRID=4326;{farm[2]}",
                    farm[3],
                    farm[4],
                    farm[5],
                    farm[6],
                ),
            )

        # Get the farm ID for Fazenda Bahia
        cursor.execute("SELECT id FROM farms WHERE slug = 'fazenda-bahia';")
        bahia_farm_id = cursor.fetchone()[0]

        # Insert sample lots for Fazenda Bahia
        lots_data = [
            (
                bahia_farm_id,
                1,
                12.5,
                180,
                "Clay loam",
                85,
                "POLYGON((-39.0650 -14.2340, -39.0640 -14.2340, -39.0640 -14.2360, -39.0650 -14.2360, -39.0650 -14.2340))",
                "POINT(-39.0645 -14.2350)",
                "2010-04-01",
            ),
            (
                bahia_farm_id,
                2,
                15.8,
                165,
                "Sandy loam",
                92,
                "POLYGON((-39.0640 -14.2340, -39.0620 -14.2340, -39.0620 -14.2365, -39.0640 -14.2365, -39.0640 -14.2340))",
                "POINT(-39.0630 -14.2352)",
                "2010-05-15",
            ),
            (
                bahia_farm_id,
                3,
                18.2,
                195,
                "Loam",
                78,
                "POLYGON((-39.0620 -14.2340, -39.0595 -14.2340, -39.0595 -14.2370, -39.0620 -14.2370, -39.0620 -14.2340))",
                "POINT(-39.0607 -14.2355)",
                "2010-06-10",
            ),
        ]

        for lot in lots_data:
            cursor.execute(
                """
                INSERT INTO lots (farm_id, lot_number, area_hectares, tree_density, soil_type, elevation_meters, boundary, centroid, planting_date)
                VALUES (%s, %s, %s, %s, %s, %s, ST_GeogFromText(%s), ST_GeogFromText(%s), %s)
                ON CONFLICT (farm_id, lot_number) DO NOTHING;
            """,
                (
                    lot[0],
                    lot[1],
                    lot[2],
                    lot[3],
                    lot[4],
                    lot[5],
                    "SRID=4326;{lot[6]}",
                    "SRID=4326;{lot[7]}",
                    lot[8],
                ),
            )

        conn.commit()
        logger.info("✅ Sample data inserted successfully!")

        # Verify data
        cursor.execute("SELECT COUNT(*) FROM farms;")
        farm_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM lots;")
        lot_count = cursor.fetchone()[0]

        logger.info("📊 Database contains {farm_count} farms and {lot_count} lots")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error("❌ Sample data insertion failed: {e}")
        return False


def create_views():
    """Create useful views for the API"""
    try:
        logger.info("📈 Creating database views...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Farm summary view
        cursor.execute(
            """
            CREATE OR REPLACE VIEW farm_summary AS
            SELECT
                f.id,
                f.name,
                f.slug,
                f.total_area_hectares,
                COUNT(DISTINCT l.id) as total_lots,
                COUNT(t.id) as total_trees,
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat,
                COALESCE(SUM(t.security_events_count), 0) as total_security_events,
                ST_AsText(f.location) as location_wkt
            FROM farms f
            LEFT JOIN lots l ON f.id = l.farm_id
            LEFT JOIN trees t ON f.id = t.farm_id
            GROUP BY f.id, f.name, f.slug, f.total_area_hectares, f.location;
        """
        )

        # Lot summary view
        cursor.execute(
            """
            CREATE OR REPLACE VIEW lot_summary AS
            SELECT
                l.id,
                l.farm_id,
                f.name as farm_name,
                l.lot_number,
                l.area_hectares,
                l.tree_density,
                l.soil_type,
                l.elevation_meters,
                COUNT(t.id) as tree_count,
                COALESCE(AVG(t.maturity_index), 0) as avg_maturity,
                COALESCE(AVG(t.fungal_threat_level), 0) as avg_fungal_threat,
                COALESCE(AVG(t.height_meters), 0) as avg_height,
                COALESCE(SUM(t.security_events_count), 0) as security_events,
                ST_AsText(l.centroid) as centroid_wkt,
                ST_Area(l.boundary) as boundary_area_sq_meters
            FROM lots l
            JOIN farms f ON l.farm_id = f.id
            LEFT JOIN trees t ON l.id = t.lot_id
            GROUP BY l.id, l.farm_id, f.name, l.lot_number, l.area_hectares, l.tree_density, l.soil_type, l.elevation_meters, l.centroid, l.boundary;
        """
        )

        conn.commit()
        logger.info("✅ Views created successfully!")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        logger.error("❌ View creation failed: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("🌱 Starting Theobroma Geo API Database Setup...")

    success = True

    # Test connection
    if not test_connection():
        logger.error("❌ Database connection failed. Setup aborted.")
        sys.exit(1)

    # Setup PostGIS
    if not setup_postgis():
        success = False

    # Create tables
    if not create_tables():
        success = False

    # Insert sample data
    if not insert_sample_data():
        success = False

    # Create views
    if not create_views():
        success = False

    if success:
        logger.info("")
        logger.info("✅ Database setup completed successfully!")
        logger.info("")
        logger.info("🔗 Connection details:")
        logger.info("   Host: {DB_CONFIG['host']}")
        logger.info("   Database: {DB_CONFIG['database']}")
        logger.info("   Username: {DB_CONFIG['user']}")
        logger.info("")
        logger.info("🚀 Your staging database is ready for use!")
        logger.info("   - PostGIS extensions enabled")
        logger.info("   - Sample farms and lots data loaded")
        logger.info("   - Views created for API queries")
        logger.info("")
        logger.info("🌐 Access from staging.theobroma.digital is configured")
        logger.info("🏠 Local access is configured for your IP")
    else:
        logger.error("❌ Database setup completed with errors!")
        sys.exit(1)


if __name__ == "__main__":
    main()
