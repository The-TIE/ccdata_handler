#!/usr/bin/env python3
"""
Comprehensive test runner for the unified data ingestion framework.

This script validates all components of the framework and provides a health
report on functionality, identifying any missing dependencies or configuration issues.
"""

import sys
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add src to path for imports
sys.path.insert(0, "src")


def test_imports() -> Dict[str, Any]:
    """Test that all framework modules can be imported."""
    results = {"status": "success", "tests": [], "errors": []}

    import_tests = [
        ("Configuration", "src.ingestion.config", "get_config"),
        (
            "Base Classes",
            "src.ingestion.base",
            "BaseIngestor,TimeSeriesIngestor,MetadataIngestor",
        ),
        ("Monitoring", "src.ingestion.monitoring", "IngestionMonitor"),
        ("Cache Manager", "src.ingestion.cache", "CacheManager"),
        ("Utils", "src.ingestion.utils", "BatchProcessor"),
        (
            "Asset Metadata Ingestor",
            "src.ingestion.ingestors.asset_metadata_ingestor",
            "AssetMetadataIngestor",
        ),
        (
            "Exchange Metadata Ingestor",
            "src.ingestion.ingestors.exchange_metadata_ingestor",
            "ExchangeMetadataIngestor",
        ),
        (
            "Spot OHLCV Ingestor",
            "src.ingestion.ingestors.spot_ohlcv_ingestor",
            "SpotOHLCVIngestor",
        ),
        (
            "Futures Data Ingestor",
            "src.ingestion.ingestors.futures_data_ingestor",
            "FuturesDataIngestor",
        ),
        (
            "Indices OHLCV Ingestor",
            "src.ingestion.ingestors.indices_ohlcv_ingestor",
            "IndicesOHLCVIngestor",
        ),
        (
            "Instrument Metadata Ingestor",
            "src.ingestion.ingestors.instrument_metadata_ingestor",
            "InstrumentMetadataIngestor",
        ),
        ("API Clients", "src.data_api.asset_api_client", "CcdataAssetApiClient"),
        ("Database Connection", "src.db.connection", "DbConnectionManager"),
        ("Logger Config", "src.logger_config", "setup_logger"),
    ]

    for test_name, module_name, classes in import_tests:
        try:
            module = __import__(module_name, fromlist=classes.split(","))
            for class_name in classes.split(","):
                getattr(module, class_name.strip())
            results["tests"].append(
                {
                    "name": test_name,
                    "status": "PASS",
                    "message": f"Successfully imported {module_name}",
                }
            )
        except Exception as e:
            results["tests"].append(
                {
                    "name": test_name,
                    "status": "FAIL",
                    "message": f"Failed to import {module_name}: {str(e)}",
                }
            )
            results["errors"].append(f"Import error in {test_name}: {str(e)}")
            results["status"] = "failure"

    return results


def test_configuration() -> Dict[str, Any]:
    """Test configuration loading and validation."""
    results = {"status": "success", "tests": [], "errors": []}

    try:
        from src.ingestion.config import get_config

        config = get_config()

        results["tests"].append(
            {
                "name": "Configuration Loading",
                "status": "PASS",
                "message": f"Configuration loaded for environment: {config.environment}",
            }
        )

        # Test required configuration sections
        config_tests = [
            ("Database Config", hasattr(config, "database")),
            ("API Config", hasattr(config, "api")),
            ("Ingestion Config", hasattr(config, "ingestion")),
            ("Monitoring Config", hasattr(config, "monitoring")),
            ("Cache Config", hasattr(config, "cache")),
        ]

        for test_name, condition in config_tests:
            if condition:
                results["tests"].append(
                    {
                        "name": test_name,
                        "status": "PASS",
                        "message": f"{test_name} section available",
                    }
                )
            else:
                results["tests"].append(
                    {
                        "name": test_name,
                        "status": "FAIL",
                        "message": f"{test_name} section missing",
                    }
                )
                results["errors"].append(f"Missing configuration section: {test_name}")
                results["status"] = "failure"

    except Exception as e:
        results["tests"].append(
            {
                "name": "Configuration Loading",
                "status": "FAIL",
                "message": f"Failed to load configuration: {str(e)}",
            }
        )
        results["errors"].append(f"Configuration error: {str(e)}")
        results["status"] = "failure"

    return results


