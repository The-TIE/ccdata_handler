"""
Migration helper script for converting existing ingestion scripts to the unified framework.

This script provides tools and templates to help migrate existing ingestion scripts
to use the new unified ingestion architecture, reducing code complexity and improving
maintainability.
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Template for new ingestion script using the unified framework
UNIFIED_SCRIPT_TEMPLATE = '''"""
{description}

This script has been migrated to use the unified ingestion framework.
Generated on {timestamp} by migrate_ingestion_script.py
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.data_api.{api_client_module} import {api_client_class}
from src.db.connection import DbConnectionManager
from src.ingestion.ingestors.{ingestor_module} import {ingestor_class}
from src.ingestion.config import get_config
from src.logger_config import setup_logger
from src.rate_limit_tracker import record_rate_limit_status

# Load environment variables
load_dotenv()

# Configure logging
script_name = os.path.splitext(os.path.basename(__file__))[0]
log_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    f"{{script_name}}.log",
)
logger = setup_logger(__name__, log_to_console=True, log_file_path=log_file_path)


async def {function_name}():
    """
    Orchestrate {data_type} ingestion using the unified framework.
    """
    logger.info("Starting {data_type} ingestion process (Unified Framework)")
    record_rate_limit_status("{function_name}", "pre")

    # Get API key from environment
    api_key = os.getenv("CCDATA_API_KEY")
    if not api_key:
        logger.error("CCDATA_API_KEY environment variable not set. Exiting.")
        return

    # Initialize components
    config = get_config()
    api_client = None
    db_client = None
    ingestor = None

    try:
        # Initialize API client
        api_client = {api_client_class}(api_key=api_key)
        logger.info("{api_client_class} initialized")

        # Initialize database client
        db_client = DbConnectionManager()
        logger.info("Database client initialized")

        # Initialize the ingestor
        ingestor = {ingestor_class}(
            api_client=api_client,
            db_client=db_client,
            config=config{ingestor_params}
        )
        logger.info("{ingestor_class} initialized")

        # Perform the ingestion
        result = await ingestor.{ingest_method}({method_params})

        # Log results
        logger.info("{data_type} ingestion completed")
        logger.info(f"Ingestion status: {{result['status']}}")
        logger.info(f"Records processed: {{result['records_processed']}}")
        logger.info(f"Records inserted: {{result['records_inserted']}}")
        logger.info(f"Duration: {{result['duration_seconds']:.2f}} seconds")

        if result['status'] != 'success':
            logger.warning(f"Ingestion completed with issues: {{result.get('error', 'Unknown error')}}")

    except Exception as e:
        logger.exception(f"An error occurred during {data_type} ingestion: {{e}}")
        record_rate_limit_status("{function_name}", "failure")
        return

    finally:
        # Clean up resources
        if db_client:
            db_client.close_connection()
            logger.info("Database connection closed")

    record_rate_limit_status("{function_name}", "post")
    logger.info("{data_type} ingestion process finished")


def main():
    """Main entry point for the script."""
    try:
        logger.info("Attempting to ingest {data_type} using unified framework...")
        asyncio.run({function_name}())
    except KeyboardInterrupt:
        logger.info("Ingestion interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error in main: {{e}}")


if __name__ == "__main__":
    main()
