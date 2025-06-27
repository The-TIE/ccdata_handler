#!/usr/bin/env python3
"""
Data Migration Validation Script

This script validates the migration from old ingestion scripts to the new unified
data ingestion framework by comparing data integrity, completeness, and consistency
between the old and new systems.

Features:
- Compare data between old and new ingestion methods
- Validate data integrity after migration
- Check for missing records or discrepancies
- Generate comprehensive validation reports
- Support for sample size options (quick vs thorough validation)
- Detailed logging and error reporting
"""

import asyncio
import argparse
import sys
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

# Add src to path for imports
sys.path.insert(0, "src")

from src.logger_config import setup_logger
from src.db.connection import DbConnectionManager
from src.ingestion.config import get_config

# from src.utils import format_timestamp  # Not used, commented out

# Configure logging
logger = setup_logger(__name__, log_to_console=True)


class MigrationValidator:
    """
    Validates data migration from old to new ingestion systems.

    Performs comprehensive validation including data integrity checks,
    completeness verification, and consistency analysis.
    """

    def __init__(self):
        """Initialize the migration validator."""
        self.config = get_config()
        self.db_connection = None
        self.validation_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_summary": {},
            "table_validations": {},
            "discrepancies": [],
            "recommendations": [],
        }

    async def initialize(self):
        """Initialize database connection and components."""
        self.db_connection = DbConnectionManager()
        logger.info("Migration validator initialized")

    async def validate_table_integrity(
        self,
        table_name: str,
        sample_size: Optional[int] = None,
        date_range_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Validate integrity of a specific table.

        Args:
            table_name: Name of the table to validate
            sample_size: Number of records to sample (None for all)
            date_range_days: Number of days to look back for validation

        Returns:
            Validation results for the table
        """
        logger.info(f"Validating table integrity: {table_name}")

        validation_result = {
            "table_name": table_name,
            "total_records": 0,
            "sample_size": sample_size,
            "validation_checks": {},
            "issues_found": [],
            "data_quality_score": 0.0,
        }

        try:
            # Get table record count
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            if "timestamp" in await self._get_table_columns(table_name):
                end_date = datetime.now(timezone.utc)
                start_date = end_date - timedelta(days=date_range_days)
                count_query += f" WHERE timestamp >= '{start_date.isoformat()}' AND timestamp <= '{end_date.isoformat()}'"

            count_result = await self.db_connection.execute_query(count_query)
            validation_result["total_records"] = count_result[0]["total"]

            # Determine sample size
            actual_sample_size = sample_size or validation_result["total_records"]
            if sample_size and sample_size < validation_result["total_records"]:
                validation_result["sample_size"] = sample_size
            else:
                validation_result["sample_size"] = validation_result["total_records"]

            # Run validation checks
            validation_result["validation_checks"] = (
                await self._run_table_validation_checks(
                    table_name, actual_sample_size, date_range_days
                )
            )

            # Calculate data quality score
            validation_result["data_quality_score"] = (
                self._calculate_data_quality_score(
                    validation_result["validation_checks"]
                )
            )

            logger.info(
                f"Table {table_name} validation completed. Quality score: {validation_result['data_quality_score']:.2f}"
            )

        except Exception as e:
            logger.error(f"Error validating table {table_name}: {e}")
            validation_result["issues_found"].append(
                {"type": "validation_error", "message": str(e), "severity": "high"}
            )

        return validation_result

    async def _run_table_validation_checks(
        self, table_name: str, sample_size: int, date_range_days: int
    ) -> Dict[str, Any]:
        """Run comprehensive validation checks on a table."""
        checks = {}

        # Get table columns
        columns = await self._get_table_columns(table_name)

        # Check for null values in critical columns
        checks["null_value_check"] = await self._check_null_values(
            table_name, columns, sample_size
        )

        # Check for duplicate records
        checks["duplicate_check"] = await self._check_duplicates(
            table_name, sample_size
        )

        # Check data freshness
        if "timestamp" in columns:
            checks["freshness_check"] = await self._check_data_freshness(
                table_name, date_range_days
            )

        # Check data consistency
        checks["consistency_check"] = await self._check_data_consistency(
            table_name, columns, sample_size
        )

        # Check for data anomalies
        checks["anomaly_check"] = await self._check_data_anomalies(
            table_name, columns, sample_size
        )

        return checks

    async def _get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table."""
        query = f"DESCRIBE {table_name}"
        result = await self.db_connection.execute_query(query)
        return [row["Field"] for row in result]

    async def _check_null_values(
        self, table_name: str, columns: List[str], sample_size: int
    ) -> Dict[str, Any]:
        """Check for null values in critical columns."""
        null_check = {"status": "passed", "issues": [], "null_percentages": {}}

        # Critical columns that shouldn't have nulls
        critical_columns = ["id", "timestamp", "symbol", "market", "exchange"]
        critical_columns = [col for col in critical_columns if col in columns]

        for column in critical_columns:
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({column}) as non_null,
                    (COUNT(*) - COUNT({column})) as null_count,
                    ROUND(((COUNT(*) - COUNT({column})) / COUNT(*)) * 100, 2) as null_percentage
                FROM {table_name}
                LIMIT {sample_size}
            """

            result = await self.db_connection.execute_query(query)
            null_percentage = result[0]["null_percentage"]
            null_check["null_percentages"][column] = null_percentage

            if null_percentage > 0:
                null_check["status"] = "failed"
                null_check["issues"].append(
                    {
                        "column": column,
                        "null_percentage": null_percentage,
                        "null_count": result[0]["null_count"],
                    }
                )

        return null_check

    async def _check_duplicates(
        self, table_name: str, sample_size: int
    ) -> Dict[str, Any]:
        """Check for duplicate records."""
        duplicate_check = {
            "status": "passed",
            "duplicate_count": 0,
            "duplicate_percentage": 0.0,
        }

        # Get table columns to build a comprehensive duplicate check
        columns = await self._get_table_columns(table_name)

        # Exclude auto-increment ID columns from duplicate check
        check_columns = [
            col for col in columns if col not in ["id", "created_at", "updated_at"]
        ]

        if check_columns:
            columns_str = ", ".join(check_columns)
            query = f"""
                SELECT COUNT(*) as total_records,
                       COUNT(DISTINCT {columns_str}) as unique_records
                FROM (SELECT {columns_str} FROM {table_name} LIMIT {sample_size}) as sample
            """

            result = await self.db_connection.execute_query(query)
            total_records = result[0]["total_records"]
            unique_records = result[0]["unique_records"]
            duplicate_count = total_records - unique_records

            duplicate_check["duplicate_count"] = duplicate_count
            duplicate_check["duplicate_percentage"] = (
                (duplicate_count / total_records) * 100 if total_records > 0 else 0
            )

            if duplicate_count > 0:
                duplicate_check["status"] = (
                    "warning"
                    if duplicate_check["duplicate_percentage"] < 5
                    else "failed"
                )

        return duplicate_check

    async def _check_data_freshness(
        self, table_name: str, date_range_days: int
    ) -> Dict[str, Any]:
        """Check data freshness based on timestamp columns."""
        freshness_check = {
            "status": "passed",
            "latest_timestamp": None,
            "hours_since_latest": 0,
        }

        query = f"SELECT MAX(timestamp) as latest_timestamp FROM {table_name}"
        result = await self.db_connection.execute_query(query)

        if result and result[0]["latest_timestamp"]:
            latest_timestamp = result[0]["latest_timestamp"]
            freshness_check["latest_timestamp"] = latest_timestamp.isoformat()

            hours_since_latest = (
                datetime.now(timezone.utc) - latest_timestamp
            ).total_seconds() / 3600
            freshness_check["hours_since_latest"] = hours_since_latest

            # Data is considered stale if it's more than 25 hours old for daily data
            if hours_since_latest > 25:
                freshness_check["status"] = (
                    "warning" if hours_since_latest < 48 else "failed"
                )
        else:
            freshness_check["status"] = "failed"
            freshness_check["latest_timestamp"] = None

        return freshness_check

    async def _check_data_consistency(
        self, table_name: str, columns: List[str], sample_size: int
    ) -> Dict[str, Any]:
        """Check data consistency and format validation."""
        consistency_check = {"status": "passed", "issues": []}

        # Check for negative values in price/volume columns
        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "price",
            "funding_rate",
        ]
        numeric_columns = [col for col in numeric_columns if col in columns]

        for column in numeric_columns:
            query = f"""
                SELECT COUNT(*) as negative_count
                FROM {table_name}
                WHERE {column} < 0
                LIMIT {sample_size}
            """

            result = await self.db_connection.execute_query(query)
            negative_count = result[0]["negative_count"]

            if negative_count > 0:
                consistency_check["status"] = "warning"
                consistency_check["issues"].append(
                    {
                        "type": "negative_values",
                        "column": column,
                        "count": negative_count,
                    }
                )

        # Check for OHLC consistency (high >= low, etc.)
        if all(col in columns for col in ["open", "high", "low", "close"]):
            query = f"""
                SELECT COUNT(*) as inconsistent_ohlc
                FROM {table_name}
                WHERE high < low OR high < open OR high < close OR low > open OR low > close
                LIMIT {sample_size}
            """

            result = await self.db_connection.execute_query(query)
            inconsistent_count = result[0]["inconsistent_ohlc"]

            if inconsistent_count > 0:
                consistency_check["status"] = "failed"
                consistency_check["issues"].append(
                    {"type": "ohlc_inconsistency", "count": inconsistent_count}
                )

        return consistency_check

    async def _check_data_anomalies(
        self, table_name: str, columns: List[str], sample_size: int
    ) -> Dict[str, Any]:
        """Check for data anomalies and outliers."""
        anomaly_check = {"status": "passed", "anomalies": []}

        # Check for extreme price movements (more than 1000% change)
        if all(col in columns for col in ["open", "close"]):
            query = f"""
                SELECT COUNT(*) as extreme_movements
                FROM {table_name}
                WHERE ABS((close - open) / open) > 10
                LIMIT {sample_size}
            """

            result = await self.db_connection.execute_query(query)
            extreme_count = result[0]["extreme_movements"]

            if extreme_count > 0:
                anomaly_check["status"] = "warning"
                anomaly_check["anomalies"].append(
                    {"type": "extreme_price_movement", "count": extreme_count}
                )

        # Check for zero volume in trading data
        if "volume" in columns:
            query = f"""
                SELECT COUNT(*) as zero_volume
                FROM {table_name}
                WHERE volume = 0
                LIMIT {sample_size}
            """

            result = await self.db_connection.execute_query(query)
            zero_volume_count = result[0]["zero_volume"]

            if zero_volume_count > sample_size * 0.1:  # More than 10% zero volume
                anomaly_check["status"] = "warning"
                anomaly_check["anomalies"].append(
                    {
                        "type": "high_zero_volume",
                        "count": zero_volume_count,
                        "percentage": (zero_volume_count / sample_size) * 100,
                    }
                )

        return anomaly_check

    def _calculate_data_quality_score(self, validation_checks: Dict[str, Any]) -> float:
        """Calculate overall data quality score based on validation checks."""
        total_score = 0.0
        check_count = 0

        for check_name, check_result in validation_checks.items():
            check_count += 1

            if check_result.get("status") == "passed":
                total_score += 100.0
            elif check_result.get("status") == "warning":
                total_score += 70.0
            elif check_result.get("status") == "failed":
                total_score += 30.0

        return total_score / check_count if check_count > 0 else 0.0

    async def compare_data_sources(
        self,
        old_table: str,
        new_table: str,
        comparison_columns: List[str],
        sample_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compare data between old and new ingestion sources.

        Args:
            old_table: Name of the old table
            new_table: Name of the new table
            comparison_columns: Columns to compare
            sample_size: Number of records to compare

        Returns:
            Comparison results
        """
        logger.info(f"Comparing data sources: {old_table} vs {new_table}")

        comparison_result = {
            "old_table": old_table,
            "new_table": new_table,
            "comparison_columns": comparison_columns,
            "record_counts": {},
            "data_differences": [],
            "match_percentage": 0.0,
            "status": "passed",
        }

        try:
            # Get record counts
            old_count_query = f"SELECT COUNT(*) as count FROM {old_table}"
            new_count_query = f"SELECT COUNT(*) as count FROM {new_table}"

            old_count = await self.db_connection.execute_query(old_count_query)
            new_count = await self.db_connection.execute_query(new_count_query)

            comparison_result["record_counts"] = {
                "old_table": old_count[0]["count"],
                "new_table": new_count[0]["count"],
            }

            # Compare sample data
            if sample_size:
                comparison_result["data_differences"] = await self._compare_sample_data(
                    old_table, new_table, comparison_columns, sample_size
                )

                # Calculate match percentage
                total_comparisons = len(comparison_result["data_differences"])
                matches = sum(
                    1 for diff in comparison_result["data_differences"] if diff["match"]
                )
                comparison_result["match_percentage"] = (
                    (matches / total_comparisons) * 100
                    if total_comparisons > 0
                    else 100.0
                )

                if comparison_result["match_percentage"] < 95:
                    comparison_result["status"] = (
                        "warning"
                        if comparison_result["match_percentage"] > 85
                        else "failed"
                    )

        except Exception as e:
            logger.error(f"Error comparing data sources: {e}")
            comparison_result["status"] = "error"
            comparison_result["error"] = str(e)

        return comparison_result

    async def _compare_sample_data(
        self,
        old_table: str,
        new_table: str,
        comparison_columns: List[str],
        sample_size: int,
    ) -> List[Dict[str, Any]]:
        """Compare sample data between two tables."""
        differences = []

        # Get sample data from both tables
        columns_str = ", ".join(comparison_columns)

        old_query = f"SELECT {columns_str} FROM {old_table} ORDER BY timestamp DESC LIMIT {sample_size}"
        new_query = f"SELECT {columns_str} FROM {new_table} ORDER BY timestamp DESC LIMIT {sample_size}"

        old_data = await self.db_connection.execute_query(old_query)
        new_data = await self.db_connection.execute_query(new_query)

        # Convert to dictionaries for easier comparison
        old_dict = {
            self._create_record_key(row, comparison_columns): row for row in old_data
        }
        new_dict = {
            self._create_record_key(row, comparison_columns): row for row in new_data
        }

        # Compare records
        all_keys = set(old_dict.keys()) | set(new_dict.keys())

        for key in all_keys:
            old_record = old_dict.get(key)
            new_record = new_dict.get(key)

            if old_record and new_record:
                # Both records exist, compare values
                match = self._compare_records(
                    old_record, new_record, comparison_columns
                )
                differences.append(
                    {
                        "key": key,
                        "match": match,
                        "old_record": old_record if not match else None,
                        "new_record": new_record if not match else None,
                    }
                )
            elif old_record:
                # Record only in old table
                differences.append(
                    {
                        "key": key,
                        "match": False,
                        "missing_in": "new_table",
                        "record": old_record,
                    }
                )
            else:
                # Record only in new table
                differences.append(
                    {
                        "key": key,
                        "match": False,
                        "missing_in": "old_table",
                        "record": new_record,
                    }
                )

        return differences

    def _create_record_key(self, record: Dict[str, Any], key_columns: List[str]) -> str:
        """Create a unique key for a record based on specified columns."""
        key_parts = []
        for col in key_columns:
            if col in record:
                value = record[col]
                if isinstance(value, datetime):
                    value = value.isoformat()
                key_parts.append(str(value))
        return "|".join(key_parts)

    def _compare_records(
        self, old_record: Dict[str, Any], new_record: Dict[str, Any], columns: List[str]
    ) -> bool:
        """Compare two records for equality."""
        for col in columns:
            old_val = old_record.get(col)
            new_val = new_record.get(col)

            # Handle floating point comparison with tolerance
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                if (
                    abs(old_val - new_val) > 0.0001
                ):  # Small tolerance for floating point
                    return False
            elif old_val != new_val:
                return False

        return True

    async def generate_validation_report(
        self,
        tables_to_validate: List[str],
        sample_size: Optional[int] = None,
        output_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.

        Args:
            tables_to_validate: List of table names to validate
            sample_size: Sample size for validation (None for full validation)
            output_format: Output format ('json' or 'html')

        Returns:
            Complete validation report
        """
        logger.info(
            f"Generating validation report for {len(tables_to_validate)} tables"
        )

        # Initialize report
        report = {
            "validation_summary": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tables_validated": len(tables_to_validate),
                "sample_size": sample_size or "full",
                "overall_status": "passed",
                "total_issues": 0,
            },
            "table_validations": {},
            "recommendations": [],
        }

        # Validate each table
        for table_name in tables_to_validate:
            try:
                validation_result = await self.validate_table_integrity(
                    table_name, sample_size
                )
                report["table_validations"][table_name] = validation_result

                # Count issues from validation_checks
                for check_name, check_result in validation_result[
                    "validation_checks"
                ].items():
                    if check_result.get("status") in ["warning", "failed"]:
                        report["validation_summary"]["total_issues"] += 1

                        if check_result.get("status") == "failed":
                            report["validation_summary"]["overall_status"] = "failed"
                        elif (
                            report["validation_summary"]["overall_status"] == "passed"
                            and check_result.get("status") == "warning"
                        ):
                            report["validation_summary"]["overall_status"] = "warning"

                # Count issues from issues_found array
                issues_found = validation_result.get("issues_found", [])
                if issues_found:
                    report["validation_summary"]["total_issues"] += len(issues_found)
                    # Any issue in issues_found should be treated as failed
                    for issue in issues_found:
                        if issue.get("severity") == "high":
                            report["validation_summary"]["overall_status"] = "failed"
                        elif report["validation_summary"][
                            "overall_status"
                        ] == "passed" and issue.get("severity") in [
                            "medium",
                            "warning",
                        ]:
                            report["validation_summary"]["overall_status"] = "warning"

            except Exception as e:
                logger.error(f"Error validating table {table_name}: {e}")
                report["table_validations"][table_name] = {
                    "error": str(e),
                    "status": "error",
                }
                report["validation_summary"]["overall_status"] = "failed"

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(
            report["table_validations"]
        )

        logger.info(
            f"Validation report generated. Overall status: {report['validation_summary']['overall_status']}"
        )
        return report

    def _generate_recommendations(self, table_validations: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        has_issues = False

        for table_name, validation in table_validations.items():
            # Check for critical errors in issues_found
            issues_found = validation.get("issues_found", [])
            if issues_found:
                has_issues = True
                for issue in issues_found:
                    if issue.get("type") == "validation_error":
                        recommendations.append(
                            f"Table {table_name}: CRITICAL ERROR - {issue.get('message', 'Unknown error')}"
                        )
                    else:
                        recommendations.append(
                            f"Table {table_name}: {issue.get('type', 'Issue')}: {issue.get('message', 'Unknown issue')}"
                        )

            # Check for errors in validation status
            if validation.get("status") == "error":
                has_issues = True
                recommendations.append(
                    f"Table {table_name}: VALIDATION FAILED - {validation.get('error', 'Unknown error')}"
                )

            # Check validation_checks if they exist
            if "validation_checks" in validation:
                checks = validation["validation_checks"]

                # Null value recommendations
                if checks.get("null_value_check", {}).get("status") == "failed":
                    has_issues = True
                    recommendations.append(
                        f"Table {table_name}: Implement data validation to prevent null values in critical columns"
                    )

                # Duplicate recommendations
                if checks.get("duplicate_check", {}).get("status") in [
                    "warning",
                    "failed",
                ]:
                    has_issues = True
                    recommendations.append(
                        f"Table {table_name}: Review data ingestion process to prevent duplicate records"
                    )

                # Freshness recommendations
                if checks.get("freshness_check", {}).get("status") in [
                    "warning",
                    "failed",
                ]:
                    has_issues = True
                    recommendations.append(
                        f"Table {table_name}: Check data ingestion schedule and API connectivity"
                    )

                # Consistency recommendations
                if checks.get("consistency_check", {}).get("status") in [
                    "warning",
                    "failed",
                ]:
                    has_issues = True
                    recommendations.append(
                        f"Table {table_name}: Implement data validation rules for price/volume consistency"
                    )

        if not has_issues:
            recommendations.append("All validations passed. Data quality is excellent!")

        return recommendations

    async def save_report(self, report: Dict[str, Any], output_path: str):
        """Save validation report to file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_path.endswith(".json"):
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        else:
            # Save as text summary
            with open(output_path, "w") as f:
                f.write("DATA MIGRATION VALIDATION REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {report['validation_summary']['timestamp']}\n")
                f.write(
                    f"Overall Status: {report['validation_summary']['overall_status'].upper()}\n"
                )
                f.write(
                    f"Tables Validated: {report['validation_summary']['tables_validated']}\n"
                )
                f.write(
                    f"Total Issues: {report['validation_summary']['total_issues']}\n\n"
                )

                f.write("RECOMMENDATIONS:\n")
                f.write("-" * 20 + "\n")
                for rec in report["recommendations"]:
                    f.write(f"• {rec}\n")

        logger.info(f"Validation report saved to: {output_path}")

    async def cleanup(self):
        """Clean up resources."""
        if self.db_connection:
            self.db_connection.close_connection()
            logger.info("Database connection closed")


async def main():
    """Main function for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate data migration from old to new ingestion systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick validation of key tables
  python validate_migration.py --quick --tables ohlcv_spot_1d_raw futures_ohlcv_1d_raw

  # Thorough validation with custom sample size
  python validate_migration.py --sample-size 10000 --output validation_report.json

  # Compare old vs new data sources
  python validate_migration.py --compare --old-table old_ohlcv --new-table ohlcv_spot_1d_raw

  # Full validation of all tables
  python validate_migration.py --full-validation --output-dir ./validation_reports/
        """,
    )

    parser.add_argument("--tables", nargs="+", help="Specific tables to validate")

    parser.add_argument(
        "--sample-size",
        type=int,
        help="Number of records to sample for validation (default: all records)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick validation with smaller sample size (1000 records)",
    )

    parser.add_argument(
        "--full-validation",
        action="store_true",
        help="Validate all tables in the database",
    )

    parser.add_argument(
        "--compare", action="store_true", help="Compare data between old and new tables"
    )

    parser.add_argument("--old-table", help="Old table name for comparison")

    parser.add_argument("--new-table", help="New table name for comparison")

    parser.add_argument(
        "--output",
        default="validation_report.json",
        help="Output file path for validation report",
    )

    parser.add_argument("--output-dir", help="Output directory for multiple reports")

    parser.add_argument(
        "--date-range-days",
        type=int,
        default=7,
        help="Number of days to look back for validation (default: 7)",
    )

    args = parser.parse_args()

    # Initialize validator
    validator = MigrationValidator()
    await validator.initialize()

    try:
        if args.compare and args.old_table and args.new_table:
            # Compare two specific tables
            comparison_columns = [
                "timestamp",
                "symbol",
                "market",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
            result = await validator.compare_data_sources(
                args.old_table, args.new_table, comparison_columns, args.sample_size
            )

            print(f"Comparison Results:")
            print(f"Match Percentage: {result['match_percentage']:.2f}%")
            print(f"Status: {result['status']}")

            # Save comparison report
            output_path = (
                args.output or f"comparison_{args.old_table}_vs_{args.new_table}.json"
            )
            await validator.save_report({"comparison": result}, output_path)

        else:
            # Determine tables to validate
            if args.full_validation:
                # Get all tables from database
                tables_query = "SHOW TABLES"
                tables_result = await validator.db_connection.execute_query(
                    tables_query
                )
                tables_to_validate = [list(row.values())[0] for row in tables_result]
            elif args.tables:
                tables_to_validate = args.tables
            else:
                # Default tables for validation
                tables_to_validate = [
                    "ohlcv_spot_1d_raw",
                    "futures_ohlcv_1d_raw",
                    "futures_funding_rate_1d_raw",
                    "futures_open_interest_1d_raw",
                    "indices_ohlcv_1d_raw",
                    "asset_metadata",
                    "exchange_metadata",
                ]

            # Determine sample size
            sample_size = args.sample_size
            if args.quick:
                sample_size = 1000

            # Generate validation report
            report = await validator.generate_validation_report(
                tables_to_validate, sample_size
            )

            # Save report
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = (
                    output_dir
                    / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            else:
                output_path = args.output

            await validator.save_report(report, str(output_path))

            # Print summary
            print(f"\nValidation Summary:")
            print(
                f"Overall Status: {report['validation_summary']['overall_status'].upper()}"
            )
            print(
                f"Tables Validated: {report['validation_summary']['tables_validated']}"
            )
            print(f"Total Issues Found: {report['validation_summary']['total_issues']}")
            print(f"Report saved to: {output_path}")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    finally:
        await validator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
