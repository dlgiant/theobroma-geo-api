-- Theobroma Geo API - Sample Data Setup for Staging Database
-- This script sets up PostGIS extension and creates sample data for farms and lots

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create farms table with geographic data
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

-- Create lots table with geographic polygons
CREATE TABLE IF NOT EXISTS lots (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
    lot_number INTEGER NOT NULL,
    area_hectares DECIMAL(8,2) NOT NULL,
    tree_density INTEGER DEFAULT 0, -- trees per hectare
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

-- Create trees table for individual tree tracking
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
    maturity_index DECIMAL(5,2) DEFAULT 0.0, -- 0-100
    fungal_threat_level DECIMAL(5,2) DEFAULT 0.0, -- 0-100
    security_events_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_farms_location ON farms USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_lots_boundary ON lots USING GIST(boundary);
CREATE INDEX IF NOT EXISTS idx_lots_centroid ON lots USING GIST(centroid);
CREATE INDEX IF NOT EXISTS idx_trees_location ON trees USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_trees_farm_lot ON trees(farm_id, lot_id);

-- Insert sample farms data (Brazilian cocoa farms)
INSERT INTO farms (name, slug, location, total_area_hectares, established_date, contact_email, contact_phone) VALUES
(
    'Fazenda Bahia', 
    'fazenda-bahia',
    ST_GeogFromText('SRID=4326;POINT(-39.0639 -14.2350)'), -- Bahia, Brazil
    150.5,
    '2010-03-15',
    'contato@fazendabahia.com.br',
    '+55 73 3234-5678'
),
(
    'Fazenda Espírito Santo', 
    'fazenda-espirito-santo',
    ST_GeogFromText('SRID=4326;POINT(-40.3372 -19.1834)'), -- Espírito Santo, Brazil
    87.3,
    '2008-06-20',
    'gestao@fazendaes.com.br',
    '+55 27 3345-6789'
),
(
    'Fazenda Pará',
    'fazenda-para',
    ST_GeogFromText('SRID=4326;POINT(-49.2044 -2.5297)'), -- Pará, Brazil
    203.8,
    '2012-09-10',
    'admin@fazendapara.com.br',
    '+55 91 3456-7890'
);

-- Insert sample lots data with realistic geographic boundaries
-- Fazenda Bahia lots
INSERT INTO lots (farm_id, lot_number, area_hectares, tree_density, soil_type, elevation_meters, boundary, centroid, planting_date) VALUES
(
    1, 1, 12.5, 180, 'Clay loam', 85,
    ST_GeogFromText('SRID=4326;POLYGON((-39.0650 -14.2340, -39.0640 -14.2340, -39.0640 -14.2360, -39.0650 -14.2360, -39.0650 -14.2340))'),
    ST_GeogFromText('SRID=4326;POINT(-39.0645 -14.2350)'),
    '2010-04-01'
),
(
    1, 2, 15.8, 165, 'Sandy loam', 92,
    ST_GeogFromText('SRID=4326;POLYGON((-39.0640 -14.2340, -39.0620 -14.2340, -39.0620 -14.2365, -39.0640 -14.2365, -39.0640 -14.2340))'),
    ST_GeogFromText('SRID=4326;POINT(-39.0630 -14.2352)'),
    '2010-05-15'
),
(
    1, 3, 18.2, 195, 'Loam', 78,
    ST_GeogFromText('SRID=4326;POLYGON((-39.0620 -14.2340, -39.0595 -14.2340, -39.0595 -14.2370, -39.0620 -14.2370, -39.0620 -14.2340))'),
    ST_GeogFromText('SRID=4326;POINT(-39.0607 -14.2355)'),
    '2010-06-10'
);

-- Fazenda Espírito Santo lots
INSERT INTO lots (farm_id, lot_number, area_hectares, tree_density, soil_type, elevation_meters, boundary, centroid, planting_date) VALUES
(
    2, 1, 10.3, 200, 'Red clay', 120,
    ST_GeogFromText('SRID=4326;POLYGON((-40.3380 -19.1825, -40.3365 -19.1825, -40.3365 -19.1840, -40.3380 -19.1840, -40.3380 -19.1825))'),
    ST_GeogFromText('SRID=4326;POINT(-40.3372 -19.1832)'),
    '2008-07-01'
),
(
    2, 2, 14.7, 175, 'Sandy clay', 145,
    ST_GeogFromText('SRID=4326;POLYGON((-40.3365 -19.1825, -40.3345 -19.1825, -40.3345 -19.1845, -40.3365 -19.1845, -40.3365 -19.1825))'),
    ST_GeogFromText('SRID=4326;POINT(-40.3355 -19.1835)'),
    '2008-08-15'
);

-- Fazenda Pará lots
INSERT INTO lots (farm_id, lot_number, area_hectares, tree_density, soil_type, elevation_meters, boundary, centroid, planting_date) VALUES
(
    3, 1, 25.6, 160, 'Alluvial soil', 45,
    ST_GeogFromText('SRID=4326;POLYGON((-49.2055 -2.5285, -49.2025 -2.5285, -49.2025 -2.5315, -49.2055 -2.5315, -49.2055 -2.5285))'),
    ST_GeogFromText('SRID=4326;POINT(-49.2040 -2.5300)'),
    '2012-10-01'
),
(
    3, 2, 32.1, 140, 'Clay', 52,
    ST_GeogFromText('SRID=4326;POLYGON((-49.2025 -2.5285, -49.1990 -2.5285, -49.1990 -2.5320, -49.2025 -2.5320, -49.2025 -2.5285))'),
    ST_GeogFromText('SRID=4326;POINT(-49.2007 -2.5302)'),
    '2012-11-15'
),
(
    3, 3, 28.9, 155, 'Sandy loam', 48,
    ST_GeogFromText('SRID=4326;POLYGON((-49.1990 -2.5285, -49.1955 -2.5285, -49.1955 -2.5318, -49.1990 -2.5318, -49.1990 -2.5285))'),
    ST_GeogFromText('SRID=4326;POINT(-49.1972 -2.5301)'),
    '2013-01-10'
);

-- Insert sample trees data (sample of trees in each lot)
-- Generate trees for Fazenda Bahia, Lot 1
INSERT INTO trees (farm_id, lot_id, tree_code, location, variety, planting_date, age_years, height_meters, trunk_diameter_cm, health_status, maturity_index, fungal_threat_level)
SELECT 
    1 as farm_id,
    1 as lot_id,
    'FB-L1-' || LPAD(generate_series::text, 4, '0') as tree_code,
    ST_GeogFromText('SRID=4326;POINT(' || 
        (-39.0650 + (random() * 0.001)) || ' ' || 
        (-14.2360 + (random() * 0.002)) || ')') as location,
    CASE (random() * 3)::int 
        WHEN 0 THEN 'Trinitario'
        WHEN 1 THEN 'Forastero'
        ELSE 'Criollo'
    END as variety,
    '2010-04-01'::date + (random() * 30)::int as planting_date,
    EXTRACT(YEAR FROM age(CURRENT_DATE, '2010-04-01'::date + (random() * 30)::int))::int as age_years,
    (3.5 + random() * 2.5)::numeric(4,2) as height_meters,
    (15 + random() * 20)::numeric(5,2) as trunk_diameter_cm,
    CASE (random() * 4)::int
        WHEN 0 THEN 'excellent'
        WHEN 1 THEN 'good'
        WHEN 2 THEN 'fair'
        ELSE 'healthy'
    END as health_status,
    (60 + random() * 40)::numeric(5,2) as maturity_index,
    (random() * 25)::numeric(5,2) as fungal_threat_level
FROM generate_series(1, 50);

-- Generate trees for Fazenda Espírito Santo, Lot 1
INSERT INTO trees (farm_id, lot_id, tree_code, location, variety, planting_date, age_years, height_meters, trunk_diameter_cm, health_status, maturity_index, fungal_threat_level)
SELECT 
    2 as farm_id,
    4 as lot_id, -- lot_id 4 corresponds to Fazenda ES, Lot 1
    'FES-L1-' || LPAD(generate_series::text, 4, '0') as tree_code,
    ST_GeogFromText('SRID=4326;POINT(' || 
        (-40.3380 + (random() * 0.0015)) || ' ' || 
        (-19.1840 + (random() * 0.0015)) || ')') as location,
    CASE (random() * 2)::int 
        WHEN 0 THEN 'Trinitario'
        ELSE 'Forastero'
    END as variety,
    '2008-07-01'::date + (random() * 45)::int as planting_date,
    EXTRACT(YEAR FROM age(CURRENT_DATE, '2008-07-01'::date + (random() * 45)::int))::int as age_years,
    (4.0 + random() * 2.0)::numeric(4,2) as height_meters,
    (18 + random() * 25)::numeric(5,2) as trunk_diameter_cm,
    CASE (random() * 3)::int
        WHEN 0 THEN 'excellent'
        WHEN 1 THEN 'good'
        ELSE 'healthy'
    END as health_status,
    (70 + random() * 30)::numeric(5,2) as maturity_index,
    (random() * 20)::numeric(5,2) as fungal_threat_level
FROM generate_series(1, 40);

-- Generate trees for Fazenda Pará, Lot 1
INSERT INTO trees (farm_id, lot_id, tree_code, location, variety, planting_date, age_years, height_meters, trunk_diameter_cm, health_status, maturity_index, fungal_threat_level)
SELECT 
    3 as farm_id,
    6 as lot_id, -- lot_id 6 corresponds to Fazenda Pará, Lot 1
    'FP-L1-' || LPAD(generate_series::text, 4, '0') as tree_code,
    ST_GeogFromText('SRID=4326;POINT(' || 
        (-49.2055 + (random() * 0.003)) || ' ' || 
        (-2.5315 + (random() * 0.003)) || ')') as location,
    CASE (random() * 3)::int 
        WHEN 0 THEN 'Trinitario'
        WHEN 1 THEN 'Nacional'
        ELSE 'Forastero'
    END as variety,
    '2012-10-01'::date + (random() * 60)::int as planting_date,
    EXTRACT(YEAR FROM age(CURRENT_DATE, '2012-10-01'::date + (random() * 60)::int))::int as age_years,
    (2.8 + random() * 3.2)::numeric(4,2) as height_meters,
    (12 + random() * 18)::numeric(5,2) as trunk_diameter_cm,
    CASE (random() * 4)::int
        WHEN 0 THEN 'excellent'
        WHEN 1 THEN 'good'
        WHEN 2 THEN 'fair'
        ELSE 'healthy'
    END as health_status,
    (45 + random() * 55)::numeric(5,2) as maturity_index,
    (random() * 30)::numeric(5,2) as fungal_threat_level
FROM generate_series(1, 60);

-- Create some useful views for the API
CREATE OR REPLACE VIEW farm_summary AS
SELECT 
    f.id,
    f.name,
    f.slug,
    f.total_area_hectares,
    COUNT(DISTINCT l.id) as total_lots,
    COUNT(t.id) as total_trees,
    AVG(t.maturity_index) as avg_maturity,
    AVG(t.fungal_threat_level) as avg_fungal_threat,
    SUM(t.security_events_count) as total_security_events,
    ST_AsText(f.location) as location_wkt
FROM farms f
LEFT JOIN lots l ON f.id = l.farm_id
LEFT JOIN trees t ON f.id = t.farm_id
GROUP BY f.id, f.name, f.slug, f.total_area_hectares, f.location;

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
    AVG(t.maturity_index) as avg_maturity,
    AVG(t.fungal_threat_level) as avg_fungal_threat,
    AVG(t.height_meters) as avg_height,
    SUM(t.security_events_count) as security_events,
    ST_AsText(l.centroid) as centroid_wkt,
    ST_Area(l.boundary) as boundary_area_sq_meters
FROM lots l
JOIN farms f ON l.farm_id = f.id
LEFT JOIN trees t ON l.id = t.lot_id
GROUP BY l.id, l.farm_id, f.name, l.lot_number, l.area_hectares, l.tree_density, l.soil_type, l.elevation_meters, l.centroid, l.boundary;

-- Sample queries to test the setup
-- Query 1: Get all farms with their basic info
-- SELECT * FROM farm_summary;

-- Query 2: Get lots within 50km of a specific point
-- SELECT l.*, ST_Distance(l.centroid, ST_GeogFromText('SRID=4326;POINT(-39.0639 -14.2350)')) / 1000 as distance_km
-- FROM lots l
-- WHERE ST_DWithin(l.centroid, ST_GeogFromText('SRID=4326;POINT(-39.0639 -14.2350)'), 50000);

-- Query 3: Get trees in a specific area (bounding box)
-- SELECT tree_code, variety, health_status, maturity_index, ST_AsText(location)
-- FROM trees 
-- WHERE ST_Within(location, ST_GeogFromText('SRID=4326;POLYGON((-39.0650 -14.2340, -39.0640 -14.2340, -39.0640 -14.2360, -39.0650 -14.2360, -39.0650 -14.2340))'));

COMMIT;

-- Display setup completion message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🌱 Theobroma Geo API Database Setup Complete!';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Sample data created:';
    RAISE NOTICE '   - % farms', (SELECT COUNT(*) FROM farms);
    RAISE NOTICE '   - % lots', (SELECT COUNT(*) FROM lots);
    RAISE NOTICE '   - % trees', (SELECT COUNT(*) FROM trees);
    RAISE NOTICE '';
    RAISE NOTICE '🗺️  PostGIS extensions enabled:';
    RAISE NOTICE '   - postgis';
    RAISE NOTICE '   - postgis_topology';
    RAISE NOTICE '';
    RAISE NOTICE '📈 Views created:';
    RAISE NOTICE '   - farm_summary';
    RAISE NOTICE '   - lot_summary';
    RAISE NOTICE '';
    RAISE NOTICE '✅ Database is ready for use!';
END $$;
