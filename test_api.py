#!/usr/bin/env python3
"""
Basic API tests for CI pipeline validation
"""

import os

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Check if we have a test database connection
TEST_DATABASE_URL = os.getenv("DATABASE_URL")
has_database = TEST_DATABASE_URL is not None


def check_database_available():
    """Check if database is available for testing"""
    if not has_database:
        return False
    try:
        from database import test_connection

        return test_connection()
    except Exception:
        return False


def test_health_endpoint():
    """Test the health endpoint returns 200 and expected structure"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "version" in data
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_root_endpoint():
    """Test the root endpoint returns API information"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "description" in data
    assert "endpoints" in data
    assert data["version"] == "1.0.0"


@pytest.mark.skipif(not has_database, reason="Database not available")
def test_farms_endpoint():
    """Test the farms endpoint returns proper structure"""
    if not check_database_available():
        pytest.skip("Database connection not available")

    response = client.get("/farms")
    assert response.status_code == 200

    data = response.json()
    assert "farms" in data
    assert "total_farms" in data
    assert isinstance(data["farms"], list)
    assert isinstance(data["total_farms"], int)


def test_docs_endpoint():
    """Test the API documentation endpoint is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200
    # OpenAPI docs should return HTML
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_spec():
    """Test the OpenAPI specification endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert data["info"]["title"] == "Theobroma Digital API"
    assert data["info"]["version"] == "1.0.0"
