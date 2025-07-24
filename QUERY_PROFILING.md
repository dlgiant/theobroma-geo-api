# Query Profiling and Performance Monitoring

This document explains how to use the integrated query profiling system in the Theobroma Geo API to identify and resolve database performance bottlenecks.

## Overview

The query profiling system includes:
- **Automatic query timing**: All database queries are automatically timed
- **Slow query detection**: Queries taking longer than 500ms are flagged
- **Performance statistics**: Aggregated metrics on query performance
- **Debug endpoints**: API endpoints for monitoring and debugging
- **Performance analyzer tool**: Automated load testing and analysis

## Debug Endpoints

### GET /debug/query-stats
Returns current query performance statistics:
```json
{
  "query_performance": {
    "total_queries": 330,
    "avg_query_time": 0.1949,
    "max_query_time": 0.3331,
    "min_query_time": 0.1504,
    "slow_queries_count": 0,
    "recent_slow_queries": []
  },
  "timestamp": "2025-07-24T15:40:01.031224"
}
```

### POST /debug/reset-query-stats
Resets all query performance statistics to start fresh monitoring.

### POST /debug/enable-detailed-logging
Enables verbose logging of all database queries with execution times.
⚠️ **Warning**: This generates a lot of log output and should only be used for debugging.

### POST /debug/disable-detailed-logging
Returns to normal logging mode where only slow queries (>500ms) are logged.

## Query Performance Analyzer Tool

The `query_analyzer.py` tool provides automated load testing and performance analysis.

### Basic Usage
```bash
python3 query_analyzer.py
```

### Advanced Usage
```bash
python3 query_analyzer.py \
  --url http://localhost:8000 \
  --concurrent 5 \
  --iterations 10 \
  --detailed-logging
```

### Parameters
- `--url`: API base URL (default: http://localhost:8000)
- `--concurrent`: Number of concurrent requests per iteration (default: 5)
- `--iterations`: Number of test iterations (default: 10)
- `--detailed-logging`: Enable detailed query logging during testing

### Output
The analyzer provides:
- **Load test results**: Response times, success rates, per-endpoint analysis
- **Database query statistics**: Query counts, execution times, slow queries
- **Performance recommendations**: Actionable advice for optimization

## Interpreting Results

### Response Time Guidelines
- **Good**: < 500ms average response time
- **Acceptable**: 500ms - 1s average response time
- **Slow**: > 1s average response time (needs optimization)

### Database Query Guidelines
- **Good**: < 100ms average query time
- **Acceptable**: 100ms - 500ms average query time
- **Slow**: > 500ms query time (flagged as slow query)

### Key Metrics to Monitor
1. **Average query time**: Should be under 100ms for optimal performance
2. **Slow query count**: Should be zero or minimal
3. **P95 response time**: 95% of requests should complete quickly
4. **Success rate**: Should be above 95%

## Common Performance Issues and Solutions

### 1. High Average Query Time
**Symptoms**: Average query time > 100ms
**Solutions**:
- Add database indexes on frequently queried columns
- Optimize complex queries with EXPLAIN ANALYZE
- Consider query result caching
- Review database connection pooling settings

### 2. Slow Individual Queries
**Symptoms**: Queries flagged as slow (>500ms)
**Solutions**:
- Examine slow query logs for patterns
- Add missing indexes
- Rewrite complex queries for better performance
- Consider data partitioning for large tables

### 3. N+1 Query Problems
**Symptoms**: Many small, similar queries
**Solutions**:
- Use JOIN queries to fetch related data in bulk
- Implement eager loading for related objects
- Batch database operations where possible

### 4. High Response Times
**Symptoms**: API endpoints responding slowly
**Solutions**:
- Profile database queries within slow endpoints
- Add response caching for frequently requested data
- Optimize business logic
- Consider database read replicas for read-heavy workloads

## Best Practices

### Development
1. **Run profiling during development**: Use the analyzer tool regularly
2. **Monitor slow queries**: Keep slow query count at zero
3. **Profile before deploying**: Ensure performance doesn't regress
4. **Use realistic test data**: Profile with production-like data volumes

### Production
1. **Monitor query statistics**: Check `/debug/query-stats` regularly
2. **Set up alerting**: Alert when slow query count increases
3. **Regular performance reviews**: Schedule periodic performance analysis
4. **Capacity planning**: Monitor trends in query performance over time

### Database Optimization
1. **Index frequently queried columns**: Especially foreign keys and WHERE clauses
2. **Use EXPLAIN ANALYZE**: Understand query execution plans
3. **Optimize JOINs**: Ensure efficient join conditions
4. **Monitor connection pools**: Avoid connection exhaustion
5. **Regular VACUUM/ANALYZE**: Keep PostgreSQL statistics current

## Example Workflow

1. **Reset statistics**:
   ```bash
   curl -X POST http://localhost:8000/debug/reset-query-stats
   ```

2. **Run load test**:
   ```bash
   python3 query_analyzer.py --concurrent 10 --iterations 5
   ```

3. **Check for slow queries**:
   ```bash
   curl http://localhost:8000/debug/query-stats
   ```

4. **If slow queries detected**:
   - Enable detailed logging
   - Reproduce the slow operations
   - Examine logs for query patterns
   - Optimize identified queries
   - Re-test to verify improvements

5. **Monitor in production**:
   - Set up automated monitoring of query stats
   - Alert on performance regressions
   - Regular performance reviews

## Dependencies

The query analyzer requires:
```bash
pip install aiohttp
```

## Configuration

### Slow Query Threshold
The slow query threshold is set to 500ms by default. This can be adjusted in `database.py`:

```python
slow_query_threshold = 0.5  # 500ms - adjust as needed
```

### Query Statistics Retention
- **Query times**: All query times are kept in memory (cleared on reset)
- **Slow queries**: Last 50 slow queries are retained to prevent memory issues
- **Recent slow queries**: Last 10 slow queries shown in API responses

## Security Considerations

- **Debug endpoints**: Should be disabled or secured in production
- **Detailed logging**: Contains query parameters - ensure logs are secure
- **Performance data**: May reveal information about database structure

Consider implementing authentication for debug endpoints in production environments.
