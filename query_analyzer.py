#!/usr/bin/env python3
"""
Query Performance Analyzer for Theobroma Geo API

This script helps identify and analyze database query performance issues.
It can simulate load, analyze query patterns, and suggest optimizations.
"""

import argparse
import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp


class QueryAnalyzer:
    """Analyze database query performance and identify bottlenecks"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def reset_query_stats(self):
        """Reset query statistics before testing"""
        try:
            async with self.session.post(
                "{self.base_url}/debug/reset-query-stats"
            ) as response:
                result = await response.json()
                print("✅ Query stats reset: {result['message']}")
        except Exception as e:
            print("❌ Failed to reset query stats: {e}")

    async def get_query_stats(self) -> Dict[str, Any]:
        """Get current query performance statistics"""
        try:
            async with self.session.get(
                "{self.base_url}/debug/query-stats"
            ) as response:
                result = await response.json()
                return result["query_performance"]
        except Exception as e:
            print("❌ Failed to get query stats: {e}")
            return {}

    async def enable_detailed_logging(self):
        """Enable detailed query logging"""
        try:
            async with self.session.post(
                "{self.base_url}/debug/enable-detailed-logging"
            ) as response:
                result = await response.json()
                print("✅ Detailed logging enabled: {result['message']}")
        except Exception as e:
            print("❌ Failed to enable detailed logging: {e}")

    async def disable_detailed_logging(self):
        """Disable detailed query logging"""
        try:
            async with self.session.post(
                "{self.base_url}/debug/disable-detailed-logging"
            ) as response:
                result = await response.json()
                print("✅ Detailed logging disabled: {result['message']}")
        except Exception as e:
            print("❌ Failed to disable detailed logging: {e}")

    async def test_endpoint(
        self, endpoint: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Test a single endpoint and measure response time"""
        start_time = time.time()
        try:
            async with self.session.get(
                "{self.base_url}{endpoint}", params=params
            ) as response:
                data = await response.json()
                end_time = time.time()

                return {
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time": round(end_time - start_time, 4),
                    "success": response.status == 200,
                    "data_size": len(json.dumps(data)) if data else 0,
                }
        except Exception as e:
            end_time = time.time()
            return {
                "endpoint": endpoint,
                "status_code": 500,
                "response_time": round(end_time - start_time, 4),
                "success": False,
                "error": str(e),
                "data_size": 0,
            }

    async def run_load_test(
        self,
        endpoints: List[Dict[str, Any]],
        concurrent_requests: int = 5,
        iterations: int = 10,
    ):
        """Run load test on multiple endpoints"""
        print(
            "🚀 Starting load test with {concurrent_requests} concurrent requests, {iterations} iterations"
        )

        # Reset stats before testing
        await self.reset_query_stats()

        all_results = []

        for i in range(iterations):
            print("  Running iteration {i+1}/{iterations}")

            # Create tasks for concurrent requests
            tasks = []
            for endpoint_config in endpoints:
                for _ in range(concurrent_requests):
                    task = self.test_endpoint(
                        endpoint_config["endpoint"], endpoint_config.get("params", {})
                    )
                    tasks.append(task)

            # Execute all requests concurrently
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

            # Small delay between iterations
            await asyncio.sleep(0.1)

        return all_results

    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze load test results"""
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]

        if not successful_requests:
            return {
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_requests),
                "success_rate": 0,
                "error": "All requests failed",
            }

        response_times = [r["response_time"] for r in successful_requests]

        # Group by endpoint
        endpoint_stats = {}
        for result in successful_requests:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(result["response_time"])

        # Calculate per-endpoint statistics
        endpoint_analysis = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_analysis[endpoint] = {
                "requests": len(times),
                "avg_response_time": round(statistics.mean(times), 4),
                "min_response_time": round(min(times), 4),
                "max_response_time": round(max(times), 4),
                "median_response_time": round(statistics.median(times), 4),
                "p95_response_time": (
                    round(statistics.quantiles(times, n=20)[18], 4)
                    if len(times) > 1
                    else round(times[0], 4)
                ),
            }

        return {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": round(len(successful_requests) / len(results) * 100, 2),
            "overall_avg_response_time": round(statistics.mean(response_times), 4),
            "overall_max_response_time": round(max(response_times), 4),
            "overall_min_response_time": round(min(response_times), 4),
            "endpoint_analysis": endpoint_analysis,
            "errors": [r.get("error", "Unknown error") for r in failed_requests],
        }

    async def get_farms_list(self) -> List[str]:
        """Get list of available farms for testing"""
        try:
            async with self.session.get("{self.base_url}/farms") as response:
                data = await response.json()
                return data["farms"]
        except Exception as e:
            print("❌ Failed to get farms list: {e}")
            return ["valley-verde"]  # Fallback to default farm

    def print_analysis_report(
        self, load_results: Dict[str, Any], query_stats: Dict[str, Any]
    ):
        """Print detailed analysis report"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)

        # Load Test Results
        print("\n🔥 LOAD TEST RESULTS:")
        print("  Total Requests: {load_results['total_requests']}")
        print("  Success Rate: {load_results['success_rate']}%")
        print("  Failed Requests: {load_results['failed_requests']}")
        print(
            "  Overall Avg Response Time: {load_results['overall_avg_response_time']}s"
        )
        print(
            "  Overall Max Response Time: {load_results['overall_max_response_time']}s"
        )

        # Per-endpoint analysis
        print("\n📋 PER-ENDPOINT ANALYSIS:")
        for endpoint, stats in load_results["endpoint_analysis"].items():
            print("  {endpoint}:")
            print("    Requests: {stats['requests']}")
            print("    Avg: {stats['avg_response_time']}s")
            print("    Min: {stats['min_response_time']}s")
            print("    Max: {stats['max_response_time']}s")
            print("    P95: {stats['p95_response_time']}s")

        # Database Query Stats
        print("\n💾 DATABASE QUERY STATISTICS:")
        print("  Total Queries: {query_stats.get('total_queries', 0)}")
        print("  Avg Query Time: {query_stats.get('avg_query_time', 0)}s")
        print("  Max Query Time: {query_stats.get('max_query_time', 0)}s")
        print("  Slow Queries Count: {query_stats.get('slow_queries_count', 0)}")

        # Slow Queries Analysis
        slow_queries = query_stats.get("recent_slow_queries", [])
        if slow_queries:
            print("\n🐌 RECENT SLOW QUERIES:")
            for i, slow_query in enumerate(slow_queries[:5], 1):  # Show top 5
                print("  {i}. Execution Time: {slow_query['execution_time']}s")
                query_preview = (
                    slow_query["query"][:100] + "..."
                    if len(slow_query["query"]) > 100
                    else slow_query["query"]
                )
                print("     Query: {query_preview}")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")

        # Response time recommendations
        slow_endpoints = [
            endpoint
            for endpoint, stats in load_results["endpoint_analysis"].items()
            if stats["avg_response_time"] > 1.0
        ]
        if slow_endpoints:
            print("  ⚠️  Slow endpoints detected (>1s avg): {', '.join(slow_endpoints)}")
            print("     Consider optimizing database queries or adding caching")

        # Database query recommendations
        if query_stats.get("slow_queries_count", 0) > 0:
            print(
                "  ⚠️  {query_stats['slow_queries_count']} slow database queries detected"
            )
            print(
                "     Review slow queries and consider adding indexes or query optimization"
            )

        if query_stats.get("avg_query_time", 0) > 0.1:
            print("  ⚠️  Average query time is {query_stats['avg_query_time']}s")
            print("     Consider query optimization or connection pooling improvements")

        # Success rate recommendations
        if load_results["success_rate"] < 95:
            print("  🚨 Low success rate ({load_results['success_rate']}%)")
            print("     Check error logs and consider improving error handling")

        print("\n" + "=" * 80)


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze Theobroma Geo API query performance"
    )
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument(
        "--concurrent", type=int, default=5, help="Concurrent requests per iteration"
    )
    parser.add_argument(
        "--iterations", type=int, default=10, help="Number of test iterations"
    )
    parser.add_argument(
        "--detailed-logging", action="store_true", help="Enable detailed query logging"
    )

    args = parser.parse_args()

    async with QueryAnalyzer(args.url) as analyzer:
        print("🔍 Theobroma Geo API Query Performance Analyzer")
        print("   Testing URL: {args.url}")
        print("   Concurrent requests: {args.concurrent}")
        print("   Iterations: {args.iterations}")

        # Get available farms
        farms = await analyzer.get_farms_list()
        test_farm = farms[0] if farms else "valley-verde"
        print("   Using test farm: {test_farm}")

        # Enable detailed logging if requested
        if args.detailed_logging:
            await analyzer.enable_detailed_logging()

        # Define test endpoints
        test_endpoints = [
            {"endpoint": f"/farms/{test_farm}/lots"},
            {
                "endpoint": "/farms/{test_farm}/security/events",
                "params": {"limit": 20},
            },
            {"endpoint": f"/farms/{test_farm}/weather"},
            {"endpoint": f"/farms/{test_farm}/analytics/production"},
            {"endpoint": "/farms"},
        ]

        try:
            # Run load test
            load_results = await analyzer.run_load_test(
                test_endpoints, args.concurrent, args.iterations
            )

            # Analyze results
            analysis = analyzer.analyze_results(load_results)

            # Get database query statistics
            query_stats = await analyzer.get_query_stats()

            # Print comprehensive report
            analyzer.print_analysis_report(analysis, query_stats)

        finally:
            # Clean up
            if args.detailed_logging:
                await analyzer.disable_detailed_logging()


if __name__ == "__main__":
    asyncio.run(main())
