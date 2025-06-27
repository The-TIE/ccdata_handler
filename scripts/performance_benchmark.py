#!/usr/bin/env python3
"""
Performance Benchmark Script

This script compares performance between old ingestion scripts and the new unified
data ingestion framework. It measures API call efficiency, database write speed,
memory usage, and overall throughput to demonstrate improvements.

Features:
- Compare performance between old scripts and new unified framework
- Measure API call efficiency, database write speed, and memory usage
- Generate performance comparison reports
- Support for benchmarking specific data types
- Output metrics in both human-readable and JSON formats
- Memory profiling and resource utilization tracking
"""

import asyncio
import argparse
import sys
import json
import time
import psutil
import tracemalloc
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import subprocess
import logging
from dataclasses import dataclass, asdict

# Add src to path for imports
sys.path.insert(0, "src")

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.ingestion.config import get_config
from scripts.unified_ingest import UnifiedIngestCLI

# Configure logging
logger = setup_logger(__name__, log_to_console=True)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    # Timing metrics
    total_duration: float = 0.0
    api_call_duration: float = 0.0
    database_write_duration: float = 0.0
    processing_duration: float = 0.0

    # Throughput metrics
    records_processed: int = 0
    records_per_second: float = 0.0
    api_calls_made: int = 0
    api_calls_per_second: float = 0.0

    # Resource metrics
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0

    # Quality metrics
    success_rate: float = 100.0
    error_count: int = 0
    retry_count: int = 0

    # Database metrics
    db_connections_used: int = 0
    db_query_count: int = 0
    db_avg_query_time: float = 0.0