def test_cli_tools() -> Dict[str, Any]:
    """Test CLI tools functionality."""
    results = {"status": "success", "tests": [], "errors": []}

    import subprocess

    cli_tests = [
        ("Unified Ingest Help", ["python", "-m", "scripts.unified_ingest", "--help"]),
        (
            "Migration Helper Help",
            ["python", "-m", "scripts.migrate_ingestion_script", "--help"],
        ),
        (
            "Asset Data V2 Help",
            ["python", "-m", "scripts.ingest_asset_data_v2", "--help"],
        ),
    ]

    for test_name, command in cli_tests:
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=30, cwd="."
            )

            if result.returncode == 0:
                results["tests"].append(
                    {
                        "name": test_name,
                        "status": "PASS",
                        "message": f"CLI tool executed successfully",
                    }
                )
            else:
                results["tests"].append(
                    {
                        "name": test_name,
                        "status": "FAIL",
                        "message": f"CLI tool failed with exit code {result.returncode}: {result.stderr}",
                    }
                )
                results["errors"].append(f"CLI error in {test_name}: {result.stderr}")
                results["status"] = "failure"

        except subprocess.TimeoutExpired:
            results["tests"].append(
                {"name": test_name, "status": "FAIL", "message": "CLI tool timed out"}
            )
            results["errors"].append(f"Timeout in {test_name}")
            results["status"] = "failure"
        except Exception as e:
            results["tests"].append(
                {
                    "name": test_name,
                    "status": "FAIL",
                    "message": f"CLI tool execution failed: {str(e)}",
                }
            )
            results["errors"].append(f"CLI execution error in {test_name}: {str(e)}")
            results["status"] = "failure"

    return results


async def test_database_connection() -> Dict[str, Any]:
    """Test database connectivity (without requiring actual database)."""
    results = {"status": "success", "tests": [], "errors": []}

    try:
        from src.db.connection import DbConnectionManager
        from src.ingestion.config import get_config

        config = get_config()

        # Test connection manager initialization
        db_manager = DbConnectionManager(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database,
        )

        results["tests"].append(
            {
                "name": "Database Manager Initialization",
                "status": "PASS",
                "message": "Database connection manager initialized successfully",
            }
        )

        # Note: We don't test actual connection as it requires database credentials
        results["tests"].append(
            {
                "name": "Database Connection Test",
                "status": "SKIP",
                "message": "Skipped - requires database credentials and connection",
            }
        )

    except Exception as e:
        results["tests"].append(
            {
                "name": "Database Manager Initialization",
                "status": "FAIL",
                "message": f"Failed to initialize database manager: {str(e)}",
            }
        )
        results["errors"].append(f"Database initialization error: {str(e)}")
        results["status"] = "failure"

    return results


def test_ingestor_initialization() -> Dict[str, Any]:
    """Test that ingestor classes can be initialized."""
    results = {"status": "success", "tests": [], "errors": []}

    try:
        from src.ingestion.config import get_config
        from src.data_api.asset_api_client import CcdataAssetApiClient
        from src.db.connection import DbConnectionManager

        config = get_config()

        # Test API client initialization
        api_client = CcdataAssetApiClient(config.api)
        results["tests"].append(
            {
                "name": "API Client Initialization",
                "status": "PASS",
                "message": "Asset API client initialized successfully",
            }
        )

        # Test database manager initialization
        db_manager = DbConnectionManager(
            host=config.database.host,
            port=config.database.port,
            user=config.database.user,
            password=config.database.password,
            database=config.database.database,
        )
        results["tests"].append(
            {
                "name": "Database Manager Initialization",
                "status": "PASS",
                "message": "Database manager initialized successfully",
            }
        )

        # Test ingestor initialization (without actual ingestion)
        from src.ingestion.ingestors.asset_metadata_ingestor import (
            AssetMetadataIngestor,
        )

        ingestor = AssetMetadataIngestor(
            api_client=api_client, db_client=db_manager, config=config
        )

        results["tests"].append(
            {
                "name": "Asset Metadata Ingestor Initialization",
                "status": "PASS",
                "message": "Asset metadata ingestor initialized successfully",
            }
        )

    except Exception as e:
        results["tests"].append(
            {
                "name": "Ingestor Initialization",
                "status": "FAIL",
                "message": f"Failed to initialize ingestor: {str(e)}",
            }
        )
        results["errors"].append(f"Ingestor initialization error: {str(e)}")
        results["status"] = "failure"

    return results


def test_framework_version() -> Dict[str, Any]:
    """Test framework version and info accessibility."""
    results = {"status": "success", "tests": [], "errors": []}

    try:
        # Check if pyproject.toml exists and can be read
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            results["tests"].append(
                {
                    "name": "Framework Version Info",
                    "status": "PASS",
                    "message": "pyproject.toml found with framework metadata",
                }
            )
        else:
            results["tests"].append(
                {
                    "name": "Framework Version Info",
                    "status": "FAIL",
                    "message": "pyproject.toml not found",
                }
            )
            results["errors"].append("Missing pyproject.toml file")
            results["status"] = "failure"

        # Check README files
        readme_files = ["README_UNIFIED_INGESTION.md", "README.md"]
        for readme in readme_files:
            if Path(readme).exists():
                results["tests"].append(
                    {
                        "name": f"Documentation - {readme}",
                        "status": "PASS",
                        "message": f"{readme} documentation available",
                    }
                )
            else:
                results["tests"].append(
                    {
                        "name": f"Documentation - {readme}",
                        "status": "WARN",
                        "message": f"{readme} not found",
                    }
                )

    except Exception as e:
        results["tests"].append(
            {
                "name": "Framework Version Info",
                "status": "FAIL",
                "message": f"Error checking framework info: {str(e)}",
            }
        )
        results["errors"].append(f"Framework info error: {str(e)}")
        results["status"] = "failure"

    return results


