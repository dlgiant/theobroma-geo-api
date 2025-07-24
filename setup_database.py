#!/usr/bin/env python3
"""
Database setup script for Theobroma Geo API
Initializes PostGIS and populates sample data
"""

import os
import random
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment variables")
    exit(1)

print("🚀 Starting database setup...")
print(
    "📡 Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'database'}"
)


def get_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)


def setup_postgis():
    """Enable PostGIS extension"""
    print("🗺️ Setting up PostGIS extension...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Enable PostGIS extension
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")

            # Verify PostGIS installation
            cur.execute("SELECT PostGIS_Version();")
            version = cur.fetchone()[0]
            print("✅ PostGIS version: {version}")


def create_tables():
    """Create database tables"""
    print("🏗️ Creating database tables...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create farms table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS farms (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) UNIQUE NOT NULL,
                    location GEOGRAPHY(POINT, 4326) NOT NULL,
                    total_area_hectares DECIMAL(10, 2),
                    established_date DATE,
                    contact_email VARCHAR(255),
                    contact_phone VARCHAR(50),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
            )

            # Create lots table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS lots (
                    id SERIAL PRIMARY KEY,
                    farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
                    lot_number INTEGER NOT NULL,
                    area_hectares DECIMAL(8, 2) NOT NULL,
                    tree_density INTEGER DEFAULT 0,
                    soil_type VARCHAR(100),
                    elevation_meters INTEGER,
                    boundary GEOGRAPHY(POLYGON, 4326),
                    centroid GEOGRAPHY(POINT, 4326),
                    planting_date DATE,
                    last_harvest DATE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
            )

            # Create trees table
            cur.execute(
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
                    height_meters DECIMAL(4, 2),
                    trunk_diameter_cm DECIMAL(5, 2),
                    health_status VARCHAR(50) DEFAULT 'healthy',
                    last_inspection DATE,
                    maturity_index DECIMAL(5, 2) DEFAULT 0.0,
                    fungal_threat_level DECIMAL(5, 2) DEFAULT 0.0,
                    security_events_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
            )

            # Create indexes
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIST (location);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_lots_boundary ON lots USING GIST (boundary);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_lots_centroid ON lots USING GIST (centroid);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_trees_location ON trees USING GIST (location);"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_farms_slug ON farms (slug);")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_trees_farm_id ON trees (farm_id);"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_trees_lot_id ON trees (lot_id);"
            )

            print("✅ Tables created successfully")


