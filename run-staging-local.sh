#!/bin/bash

# Theobroma Geo API - Local Staging Deployment Script
# This script runs the staging deployment locally using Docker

set -e

# Configuration
POSTGRES_PASSWORD="staging_password"
POSTGRES_USER="staging_user"  
POSTGRES_DB="theobroma_staging"
API_PORT="8000"
DB_PORT="5433"  # Different port to avoid conflicts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Theobroma Geo API - Local Staging Deployment${NC}"
echo "=================================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up containers...${NC}"
    docker stop theobroma-staging-api theobroma-staging-postgres 2>/dev/null || true
    docker rm theobroma-staging-api theobroma-staging-postgres 2>/dev/null || true
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Stop any existing containers
cleanup

echo -e "${BLUE}📦 Starting PostgreSQL database...${NC}"
docker run -d \
    --name theobroma-staging-postgres \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -p $DB_PORT:5432 \
    postgis/postgis:13-3.1

echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 10

# Check if PostgreSQL is ready
for i in {1..30}; do
    if docker exec theobroma-staging-postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        break
    else
        echo -n "."
        sleep 1
    fi
done

echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker build -t theobroma-geo-api:staging .

echo -e "${BLUE}🚀 Starting API server...${NC}"
docker run -d \
    --name theobroma-staging-api \
    --link theobroma-staging-postgres:postgres \
    -e DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB" \
    -e ENVIRONMENT="staging" \
    -e LOG_LEVEL="DEBUG" \
    -p $API_PORT:8000 \
    theobroma-geo-api:staging

echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
sleep 15

# Test the API health endpoint
echo -e "${BLUE}🔍 Testing API endpoints...${NC}"
for i in {1..30}; do
    if curl -f -s http://localhost:$API_PORT/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API is ready and healthy${NC}"
        break
    else
        echo -n "."
        sleep 2
    fi
done

echo ""
echo -e "${GREEN}🎉 Staging deployment is ready!${NC}"
echo ""
echo -e "${BLUE}📋 Available endpoints:${NC}"
echo "  🔍 Health Check:     http://localhost:$API_PORT/health"
echo "  📚 API Docs:         http://localhost:$API_PORT/docs"  
echo "  📖 ReDoc:            http://localhost:$API_PORT/redoc"
echo "  🏡 Farms:            http://localhost:$API_PORT/farms"
echo "  🌳 Trees:            http://localhost:$API_PORT/trees"
echo "  📦 Lots:             http://localhost:$API_PORT/lots"
echo "  🚨 Security Events:  http://localhost:$API_PORT/security-events"
echo "  📊 Metrics:          http://localhost:$API_PORT/metrics"
echo ""
echo -e "${BLUE}💾 Database connection:${NC}"
echo "  Host: localhost:$DB_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo "  Password: $POSTGRES_PASSWORD"
echo ""

# Test some endpoints
echo -e "${BLUE}🧪 Running basic endpoint tests...${NC}"

echo -n "  Health check: "
if curl -f -s http://localhost:$API_PORT/health | jq -r '.status' | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "  Farms endpoint: "
if curl -f -s http://localhost:$API_PORT/farms >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "  API documentation: "  
if curl -f -s http://localhost:$API_PORT/docs >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo ""
echo -e "${YELLOW}📝 To view container logs:${NC}"
echo "  docker logs theobroma-staging-api"
echo "  docker logs theobroma-staging-postgres"
echo ""
echo -e "${YELLOW}⏹️  Press Ctrl+C to stop the staging environment${NC}"

# Keep the script running and show logs
echo -e "${BLUE}📋 API Server Logs (real-time):${NC}"
echo "=================================="
docker logs -f theobroma-staging-api
