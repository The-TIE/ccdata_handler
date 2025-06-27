"""
Unified Data Ingestion Pipeline

This package provides a modular, efficient, and maintainable framework for
data ingestion with clear separation of concerns, robust error handling,
and asynchronous processing capabilities.

The package includes:
- Base ingestion framework with abstract classes
- Specialized ingestors for time-series and metadata
- Shared utilities for common operations
- Centralized configuration management
- Performance monitoring and metrics collection

Example usage:
    from src.ingestion import TimeSeriesIngestor, get_config
    from src.ingestion.utils import performance_monitor

    config = get_config()
    ingestor = TimeSeriesIngestor(api_client, db_client, config, '1d')
    result = await ingestor.ingest_with_backfill(market='binance', instrument='BTCUSDT')
"""

# Core framework components
from .base import BaseIngestor, TimeSeriesIngestor, MetadataIngestor

# Configuration management
from .config import (
    IngestionConfigManager,
    DatabaseConfig,
    ApiConfig,
    IngestionConfig,
    LoggingConfig,
    MonitoringConfig,
    get_config,
    get_database_config,
    get_api_config,
    get_ingestion_config,
    get_logging_config,
    get_monitoring_config,
    reset_config,
)

# Shared utilities
from .utils import (
    DateTimeHandler,
    DataTransformer,
    BatchProcessor,
    performance_monitor,
    IngestionMetrics,
    ingestion_metrics,
)

# Legacy import for backwards compatibility
from .futures_ingestor import FuturesIngestor


__version__ = "1.0.0"
__author__ = "Brian Blandin"

__all__ = [
    # Core framework
    "BaseIngestor",
    "TimeSeriesIngestor",
    "MetadataIngestor",
    # Configuration
    "IngestionConfigManager",
    "DatabaseConfig",
    "ApiConfig",
    "IngestionConfig",
    "LoggingConfig",
    "MonitoringConfig",
    "get_config",
    "get_database_config",
    "get_api_config",
    "get_ingestion_config",
    "get_logging_config",
    "get_monitoring_config",
    "reset_config",
    # Utilities
    "DateTimeHandler",
    "DataTransformer",
    "BatchProcessor",
    "performance_monitor",
    "IngestionMetrics",
    "ingestion_metrics",
    # Legacy
    "FuturesIngestor",
]


def get_version() -> str:
    """Get the current version of the ingestion framework."""
    return __version__


def get_framework_info() -> dict:
    """
    Get information about the ingestion framework.

    Returns:
        Dictionary containing framework information
    """
    return {
        "name": "Unified Data Ingestion Pipeline",
        "version": __version__,
        "author": __author__,
        "components": {
            "base_ingestors": [
                "BaseIngestor",
                "TimeSeriesIngestor",
                "MetadataIngestor",
            ],
            "configuration": ["IngestionConfigManager", "DatabaseConfig", "ApiConfig"],
            "utilities": ["DateTimeHandler", "DataTransformer", "BatchProcessor"],
            "monitoring": ["IngestionMetrics", "performance_monitor"],
            "legacy": ["FuturesIngestor"],
        },
        "features": [
            "Asynchronous processing support",
            "Centralized configuration management",
            "Performance monitoring and metrics",
            "Robust error handling and retry logic",
            "Time-series data backfilling",
            "Metadata change detection",
            "Batch processing optimization",
            "Database-level deduplication",
        ],
    }