def populate_sample_data():
    """Populate database with sample data"""
    print("🌱 Populating sample data...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if data already exists
            cur.execute("SELECT COUNT(*) FROM farms")
            farm_count = cur.fetchone()[0]
            if farm_count > 0:
                print(
                    "📊 Database already contains {farm_count} farms, skipping data population"
                )
                return

            # Brazilian cocoa farm locations (Bahia region)
            farms_data = [
                {
                    "name": "Fazenda Cacau Dourado",
                    "slug": "cacau-dourado",
                    "lat": -14.2350,
                    "lng": -39.0648,
                    "area": 450.75,
                    "established": "2010-03-15",
                    "email": "contato@cacaudourado.com.br",
                    "phone": "+55 73 3214-5678",
                },
                {
                    "name": "Sítio Theobroma Bahia",
                    "slug": "theobroma-bahia",
                    "lat": -14.4567,
                    "lng": -39.1234,
                    "area": 287.30,
                    "established": "2008-07-20",
                    "email": "info@theobromabahia.com.br",
                    "phone": "+55 73 3298-7654",
                },
                {
                    "name": "Plantação Serra Verde",
                    "slug": "serra-verde",
                    "lat": -14.3891,
                    "lng": -38.9876,
                    "area": 623.50,
                    "established": "2005-11-08",
                    "email": "admin@serraverde.agro.br",
                    "phone": "+55 73 3187-4321",
                },
            ]

            farm_ids = []
            for farm in farms_data:
                cur.execute(
                    """
                    INSERT INTO farms (name, slug, location, total_area_hectares, established_date, contact_email, contact_phone)
                    VALUES (%s, %s, ST_GeogFromText('POINT(%s %s)'), %s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        farm["name"],
                        farm["slug"],
                        farm["lng"],
                        farm["lat"],
                        farm["area"],
                        farm["established"],
                        farm["email"],
                        farm["phone"],
                    ),
                )
                farm_id = cur.fetchone()[0]
                farm_ids.append(farm_id)
                print("✅ Created farm: {farm['name']} (ID: {farm_id})")

            # Create lots for each farm
            lot_id_counter = 1
            lot_ids = []
            for farm_id in farm_ids:
                # Each farm has 3-5 lots
                num_lots = random.randint(3, 5)
                for lot_num in range(1, num_lots + 1):
                    area = round(random.uniform(25.0, 150.0), 2)
                    tree_density = random.randint(80, 200)
                    elevation = random.randint(150, 800)

                    # Generate random point near farm for lot centroid
                    base_lat = (
                        -14.2350 + (farm_id - 1) * 0.1 + random.uniform(-0.05, 0.05)
                    )
                    base_lng = (
                        -39.0648 + (farm_id - 1) * 0.1 + random.uniform(-0.05, 0.05)
                    )

                    # Create simple polygon boundary around centroid
                    offset = 0.01
                    boundary_wkt = """POLYGON(({base_lng-offset} {base_lat-offset},
                                                {base_lng+offset} {base_lat-offset},
                                                {base_lng+offset} {base_lat+offset},
                                                {base_lng-offset} {base_lat+offset},
                                                {base_lng-offset} {base_lat-offset}))"""

                    cur.execute(
                        """
                        INSERT INTO lots (farm_id, lot_number, area_hectares, tree_density,
                                        soil_type, elevation_meters, boundary, centroid, planting_date)
                        VALUES (%s, %s, %s, %s, %s, %s, ST_GeogFromText(%s), ST_GeogFromText('POINT(%s %s)'), %s)
                        RETURNING id
                    """,
                        (
                            farm_id,
                            lot_num,
                            area,
                            tree_density,
                            random.choice(["Clay", "Sandy", "Loamy", "Silty"]),
                            elevation,
                            boundary_wkt,
                            base_lng,
                            base_lat,
                            "2015-01-01",
                        ),
                    )
                    lot_id = cur.fetchone()[0]
                    lot_ids.append((lot_id, farm_id))
                    lot_id_counter += 1

            print("✅ Created {len(lot_ids)} lots")

            # Create trees for each lot
            tree_counter = 1
            for lot_id, farm_id in lot_ids:
                # Each lot has 50-150 trees
                num_trees = random.randint(50, 150)
                for tree_num in range(num_trees):
                    # Generate random location within lot
                    base_lat = (
                        -14.2350 + (farm_id - 1) * 0.1 + random.uniform(-0.08, 0.08)
                    )
                    base_lng = (
                        -39.0648 + (farm_id - 1) * 0.1 + random.uniform(-0.08, 0.08)
                    )

                    tree_code = "T{farm_id:02d}{lot_id:03d}{tree_num:03d}"
                    age = random.randint(5, 15)
                    height = round(random.uniform(2.5, 8.0), 2)
                    diameter = round(random.uniform(15.0, 45.0), 2)
                    health = random.choice(["healthy", "good", "fair", "poor"])
                    maturity = round(random.uniform(30.0, 95.0), 2)
                    fungal_threat = round(random.uniform(0.0, 40.0), 2)
                    security_events = random.randint(0, 5)

                    cur.execute(
                        """
                        INSERT INTO trees (farm_id, lot_id, tree_code, location, variety,
                                         planting_date, age_years, height_meters, trunk_diameter_cm,
                                         health_status, last_inspection, maturity_index,
                                         fungal_threat_level, security_events_count)
                        VALUES (%s, %s, %s, ST_GeogFromText('POINT(%s %s)'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            farm_id,
                            lot_id,
                            tree_code,
                            base_lng,
                            base_lat,
                            random.choice(["Trinitario", "Forastero", "Criollo"]),
                            date(
                                2024 - age, random.randint(1, 12), random.randint(1, 28)
                            ),
                            age,
                            height,
                            diameter,
                            health,
                            date.today(),
                            maturity,
                            fungal_threat,
                            security_events,
                        ),
                    )

                    tree_counter += 1

                    if tree_counter % 100 == 0:
                        print("🌳 Created {tree_counter} trees...")

            print("✅ Created {tree_counter - 1} trees")


def create_views():
    """Create useful database views"""
    print("📊 Creating database views...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Farm summary view
            cur.execute(
                """
                CREATE OR REPLACE VIEW farm_summary AS
                SELECT
                    f.id,
                    f.name,
                    f.slug,
                    f.total_area_hectares,
                    COUNT(DISTINCT l.id) as total_lots,
                    COUNT(t.id) as total_trees,
                    ROUND(AVG(t.maturity_index), 2) as avg_maturity,
                    ROUND(AVG(t.fungal_threat_level), 2) as avg_fungal_threat,
                    SUM(t.security_events_count) as total_security_events
                FROM farms f
                LEFT JOIN lots l ON f.id = l.farm_id
                LEFT JOIN trees t ON f.id = t.farm_id
                GROUP BY f.id, f.name, f.slug, f.total_area_hectares;
            """
            )

            # Lot summary view
            cur.execute(
                """
                CREATE OR REPLACE VIEW lot_summary AS
                SELECT
                    l.id,
                    l.farm_id,
                    l.lot_number,
                    l.area_hectares,
                    COUNT(t.id) as tree_count,
                    ROUND(AVG(t.maturity_index), 2) as avg_maturity,
                    ROUND(AVG(t.fungal_threat_level), 2) as avg_fungal_threat,
                    SUM(t.security_events_count) as security_events
                FROM lots l
                LEFT JOIN trees t ON l.id = t.lot_id
                GROUP BY l.id, l.farm_id, l.lot_number, l.area_hectares;
            """
            )

            print("✅ Views created successfully")


def test_connection():
    """Test database connection and data"""
    print("🧪 Testing database connection and data...")

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Test basic queries
            cur.execute("SELECT COUNT(*) as count FROM farms")
            farms_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM lots")
            lots_count = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM trees")
            trees_count = cur.fetchone()["count"]

            print("📊 Database statistics:")
            print("   Farms: {farms_count}")
            print("   Lots: {lots_count}")
            print("   Trees: {trees_count}")

            # Test PostGIS functionality
            cur.execute(
                """
                SELECT f.name, ST_AsText(f.location::geometry) as location
                FROM farms f
                LIMIT 1
            """
            )
            farm = cur.fetchone()
            if farm:
                print("📍 Sample farm location: {farm['name']} at {farm['location']}")

            print("✅ Database test completed successfully")


def main():
    """Main setup function"""
    try:
        setup_postgis()
        create_tables()
        populate_sample_data()
        create_views()
        test_connection()
        print("🎉 Database setup completed successfully!")

    except Exception as e:
        print("❌ Database setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
