# Theobroma Geo API 🌱

A high-performance FastAPI microservice for cocoa plantation monitoring and management, featuring advanced batch fetching optimizations and real-time query profiling.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://postgresql.org)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.0+-orange.svg)](https://postgis.net)

## 🚀 Features

### Core Functionality
- **Plantation Management**: Comprehensive farm, lot, and tree data management
- **Security Monitoring**: Real-time security event tracking and alerting
- **Weather Integration**: Weather data collection and analysis for plantation lots
- **Production Analytics**: Harvest predictions, yield estimates, and quality scoring
- **Geographic Data**: Full PostGIS integration for spatial queries and mapping

### Performance Optimizations
- **Batch Fetching**: Eliminated N+1 query problems with 90%+ query reduction
- **Query Profiling**: Real-time database performance monitoring and analysis
- **Optimized Joins**: Efficient SQL queries with database-level aggregations
- **Connection Pooling**: Optimized database connection management

### Developer Experience
- **Comprehensive API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Performance Testing**: Automated tools for query optimization validation
- **Docker Support**: Containerized deployment with health checks
- **Code Quality**: Fully linted with Black, isort, and flake8

## 📊 Performance Achievements

| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| Farm Locations | ~10 queries | 1 query | **90% reduction** |
| Lot Summary | ~20 queries | 2 queries | **90% reduction** |
| Analytics | ~16 queries | 2 queries | **87.5% reduction** |
| Tree Locations | ~100 queries | 3 queries | **97% reduction** |

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 13+ with PostGIS 3.0+
- **ORM**: SQLAlchemy 2.0+
- **Geographic**: PostGIS for spatial data processing
- **Validation**: Pydantic models with type safety
- **Testing**: Performance testing with aiohttp
- **Containerization**: Docker with multi-stage builds

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL with PostGIS (for local development)

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 2. Docker Deployment (Recommended)
```bash
# Build and run the API
docker build -t theobroma-geo-api .
docker run -d -p 8000:8000 --name theobroma-api theobroma-geo-api
```

### 3. Verify Installation
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "uptime_seconds": X}
```

## 📚 API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Key Endpoints

### Core Endpoints
- `GET /farms` - List all farms with location data
- `GET /farms/{farm_id}/lots` - Get lot summaries with tree metrics
- `GET /farms/{farm_id}/security/events` - Security event monitoring
- `GET /farms/{farm_id}/weather` - Weather data for plantation lots
- `GET /farms/{farm_id}/analytics/production` - Production analytics and predictions

### Performance Monitoring
- `GET /debug/query-stats` - Real-time database query performance
- `POST /debug/reset-query-stats` - Reset performance statistics
- `POST /debug/enable-detailed-logging` - Enable verbose query logging
- `POST /debug/disable-detailed-logging` - Disable verbose logging

### Example Usage
```bash
# Get farms list
curl http://localhost:8000/farms

# Get lot summary for a farm
curl http://localhost:8000/farms/valley-verde/lots?limit=10

# Get security events
curl http://localhost:8000/farms/valley-verde/security/events?severity=HIGH

# Check query performance
curl http://localhost:8000/debug/query-stats
```

## 🧪 Performance Testing

The project includes comprehensive performance testing tools:

### Run Performance Analysis
```bash
# Basic performance test
python3 batch_performance_test.py

# Load testing with custom parameters
python3 query_analyzer.py --concurrent 10 --iterations 5
```

### Performance Metrics
- **Query Efficiency**: Tracks queries per request ratio
- **Response Times**: Monitors API endpoint performance
- **Database Performance**: Real-time query execution monitoring
- **Batch Optimization**: Validates N+1 query elimination

## 🏗️ Architecture

### Database Schema
```
farms (geographic farms)
├── lots (plantation sections)
│   └── trees (individual cocoa trees)
├── location (PostGIS POINT)
└── metadata (area, dates, etc.)
```

### Service Layer Architecture
- **FarmService**: Farm management and validation
- **LotService**: Lot operations with batch tree metrics
- **SecurityService**: Event monitoring and alerting
- **WeatherService**: Weather data integration
- **AnalyticsService**: Production analytics and forecasting

## 📈 Performance Optimizations

### Batch Fetching Implementation
The API eliminates N+1 query problems through:

- **Farm locations**: Single query with PostGIS coordinate extraction
- **Lot metrics**: Aggregated tree data with GROUP BY operations
- **Analytics**: Comprehensive lot analysis in single query
- **Tree locations**: Batch coordinate fetching with spatial functions

### Query Profiling System
- **Automatic timing**: All queries automatically profiled
- **Slow query detection**: Queries >500ms flagged and logged
- **Performance statistics**: Real-time metrics via API endpoints
- **Memory management**: Circular buffer for performance data

## 🔧 Development

### Code Quality
```bash
# Format code
python3 -m black *.py
python3 -m isort *.py

# Lint code
python3 -m flake8 *.py
```

### Testing
```bash
# Run performance tests
python3 batch_performance_test.py

# Run query analysis
python3 query_analyzer.py --detailed-logging
```

### Database Setup
```bash
# Initialize database with sample data
python3 setup_database.py

# Test database connection
python3 test-db-connection.py
```

## 📊 Monitoring

### Query Performance Dashboard
Access real-time performance metrics:
```bash
curl http://localhost:8000/debug/query-stats | python3 -m json.tool
```

### Health Checks
```bash
# API health status
curl http://localhost:8000/health

# Database connectivity
python3 test-db-connection.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Use Black for code formatting
- Add type hints for all functions
- Include docstrings for public methods
- Write performance tests for new features

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- PostGIS for advanced geographic capabilities
- SQLAlchemy for robust ORM functionality
- The Python community for excellent tooling

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review performance guides in documentation

---

**Built with ❤️ for sustainable cocoa farming** 🍫