async def run_all_tests() -> Dict[str, Any]:
    """Run all validation tests."""
    print("🚀 Starting Unified Data Ingestion Framework Validation")
    print("=" * 80)

    test_results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "success",
        "test_suites": {},
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "warnings": 0,
        },
        "critical_issues": [],
        "recommendations": [],
    }

    # Define test suites
    test_suites = [
        ("Framework Imports", test_imports),
        ("Configuration", test_configuration),
        ("CLI Tools", test_cli_tools),
        ("Database Connection", test_database_connection),
        ("Ingestor Initialization", test_ingestor_initialization),
        ("Framework Version", test_framework_version),
    ]

    # Run each test suite
    for suite_name, test_func in test_suites:
        print(f"\n📋 Running {suite_name} tests...")

        try:
            if asyncio.iscoroutinefunction(test_func):
                suite_results = await test_func()
            else:
                suite_results = test_func()

            test_results["test_suites"][suite_name] = suite_results

            # Update summary
            for test in suite_results["tests"]:
                test_results["summary"]["total_tests"] += 1
                if test["status"] == "PASS":
                    test_results["summary"]["passed"] += 1
                    print(f"  ✅ {test['name']}: {test['message']}")
                elif test["status"] == "FAIL":
                    test_results["summary"]["failed"] += 1
                    print(f"  ❌ {test['name']}: {test['message']}")
                    test_results["overall_status"] = "failure"
                elif test["status"] == "SKIP":
                    test_results["summary"]["skipped"] += 1
                    print(f"  ⏭️  {test['name']}: {test['message']}")
                elif test["status"] == "WARN":
                    test_results["summary"]["warnings"] += 1
                    print(f"  ⚠️  {test['name']}: {test['message']}")

            # Collect critical issues
            if suite_results.get("errors"):
                test_results["critical_issues"].extend(suite_results["errors"])

        except Exception as e:
            print(f"  💥 Test suite {suite_name} crashed: {str(e)}")
            test_results["test_suites"][suite_name] = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
            test_results["overall_status"] = "failure"
            test_results["critical_issues"].append(
                f"Test suite {suite_name} crashed: {str(e)}"
            )

    # Add known issues from testing
    test_results["critical_issues"].extend(
        [
            "Database schema mismatch: 'datetime' column not found in market.cc_assets table",
            "Asset metadata ingestor incorrectly expects datetime fields for metadata records",
            "Unit test suite has 77 failures out of 314 tests (75% failure rate)",
            "Async fixture configuration issues in test_async_db.py",
            "Multiple test failures in base ingestor functionality",
        ]
    )

    # Add recommendations
    test_results["recommendations"] = [
        "Fix database schema mismatch by updating table schema or ingestor expectations",
        "Review and fix asset metadata ingestor to handle metadata records correctly",
        "Fix async test fixtures in test_async_db.py using @pytest_asyncio.fixture",
        "Review and fix base ingestor test mocks and assertions",
        "Update cache manager tests to handle Redis connection properly",
        "Review monitoring module test expectations and fix metric collection",
        "Consider implementing dry-run mode for all CLI commands",
        "Add integration tests that don't require actual database connections",
        "Implement proper error handling for missing database tables",
        "Add validation for ingestor data type compatibility",
    ]

    return test_results


def print_summary(results: Dict[str, Any]):
    """Print test summary and recommendations."""
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)

    summary = results["summary"]
    print(
        f"Overall Status: {'✅ PASS' if results['overall_status'] == 'success' else '❌ FAIL'}"
    )
    print(f"Total Tests: {summary['total_tests']}")
    print(
        f"Passed: {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)"
    )
    print(
        f"Failed: {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)"
    )
    print(
        f"Skipped: {summary['skipped']} ({summary['skipped']/summary['total_tests']*100:.1f}%)"
    )
    print(
        f"Warnings: {summary['warnings']} ({summary['warnings']/summary['total_tests']*100:.1f}%)"
    )

    if results["critical_issues"]:
        print(f"\n🚨 CRITICAL ISSUES ({len(results['critical_issues'])})")
        print("-" * 40)
        for i, issue in enumerate(results["critical_issues"], 1):
            print(f"{i}. {issue}")

    if results["recommendations"]:
        print(f"\n💡 RECOMMENDATIONS ({len(results['recommendations'])})")
        print("-" * 40)
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")

    print(
        f"\n📄 Full results saved to: test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )


async def main():
    """Main test runner function."""
    try:
        results = await run_all_tests()

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{timestamp}.json"

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        # Print summary
        print_summary(results)

        # Exit with appropriate code
        exit_code = 0 if results["overall_status"] == "success" else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"💥 Test runner crashed: {str(e)}")
        print(traceback.format_exc())
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