class PerformanceBenchmark:
    """
    Performance benchmarking system for comparing old vs new ingestion methods.

    Provides comprehensive performance analysis including timing, throughput,
    resource utilization, and quality metrics.
    """

    def __init__(self):
        """Initialize the performance benchmark."""
        self.config = get_config()
        self.db_connection = None
        self.unified_cli = None
        self.benchmark_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_info": {},
            "benchmarks": {},
            "comparisons": {},
            "recommendations": [],
        }

    async def initialize(self):
        """Initialize database connection and components."""
        self.db_connection = DbConnectionManager()
        self.unified_cli = UnifiedIngestCLI()
        await self.unified_cli.initialize(enable_monitoring=True, enable_caching=True)

        # Collect system information
        self.benchmark_results["system_info"] = self._collect_system_info()

        logger.info("Performance benchmark initialized")

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for benchmark context."""
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_usage": {
                "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
            },
            "python_version": sys.version,
            "platform": sys.platform,
        }

    async def benchmark_unified_framework(
        self,
        data_type: str,
        test_params: Dict[str, Any],
        duration_seconds: Optional[int] = None,
    ) -> PerformanceMetrics:
        """
        Benchmark the unified ingestion framework.

        Args:
            data_type: Type of data to benchmark
            test_params: Parameters for the test
            duration_seconds: Maximum duration for the test

        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking unified framework for {data_type}")

        # Start resource monitoring
        process = psutil.Process()
        tracemalloc.start()
        start_time = time.time()
        start_cpu_times = process.cpu_times()
        start_io = process.io_counters()

        metrics = PerformanceMetrics()
        cpu_samples = []
        memory_samples = []

        try:
            # Monitor resources during execution
            async def monitor_resources():
                while True:
                    cpu_samples.append(process.cpu_percent())
                    memory_samples.append(process.memory_info().rss / (1024**2))  # MB
                    await asyncio.sleep(0.5)

            # Start monitoring task
            monitor_task = asyncio.create_task(monitor_resources())

            # Execute the ingestion
            api_start = time.time()
            result = await self.unified_cli.ingest_single(data_type, **test_params)
            api_end = time.time()

            # Stop monitoring
            monitor_task.cancel()

            # Calculate metrics
            end_time = time.time()
            end_cpu_times = process.cpu_times()
            end_io = process.io_counters()

            metrics.total_duration = end_time - start_time
            metrics.api_call_duration = api_end - api_start

            # Extract results
            if result.get("status") == "success":
                metrics.records_processed = result.get("records_processed", 0)
                metrics.api_calls_made = result.get("api_calls_made", 0)
                metrics.success_rate = 100.0
            else:
                metrics.error_count = 1
                metrics.success_rate = 0.0

            # Calculate throughput
            if metrics.total_duration > 0:
                metrics.records_per_second = (
                    metrics.records_processed / metrics.total_duration
                )
                metrics.api_calls_per_second = (
                    metrics.api_calls_made / metrics.total_duration
                )

            # Resource metrics
            metrics.peak_memory_mb = max(memory_samples) if memory_samples else 0
            metrics.avg_cpu_percent = (
                sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            )

            # I/O metrics
            metrics.disk_io_read_mb = (end_io.read_bytes - start_io.read_bytes) / (
                1024**2
            )
            metrics.disk_io_write_mb = (end_io.write_bytes - start_io.write_bytes) / (
                1024**2
            )

            # Memory profiling
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            logger.info(
                f"Unified framework benchmark completed. Records/sec: {metrics.records_per_second:.2f}"
            )

        except Exception as e:
            logger.error(f"Error in unified framework benchmark: {e}")
            metrics.error_count = 1
            metrics.success_rate = 0.0
            tracemalloc.stop()

        return metrics

    async def benchmark_legacy_script(
        self, script_path: str, script_args: List[str], timeout_seconds: int = 300
    ) -> PerformanceMetrics:
        """
        Benchmark a legacy ingestion script.

        Args:
            script_path: Path to the legacy script
            script_args: Arguments for the script
            timeout_seconds: Timeout for script execution

        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking legacy script: {script_path}")

        metrics = PerformanceMetrics()
        start_time = time.time()

        try:
            # Prepare command
            cmd = [sys.executable, script_path] + script_args

            # Execute script with monitoring
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=Path.cwd(),
            )

            # Monitor the process
            psutil_process = psutil.Process(process.pid)
            cpu_samples = []
            memory_samples = []

            async def monitor_process():
                while process.returncode is None:
                    try:
                        cpu_samples.append(psutil_process.cpu_percent())
                        memory_samples.append(
                            psutil_process.memory_info().rss / (1024**2)
                        )
                        await asyncio.sleep(0.5)
                    except psutil.NoSuchProcess:
                        break

            # Start monitoring
            monitor_task = asyncio.create_task(monitor_process())

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                metrics.error_count = 1
                metrics.success_rate = 0.0
                logger.error(f"Legacy script timed out after {timeout_seconds} seconds")
                return metrics

            # Stop monitoring
            monitor_task.cancel()

            end_time = time.time()
            metrics.total_duration = end_time - start_time

            # Parse output for metrics (if available)
            if process.returncode == 0:
                metrics.success_rate = 100.0
                # Try to extract metrics from stdout
                output_text = stdout.decode("utf-8")
                metrics.records_processed = self._extract_records_from_output(
                    output_text
                )
            else:
                metrics.error_count = 1
                metrics.success_rate = 0.0
                logger.error(
                    f"Legacy script failed with return code {process.returncode}"
                )
                logger.error(f"Error output: {stderr.decode('utf-8')}")

            # Resource metrics
            if cpu_samples:
                metrics.avg_cpu_percent = sum(cpu_samples) / len(cpu_samples)
            if memory_samples:
                metrics.peak_memory_mb = max(memory_samples)

            # Calculate throughput
            if metrics.total_duration > 0 and metrics.records_processed > 0:
                metrics.records_per_second = (
                    metrics.records_processed / metrics.total_duration
                )

            logger.info(
                f"Legacy script benchmark completed. Duration: {metrics.total_duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error benchmarking legacy script: {e}")
            metrics.error_count = 1
            metrics.success_rate = 0.0
            metrics.total_duration = time.time() - start_time

        return metrics

    def _extract_records_from_output(self, output: str) -> int:
        """Extract record count from script output."""
        # Look for common patterns in output
        patterns = [
            r"processed (\d+) records",
            r"inserted (\d+) records",
            r"(\d+) records processed",
            r"Total records: (\d+)",
        ]

        import re

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    async def run_comparative_benchmark(
        self,
        data_type: str,
        legacy_script_path: str,
        test_params: Dict[str, Any],
        legacy_script_args: List[str],
        iterations: int = 3,
    ) -> Dict[str, Any]:
        """
        Run comparative benchmark between unified framework and legacy script.

        Args:
            data_type: Type of data to benchmark
            legacy_script_path: Path to legacy script
            test_params: Parameters for unified framework test
            legacy_script_args: Arguments for legacy script
            iterations: Number of iterations to run

        Returns:
            Comparative benchmark results
        """
        logger.info(
            f"Running comparative benchmark for {data_type} ({iterations} iterations)"
        )

        unified_results = []
        legacy_results = []

        # Run multiple iterations
        for i in range(iterations):
            logger.info(f"Running iteration {i+1}/{iterations}")

            # Benchmark unified framework
            try:
                unified_metrics = await self.benchmark_unified_framework(
                    data_type, test_params
                )
                unified_results.append(unified_metrics)
            except Exception as e:
                logger.error(
                    f"Unified framework benchmark failed in iteration {i+1}: {e}"
                )

            # Wait between tests
            await asyncio.sleep(2)

            # Benchmark legacy script
            try:
                legacy_metrics = await self.benchmark_legacy_script(
                    legacy_script_path, legacy_script_args
                )
                legacy_results.append(legacy_metrics)
            except Exception as e:
                logger.error(f"Legacy script benchmark failed in iteration {i+1}: {e}")

            # Wait between iterations
            await asyncio.sleep(5)

        # Calculate averages and comparisons
        comparison = self._calculate_comparison(unified_results, legacy_results)
        comparison["data_type"] = data_type
        comparison["iterations"] = iterations
        comparison["test_timestamp"] = datetime.now(timezone.utc).isoformat()

        return comparison

    def _calculate_comparison(
        self,
        unified_results: List[PerformanceMetrics],
        legacy_results: List[PerformanceMetrics],
    ) -> Dict[str, Any]:
        """Calculate comparison metrics between unified and legacy results."""

        def avg_metrics(results: List[PerformanceMetrics]) -> Dict[str, float]:
            if not results:
                return {}

            metrics_dict = {}
            for field in PerformanceMetrics.__dataclass_fields__:
                values = [
                    getattr(result, field)
                    for result in results
                    if getattr(result, field) is not None
                ]
                metrics_dict[field] = sum(values) / len(values) if values else 0.0

            return metrics_dict

        unified_avg = avg_metrics(unified_results)
        legacy_avg = avg_metrics(legacy_results)

        comparison = {
            "unified_framework": {
                "metrics": unified_avg,
                "iterations_successful": len(
                    [r for r in unified_results if r.success_rate > 0]
                ),
            },
            "legacy_script": {
                "metrics": legacy_avg,
                "iterations_successful": len(
                    [r for r in legacy_results if r.success_rate > 0]
                ),
            },
            "improvements": {},
            "summary": {},
        }

        # Calculate improvements
        if legacy_avg and unified_avg:
            for metric in [
                "total_duration",
                "records_per_second",
                "peak_memory_mb",
                "avg_cpu_percent",
            ]:
                legacy_val = legacy_avg.get(metric, 0)
                unified_val = unified_avg.get(metric, 0)

                if legacy_val > 0:
                    if (
                        metric == "total_duration"
                        or metric == "peak_memory_mb"
                        or metric == "avg_cpu_percent"
                    ):
                        # Lower is better
                        improvement = ((legacy_val - unified_val) / legacy_val) * 100
                    else:
                        # Higher is better
                        improvement = ((unified_val - legacy_val) / legacy_val) * 100

                    comparison["improvements"][metric] = {
                        "percentage": round(improvement, 2),
                        "legacy_value": round(legacy_val, 2),
                        "unified_value": round(unified_val, 2),
                    }

        # Generate summary
        improvements = comparison["improvements"]
        if improvements:
            speed_improvement = improvements.get("total_duration", {}).get(
                "percentage", 0
            )
            throughput_improvement = improvements.get("records_per_second", {}).get(
                "percentage", 0
            )
            memory_improvement = improvements.get("peak_memory_mb", {}).get(
                "percentage", 0
            )

            comparison["summary"] = {
                "speed_improvement_percent": speed_improvement,
                "throughput_improvement_percent": throughput_improvement,
                "memory_improvement_percent": memory_improvement,
                "overall_winner": "unified" if speed_improvement > 0 else "legacy",
            }

        return comparison

    async def benchmark_specific_operations(
        self, operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Benchmark specific operations in isolation.

        Args:
            operations: List of operations to benchmark

        Returns:
            Benchmark results for each operation
        """
        logger.info(f"Benchmarking {len(operations)} specific operations")

        results = {}

        for operation in operations:
            op_name = operation.get("name", "unknown")
            op_type = operation.get("type", "spot_ohlcv")
            op_params = operation.get("params", {})

            logger.info(f"Benchmarking operation: {op_name}")

            try:
                metrics = await self.benchmark_unified_framework(op_type, op_params)
                results[op_name] = {"metrics": asdict(metrics), "status": "success"}
            except Exception as e:
                logger.error(f"Error benchmarking operation {op_name}: {e}")
                results[op_name] = {"status": "error", "error": str(e)}

        return results

    def generate_performance_report(
        self, benchmark_results: Dict[str, Any], output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            benchmark_results: Results from benchmarks
            output_format: Output format ('json' or 'html')

        Returns:
            Performance report
        """
        logger.info("Generating performance report")

        report = {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "system_info": self.benchmark_results["system_info"],
                "report_version": "1.0",
            },
            "executive_summary": {},
            "detailed_results": benchmark_results,
            "recommendations": [],
        }

        # Generate executive summary
        if "improvements" in benchmark_results:
            improvements = benchmark_results["improvements"]
            summary = benchmark_results.get("summary", {})

            report["executive_summary"] = {
                "overall_performance_improvement": summary.get(
                    "speed_improvement_percent", 0
                ),
                "throughput_improvement": summary.get(
                    "throughput_improvement_percent", 0
                ),
                "memory_efficiency_improvement": summary.get(
                    "memory_improvement_percent", 0
                ),
                "recommended_approach": summary.get("overall_winner", "unified"),
                "key_benefits": self._generate_key_benefits(improvements),
            }

        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(
            benchmark_results
        )

        return report

    def _generate_key_benefits(self, improvements: Dict[str, Any]) -> List[str]:
        """Generate key benefits from improvement metrics."""
        benefits = []

        speed_improvement = improvements.get("total_duration", {}).get("percentage", 0)
        if speed_improvement > 10:
            benefits.append(f"Execution speed improved by {speed_improvement:.1f}%")

        throughput_improvement = improvements.get("records_per_second", {}).get(
            "percentage", 0
        )
        if throughput_improvement > 10:
            benefits.append(
                f"Data throughput increased by {throughput_improvement:.1f}%"
            )

        memory_improvement = improvements.get("peak_memory_mb", {}).get("percentage", 0)
        if memory_improvement > 10:
            benefits.append(f"Memory usage reduced by {memory_improvement:.1f}%")

        if not benefits:
            benefits.append(
                "Performance characteristics are comparable between approaches"
            )

        return benefits

    def _generate_performance_recommendations(
        self, results: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations based on results."""
        recommendations = []

        summary = results.get("summary", {})
        improvements = results.get("improvements", {})

        if summary.get("overall_winner") == "unified":
            recommendations.append(
                "Migrate to unified framework for improved performance"
            )

            if improvements.get("total_duration", {}).get("percentage", 0) > 20:
                recommendations.append(
                    "Significant speed improvements justify immediate migration"
                )

            if improvements.get("peak_memory_mb", {}).get("percentage", 0) > 15:
                recommendations.append(
                    "Memory efficiency gains will reduce infrastructure costs"
                )

        else:
            recommendations.append(
                "Consider optimizing unified framework before migration"
            )
            recommendations.append(
                "Analyze specific bottlenecks in unified framework implementation"
            )

        # General recommendations
        recommendations.extend(
            [
                "Monitor performance metrics regularly after migration",
                "Consider implementing caching for frequently accessed data",
                "Use parallel processing for large batch operations",
                "Optimize database connection pooling based on workload",
            ]
        )

        return recommendations

    async def save_report(
        self, report: Dict[str, Any], output_path: str, format_type: str = "json"
    ):
        """Save performance report to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "json":
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

        elif format_type == "html":
            html_content = self._generate_html_report(report)
            with open(output_path, "w") as f:
                f.write(html_content)

        else:
            # Text format
            with open(output_path, "w") as f:
                f.write("PERFORMANCE BENCHMARK REPORT\n")
                f.write("=" * 50 + "\n\n")

                summary = report.get("executive_summary", {})
                f.write(
                    f"Overall Performance Improvement: {summary.get('overall_performance_improvement', 0):.1f}%\n"
                )
                f.write(
                    f"Throughput Improvement: {summary.get('throughput_improvement', 0):.1f}%\n"
                )
                f.write(
                    f"Memory Efficiency Improvement: {summary.get('memory_efficiency_improvement', 0):.1f}%\n"
                )
                f.write(
                    f"Recommended Approach: {summary.get('recommended_approach', 'N/A')}\n\n"
                )

                f.write("KEY BENEFITS:\n")
                for benefit in summary.get("key_benefits", []):
                    f.write(f"• {benefit}\n")

                f.write("\nRECOMMENDATIONS:\n")
                for rec in report.get("recommendations", []):
                    f.write(f"• {rec}\n")

        logger.info(f"Performance report saved to: {output_path}")

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML performance report."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Benchmark Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
                .metric { margin: 10px 0; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #007bff; }
                .improvement { color: green; font-weight: bold; }
                .degradation { color: red; font-weight: bold; }
                .recommendations { background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Performance Benchmark Report</h1>
                <p>Generated: {timestamp}</p>
            </div>
        """.format(
            timestamp=report["report_metadata"]["generated_at"]
        )

        # Add executive summary
        summary = report.get("executive_summary", {})
        html += f"""
            <h2>Executive Summary</h2>
            <div class="metric">
                <strong>Overall Performance Improvement:</strong> 
                <span class="{'improvement' if summary.get('overall_performance_improvement', 0) > 0 else 'degradation'}">
                    {summary.get('overall_performance_improvement', 0):.1f}%
                </span>
            </div>
        """

        # Add recommendations
        html += """
            <div class="recommendations">
                <h3>Recommendations</h3>
                <ul>
        """
        for rec in report.get("recommendations", []):
            html += f"<li>{rec}</li>"

        html += """
                </ul>
            </div>
        </body>
        </html>
        """

        return html

    async def cleanup(self):
        """Clean up resources."""
        if self.unified_cli:
            await self.unified_cli.cleanup()

        if self.db_connection:
            self.db_connection.close_connection()

        logger.info("Performance benchmark cleanup completed")


async def main():
    """Main function for the performance benchmark script."""
    parser = argparse.ArgumentParser(
        description="Performance benchmark for comparing old vs new ingestion systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare unified framework vs legacy script
  python performance_benchmark.py --compare --data-type spot_ohlcv --legacy-script scripts/ingest_daily_ohlcv_spot_data.py

  # Benchmark specific operations
  python performance_benchmark.py --benchmark-operations --config benchmark_config.json

  # Quick performance test
  python performance_benchmark.py --quick-test --data-type futures_ohlcv --output performance_report.json

  # Full comparative analysis
  python performance_benchmark.py --full-analysis --iterations 5 --output-dir ./benchmark_reports/
        """,
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run comparative benchmark between unified framework and legacy script",
    )

    parser.add_argument(
        "--data-type",
        choices=[
            "spot_ohlcv",
            "futures_ohlcv",
            "futures_funding_rate",
            "futures_open_interest",
            "indices_ohlcv",
        ],
        default="spot_ohlcv",
        help="Type of data to benchmark",
    )

    parser.add_argument("--legacy-script", help="Path to legacy script for comparison")

    parser.add_argument(
        "--legacy-args", nargs="*", default=[], help="Arguments for legacy script"
    )

    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of iterations to run for each test",
    )

    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Run quick performance test (single iteration, small dataset)",
    )

    parser.add_argument(
        "--benchmark-operations",
        action="store_true",
        help="Benchmark specific operations from config file",
    )

    parser.add_argument("--config", help="Configuration file for benchmark operations")

    parser.add_argument(
        "--output",
        default="performance_report.json",
        help="Output file path for performance report",
    )

    parser.add_argument("--output-dir", help="Output directory for multiple reports")

    parser.add_argument(
        "--format",
        choices=["json", "html", "text"],
        default="json",
        help="Output format for reports",
    )

    parser.add_argument(
        "--full-analysis",
        action="store_true",
        help="Run full performance analysis with multiple data types",
    )

    args = parser.parse_args()

    # Initialize benchmark
    benchmark = PerformanceBenchmark()
    await benchmark.initialize()

    try:
        if args.compare and args.legacy_script:
            # Run comparative benchmark
            test_params = {"pair_limit": 10 if args.quick_test else 50}

            result = await benchmark.run_comparative_benchmark(
                args.data_type,
                args.legacy_script,
                test_params,
                args.legacy_args,
                1 if args.quick_test else args.iterations,
            )

            # Generate report
            report = benchmark.generate_performance_report(result, args.format)

            # Save report
            output_path = args.output
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = (
                    output_dir
                    / f"comparison_{args.data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
                )

            await benchmark.save_report(report, str(output_path), args.format)

            # Print summary
            summary = report.get("executive_summary", {})
            print(f"\nPerformance Comparison Summary:")
            print(
                f"Overall Improvement: {summary.get('overall_performance_improvement', 0):.1f}%"
            )
            print(
                f"Throughput Improvement: {summary.get('throughput_improvement', 0):.1f}%"
            )
            print(
                f"Memory Efficiency: {summary.get('memory_efficiency_improvement', 0):.1f}%"
            )
            print(f"Report saved to: {output_path}")

        elif args.benchmark_operations and args.config:
            # Benchmark specific operations
            with open(args.config, "r") as f:
                operations = json.load(f)

            results = await benchmark.benchmark_specific_operations(operations)

            # Save results
            output_path = args.output or "operations_benchmark.json"
            await benchmark.save_report(
                {"operations": results}, output_path, args.format
            )

            print(f"Operations benchmark completed. Results saved to: {output_path}")

        elif args.full_analysis:
            # Run full analysis across multiple data types
            data_types = ["spot_ohlcv", "futures_ohlcv", "indices_ohlcv"]
            all_results = {}

            for data_type in data_types:
                print(f"Analyzing {data_type}...")
                test_params = {"pair_limit": 20, "asset_limit": 20}

                metrics = await benchmark.benchmark_unified_framework(
                    data_type, test_params
                )
                all_results[data_type] = asdict(metrics)
            # Generate comprehensive report
            report = {
                "full_analysis": all_results,
                "summary": {
                    "total_data_types_tested": len(data_types),
                    "average_throughput": sum(
                        r.get("records_per_second", 0) for r in all_results.values()
                    )
                    / len(all_results),
                    "total_records_processed": sum(
                        r.get("records_processed", 0) for r in all_results.values()
                    ),
                },
            }

            # Save comprehensive report
            output_path = args.output or "full_analysis_report.json"
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = (
                    output_dir
                    / f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
                )

            await benchmark.save_report(report, str(output_path), args.format)

            print(f"Full analysis completed. Report saved to: {output_path}")

        else:
            # Default: benchmark unified framework only
            test_params = {"pair_limit": 10 if args.quick_test else 50}

            metrics = await benchmark.benchmark_unified_framework(
                args.data_type, test_params
            )

            report = {
                "single_benchmark": {
                    "data_type": args.data_type,
                    "metrics": asdict(metrics),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }

            output_path = args.output or f"benchmark_{args.data_type}.json"
            await benchmark.save_report(report, output_path, args.format)

            print(f"Benchmark completed. Records/sec: {metrics.records_per_second:.2f}")
            print(f"Report saved to: {output_path}")

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)

    finally:
        await benchmark.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