'''


class IngestionScriptMigrator:
    """
    Helper class for migrating existing ingestion scripts to the unified framework.
    """

    def __init__(self):
        """Initialize the migrator with predefined mappings."""
        self.script_mappings = {
            "ingest_asset_data.py": {
                "data_type": "asset metadata",
                "api_client_module": "asset_api_client",
                "api_client_class": "CcdataAssetApiClient",
                "ingestor_module": "asset_metadata_ingestor",
                "ingestor_class": "AssetMetadataIngestor",
                "ingest_method": "ingest_assets",
                "method_params": "page_size=100",
                "ingestor_params": "",
            },
            "ingest_exchanges_general.py": {
                "data_type": "exchange metadata",
                "api_client_module": "utilities_api_client",
                "api_client_class": "CcdataUtilitiesApiClient",
                "ingestor_module": "exchange_metadata_ingestor",
                "ingestor_class": "ExchangeMetadataIngestor",
                "ingest_method": "ingest_exchanges",
                "method_params": "",
                "ingestor_params": "",
            },
            "ingest_daily_ohlcv_spot_data.py": {
                "data_type": "spot OHLCV",
                "api_client_module": "spot_api_client",
                "api_client_class": "CcdataSpotApiClient",
                "ingestor_module": "spot_ohlcv_ingestor",
                "ingestor_class": "SpotOHLCVIngestor",
                "ingest_method": "ingest_multiple_pairs",
                "method_params": "trading_pairs=get_trading_pairs()",
                "ingestor_params": ',\n            interval="1d"',
            },
        }

    def analyze_script(self, script_path: Path) -> Dict[str, any]:
        """
        Analyze an existing ingestion script to extract key information.

        Args:
            script_path: Path to the script to analyze

        Returns:
            Dictionary containing analysis results
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")

        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        analysis = {
            "file_name": script_path.name,
            "line_count": len(content.splitlines()),
            "has_api_client": bool(re.search(r"from src\..*api.*import", content)),
            "has_db_client": bool(re.search(r"DbConnectionManager", content)),
            "has_transform_function": bool(re.search(r"def transform_.*\(", content)),
            "has_insert_function": bool(re.search(r"def insert_.*\(", content)),
            "api_calls": len(re.findall(r"\.get_.*\(", content)),
            "database_tables": len(re.findall(r'insert_dataframe.*"([^"]+)"', content)),
            "complexity_score": self._calculate_complexity_score(content),
        }

        return analysis

    def _calculate_complexity_score(self, content: str) -> int:
        """
        Calculate a complexity score for the script.

        Args:
            content: Script content

        Returns:
            Complexity score (higher = more complex)
        """
        score = 0
        score += len(re.findall(r"def ", content)) * 2  # Functions
        score += len(re.findall(r"for ", content))  # Loops
        score += len(re.findall(r"if ", content))  # Conditionals
        score += len(re.findall(r"try:", content)) * 2  # Exception handling
        score += len(re.findall(r"\.insert_dataframe", content)) * 3  # DB operations
        return score

    def generate_migration_plan(self, script_path: Path) -> Dict[str, any]:
        """
        Generate a migration plan for a script.

        Args:
            script_path: Path to the script to migrate

        Returns:
            Dictionary containing the migration plan
        """
        analysis = self.analyze_script(script_path)
        script_name = script_path.name

        if script_name in self.script_mappings:
            mapping = self.script_mappings[script_name]
            estimated_reduction = max(
                60, min(80, 100 - (analysis["complexity_score"] * 2))
            )
        else:
            mapping = self._infer_mapping(script_path)
            estimated_reduction = 50  # Conservative estimate for unknown scripts

        plan = {
            "original_analysis": analysis,
            "mapping": mapping,
            "estimated_line_reduction": f"{estimated_reduction}%",
            "migration_steps": [
                "1. Create new script using unified framework template",
                "2. Configure appropriate ingestor class",
                "3. Replace manual API pagination with ingestor methods",
                "4. Remove manual data transformation functions",
                "5. Remove manual database insertion logic",
                "6. Test the new script with small dataset",
                "7. Compare results with original script",
                "8. Update scheduling/automation to use new script",
            ],
            "benefits": [
                f"Reduce code by ~{estimated_reduction}%",
                "Automatic error handling and retry logic",
                "Built-in rate limiting and monitoring",
                "Consistent logging and configuration",
                "Better performance with async operations",
                "Easier maintenance and testing",
            ],
        }

        return plan

    def _infer_mapping(self, script_path: Path) -> Dict[str, str]:
        """
        Infer mapping for unknown scripts based on content analysis.

        Args:
            script_path: Path to the script

        Returns:
            Inferred mapping dictionary
        """
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to infer the type of data being ingested
        if "asset" in content.lower():
            base_mapping = self.script_mappings["ingest_asset_data.py"]
        elif "exchange" in content.lower():
            base_mapping = self.script_mappings["ingest_exchanges_general.py"]
        elif "ohlcv" in content.lower() or "spot" in content.lower():
            base_mapping = self.script_mappings["ingest_daily_ohlcv_spot_data.py"]
        else:
            # Generic mapping
            base_mapping = {
                "data_type": "unknown data",
                "api_client_module": "unknown_api_client",
                "api_client_class": "UnknownApiClient",
                "ingestor_module": "unknown_ingestor",
                "ingestor_class": "UnknownIngestor",
                "ingest_method": "ingest",
                "method_params": "",
                "ingestor_params": "",
            }

        return base_mapping

    def migrate_script(
        self,
        script_path: Path,
        output_path: Optional[Path] = None,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """
        Migrate a script to use the unified framework.

        Args:
            script_path: Path to the original script
            output_path: Path for the new script (defaults to original_v2.py)
            dry_run: If True, don't write the file, just return the content

        Returns:
            Tuple of (success, message/content)
        """
        try:
            plan = self.generate_migration_plan(script_path)
            mapping = plan["mapping"]

            if output_path is None:
                output_path = script_path.parent / f"{script_path.stem}_v2.py"

            # Generate the new script content
            function_name = f"ingest_{mapping['data_type'].replace(' ', '_')}_v2"

            new_content = UNIFIED_SCRIPT_TEMPLATE.format(
                description=f"{mapping['data_type'].title()} ingestion using unified framework",
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                api_client_module=mapping["api_client_module"],
                api_client_class=mapping["api_client_class"],
                ingestor_module=mapping["ingestor_module"],
                ingestor_class=mapping["ingestor_class"],
                function_name=function_name,
                data_type=mapping["data_type"],
                ingest_method=mapping["ingest_method"],
                method_params=mapping["method_params"],
                ingestor_params=mapping["ingestor_params"],
            )

            if dry_run:
                return True, new_content

            # Write the new script
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True, f"Successfully migrated script to {output_path}"

        except Exception as e:
            return False, f"Migration failed: {e}"

    def generate_migration_report(self, scripts_dir: Path) -> str:
        """
        Generate a comprehensive migration report for all scripts in a directory.

        Args:
            scripts_dir: Directory containing ingestion scripts

        Returns:
            Formatted migration report
        """
        if not scripts_dir.exists():
            return f"Directory not found: {scripts_dir}"

        script_files = list(scripts_dir.glob("ingest_*.py"))
        if not script_files:
            return f"No ingestion scripts found in {scripts_dir}"

        report_lines = [
            "INGESTION SCRIPT MIGRATION REPORT",
            "=" * 50,
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Scripts directory: {scripts_dir}",
            f"Scripts found: {len(script_files)}",
            "",
        ]

        total_lines = 0
        total_estimated_reduction = 0

        for script_file in script_files:
            try:
                plan = self.generate_migration_plan(script_file)
                analysis = plan["original_analysis"]

                report_lines.extend(
                    [
                        f"SCRIPT: {script_file.name}",
                        "-" * 30,
                        f"Current lines of code: {analysis['line_count']}",
                        f"Complexity score: {analysis['complexity_score']}",
                        f"API calls: {analysis['api_calls']}",
                        f"Database tables: {analysis['database_tables']}",
                        f"Estimated reduction: {plan['estimated_line_reduction']}",
                        "",
                        "Migration benefits:",
                    ]
                )

                for benefit in plan["benefits"]:
                    report_lines.append(f"  • {benefit}")

                report_lines.extend(["", "Migration steps:"])
                for step in plan["migration_steps"]:
                    report_lines.append(f"  {step}")

                report_lines.extend(["", "=" * 50, ""])

                total_lines += analysis["line_count"]
                reduction_pct = int(plan["estimated_line_reduction"].rstrip("%"))
                total_estimated_reduction += reduction_pct

            except Exception as e:
                report_lines.extend(
                    [
                        f"SCRIPT: {script_file.name}",
                        f"ERROR: {e}",
                        "",
                    ]
                )

        # Summary
        if script_files:
            avg_reduction = total_estimated_reduction / len(script_files)
            report_lines.extend(
                [
                    "SUMMARY",
                    "=" * 20,
                    f"Total scripts: {len(script_files)}",
                    f"Total lines of code: {total_lines}",
                    f"Average estimated reduction: {avg_reduction:.1f}%",
                    f"Estimated lines saved: {int(total_lines * avg_reduction / 100)}",
                    "",
                    "Next steps:",
                    "1. Review this report and migration plans",
                    "2. Start with the simplest scripts first",
                    "3. Test each migrated script thoroughly",
                    "4. Update scheduling and automation",
                    "5. Archive original scripts after successful migration",
                ]
            )

        return "\n".join(report_lines)


def main():
    """Main entry point for the migration helper script."""
    parser = argparse.ArgumentParser(
        description="Migration helper for ingestion scripts"
    )
    parser.add_argument(
        "action", choices=["analyze", "migrate", "report"], help="Action to perform"
    )
    parser.add_argument(
        "--script", type=Path, help="Path to script to analyze or migrate"
    )
    parser.add_argument("--output", type=Path, help="Output path for migrated script")
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=Path("scripts"),
        help="Directory containing ingestion scripts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    args = parser.parse_args()
    migrator = IngestionScriptMigrator()

    if args.action == "analyze":
        if not args.script:
            print("--script is required for analyze action")
            return

        try:
            analysis = migrator.analyze_script(args.script)
            print(f"Analysis for {args.script}:")
            for key, value in analysis.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error analyzing script: {e}")

    elif args.action == "migrate":
        if not args.script:
            print("--script is required for migrate action")
            return

        try:
            success, result = migrator.migrate_script(
                args.script, args.output, args.dry_run
            )
            if success:
                if args.dry_run:
                    print("Generated script content:")
                    print("-" * 50)
                    print(result)
                else:
                    print(result)
            else:
                print(f"Migration failed: {result}")
        except Exception as e:
            print(f"Error migrating script: {e}")

    elif args.action == "report":
        try:
            report = migrator.generate_migration_report(args.scripts_dir)
            print(report)
        except Exception as e:
            print(f"Error generating report: {e}")


if __name__ == "__main__":
    main()
