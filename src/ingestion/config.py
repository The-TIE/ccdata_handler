"""
Configuration management system for the unified data ingestion pipeline.

This module provides centralized configuration management with support for
environment-specific settings, validation, and type checking. It follows
the architecture design for consistent configuration across all ingestors.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

from dotenv import load_dotenv, find_dotenv
from ..logger_config import setup_logger


logger = setup_logger(__name__)


@dataclass
class DatabaseConfig:
    """Configuration for database connections."""

    host: str = ""
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class ApiConfig:
    """Configuration for API clients."""

    ccdata_api_key: str = ""
    min_api_base_url: str = "https://min-api.cryptocompare.com/data"
    data_api_base_url: str = "https://data-api.cryptocompare.com"
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_calls_per_second: float = 10.0
    rate_limit_calls_per_minute: int = 300
    rate_limit_calls_per_hour: int = 10000


@dataclass
class IngestionConfig:
    """Configuration for ingestion processes."""

    batch_size: int = 1000
    max_api_limit: int = 5000
    api_call_delay: float = 0.1
    backfill_enabled: bool = True
    max_backfill_days: int = 365
    metadata_full_refresh: bool = False
    metadata_change_detection: bool = True
    parallel_workers: int = 4
    chunk_size: int = 10000

    # Time series specific settings
    default_intervals: List[str] = field(default_factory=lambda: ["1d", "1h", "1m"])
    max_limit_per_call: Dict[str, int] = field(
        default_factory=lambda: {"1d": 5000, "1h": 2000, "1m": 2000}
    )

    # Futures specific settings
    futures_exchanges: List[str] = field(default_factory=list)
    futures_instrument_statuses: List[str] = field(
        default_factory=lambda: ["ACTIVE", "EXPIRED"]
    )

    # Error handling
    max_consecutive_failures: int = 5
    failure_backoff_multiplier: float = 2.0
    max_failure_backoff: int = 300


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/ingestion.log"
    file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    file_backup_count: int = 5
    console_enabled: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching."""

    enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    default_ttl: int = 3600  # seconds
    max_connections: int = 10


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and metrics."""

    metrics_enabled: bool = True
    performance_monitoring: bool = True
    alert_on_failure: bool = True
    alert_on_consecutive_failures: int = 3
    health_check_interval: int = 300  # seconds
    metrics_retention_days: int = 30


class IngestionConfigManager:
    """
    Centralized configuration manager for the ingestion pipeline.

    Provides a single source for all application configuration settings,
    with support for environment-specific overrides and validation.
    """

    def __init__(self, env: str = "development"):
        """
        Initialize the configuration manager.

        Args:
            env: Environment name (development, staging, production)
        """
        self.env = env
        self.environment = env  # Add environment attribute for compatibility
        self._load_environment_variables()

        # Initialize configuration sections
        self.database = self._load_database_config()
        self.api = self._load_api_config()
        self.ingestion = self._load_ingestion_config()
        self.logging = self._load_logging_config()
        self.monitoring = self._load_monitoring_config()
        self.cache = self._load_cache_config()

        # Validate configuration
        self._validate_config()

        logger.info(f"Configuration loaded for environment: {self.env}")

    def _load_environment_variables(self):
        """Load environment variables from .env files."""
        # Load base .env file
        base_env_path = find_dotenv()
        if base_env_path:
            load_dotenv(base_env_path, override=False)
            logger.debug(f"Loaded base environment from: {base_env_path}")

        # Load environment-specific .env file
        env_specific_path = Path(f".env.{self.env}")
        if env_specific_path.exists():
            load_dotenv(env_specific_path, override=True)
            logger.debug(
                f"Loaded environment-specific config from: {env_specific_path}"
            )

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables."""
        return DatabaseConfig(
            host=os.getenv("S2_HOST", "localhost"),
            port=int(os.getenv("S2_PORT", "3306")),
            user=os.getenv("S2_USER", ""),
            password=os.getenv("S2_PASSWORD", ""),
            database=os.getenv("S2_DATABASE", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
        )

    def _load_api_config(self) -> ApiConfig:
        """Load API configuration from environment variables."""
        return ApiConfig(
            ccdata_api_key=os.getenv("CCDATA_API_KEY", ""),
            min_api_base_url=os.getenv(
                "MIN_API_BASE_URL", "https://min-api.cryptocompare.com/data"
            ),
            data_api_base_url=os.getenv(
                "DATA_API_BASE_URL", "https://data-api.cryptocompare.com"
            ),
            request_timeout=int(os.getenv("API_REQUEST_TIMEOUT", "30")),
            max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("API_RETRY_DELAY", "1.0")),
            rate_limit_calls_per_second=float(
                os.getenv("API_RATE_LIMIT_PER_SECOND", "10.0")
            ),
            rate_limit_calls_per_minute=int(
                os.getenv("API_RATE_LIMIT_PER_MINUTE", "300")
            ),
            rate_limit_calls_per_hour=int(
                os.getenv("API_RATE_LIMIT_PER_HOUR", "10000")
            ),
        )

    def _load_ingestion_config(self) -> IngestionConfig:
        """Load ingestion configuration from environment variables."""
        # Parse futures exchanges from comma-separated string
        futures_exchanges_str = os.getenv("FUTURES_EXCHANGES", "")
        futures_exchanges = [
            ex.strip() for ex in futures_exchanges_str.split(",") if ex.strip()
        ]

        # Parse futures instrument statuses
        statuses_str = os.getenv("FUTURES_INSTRUMENT_STATUSES", "ACTIVE,EXPIRED")
        instrument_statuses = [
            status.strip() for status in statuses_str.split(",") if status.strip()
        ]

        return IngestionConfig(
            batch_size=int(os.getenv("INGESTION_BATCH_SIZE", "1000")),
            max_api_limit=int(os.getenv("INGESTION_MAX_API_LIMIT", "5000")),
            api_call_delay=float(os.getenv("INGESTION_API_CALL_DELAY", "0.1")),
            backfill_enabled=os.getenv("INGESTION_BACKFILL_ENABLED", "true").lower()
            == "true",
            max_backfill_days=int(os.getenv("INGESTION_MAX_BACKFILL_DAYS", "365")),
            metadata_full_refresh=os.getenv("METADATA_FULL_REFRESH", "false").lower()
            == "true",
            metadata_change_detection=os.getenv(
                "METADATA_CHANGE_DETECTION", "true"
            ).lower()
            == "true",
            parallel_workers=int(os.getenv("INGESTION_PARALLEL_WORKERS", "4")),
            chunk_size=int(os.getenv("INGESTION_CHUNK_SIZE", "10000")),
            futures_exchanges=futures_exchanges,
            futures_instrument_statuses=instrument_statuses,
            max_consecutive_failures=int(
                os.getenv("INGESTION_MAX_CONSECUTIVE_FAILURES", "5")
            ),
            failure_backoff_multiplier=float(
                os.getenv("INGESTION_FAILURE_BACKOFF_MULTIPLIER", "2.0")
            ),
            max_failure_backoff=int(os.getenv("INGESTION_MAX_FAILURE_BACKOFF", "300")),
        )

    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration from environment variables."""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv(
                "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            file_path=os.getenv("LOG_FILE_PATH", "logs/ingestion.log"),
            file_max_bytes=int(os.getenv("LOG_FILE_MAX_BYTES", str(10 * 1024 * 1024))),
            file_backup_count=int(os.getenv("LOG_FILE_BACKUP_COUNT", "5")),
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
        )

    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration from environment variables."""
        return CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
        )

    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration from environment variables."""
        return MonitoringConfig(
            metrics_enabled=os.getenv("MONITORING_METRICS_ENABLED", "true").lower()
            == "true",
            performance_monitoring=os.getenv(
                "MONITORING_PERFORMANCE_ENABLED", "true"
            ).lower()
            == "true",
            alert_on_failure=os.getenv("MONITORING_ALERT_ON_FAILURE", "true").lower()
            == "true",
            alert_on_consecutive_failures=int(
                os.getenv("MONITORING_ALERT_CONSECUTIVE_FAILURES", "3")
            ),
            health_check_interval=int(
                os.getenv("MONITORING_HEALTH_CHECK_INTERVAL", "300")
            ),
            metrics_retention_days=int(
                os.getenv("MONITORING_METRICS_RETENTION_DAYS", "30")
            ),
        )

    def _validate_config(self):
        """Validate the loaded configuration."""
        errors = []

        # Validate database configuration
        if not all(
            [
                self.database.host,
                self.database.user,
                self.database.password,
                self.database.database,
            ]
        ):
            errors.append(
                "Database configuration incomplete: host, user, password, and database are required"
            )

        # Validate API configuration
        if not self.api.ccdata_api_key:
            logger.warning("CCDATA_API_KEY not set - some API calls may fail")

        # Validate ingestion configuration
        if self.ingestion.batch_size <= 0:
            errors.append("Ingestion batch_size must be positive")

        if self.ingestion.max_api_limit <= 0:
            errors.append("Ingestion max_api_limit must be positive")

        if self.ingestion.parallel_workers <= 0:
            errors.append("Ingestion parallel_workers must be positive")

        # Validate logging configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            errors.append(
                f"Invalid log level: {self.logging.level}. Must be one of {valid_log_levels}"
            )

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            raise ValueError(error_msg)

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current environment configuration.

        Returns:
            Dictionary containing environment information
        """
        return {
            "environment": self.env,
            "database_host": self.database.host,
            "database_name": self.database.database,
            "api_base_urls": {
                "min_api": self.api.min_api_base_url,
                "data_api": self.api.data_api_base_url,
            },
            "ingestion_settings": {
                "batch_size": self.ingestion.batch_size,
                "backfill_enabled": self.ingestion.backfill_enabled,
                "parallel_workers": self.ingestion.parallel_workers,
            },
            "logging_level": self.logging.level,
            "monitoring_enabled": self.monitoring.metrics_enabled,
        }

    def update_config(self, section: str, **kwargs):
        """
        Update configuration values at runtime.

        Args:
            section: Configuration section to update ('database', 'api', 'ingestion', etc.)
            **kwargs: Configuration values to update
        """
        if section == "database":
            for key, value in kwargs.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        elif section == "api":
            for key, value in kwargs.items():
                if hasattr(self.api, key):
                    setattr(self.api, key, value)
        elif section == "ingestion":
            for key, value in kwargs.items():
                if hasattr(self.ingestion, key):
                    setattr(self.ingestion, key, value)
        elif section == "logging":
            for key, value in kwargs.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        elif section == "monitoring":
            for key, value in kwargs.items():
                if hasattr(self.monitoring, key):
                    setattr(self.monitoring, key, value)
        else:
            raise ValueError(f"Unknown configuration section: {section}")

        logger.info(f"Updated {section} configuration: {kwargs}")


# Global configuration instance
# This will be initialized when the module is imported
_config_manager: Optional[IngestionConfigManager] = None


def get_config(env: Optional[str] = None) -> IngestionConfigManager:
    """
    Get the global configuration manager instance.

    Args:
        env: Environment name (only used for first initialization)

    Returns:
        Global IngestionConfigManager instance
    """
    global _config_manager

    if _config_manager is None:
        environment = env or os.getenv("ENVIRONMENT", "development")
        _config_manager = IngestionConfigManager(environment)

    return _config_manager


def reset_config():
    """Reset the global configuration manager (mainly for testing)."""
    global _config_manager
    _config_manager = None


# Convenience function to get specific configuration sections
def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return get_config().database


def get_api_config() -> ApiConfig:
    """Get API configuration."""
    return get_config().api


def get_ingestion_config() -> IngestionConfig:
    """Get ingestion configuration."""
    return get_config().ingestion


def get_logging_config() -> LoggingConfig:
    """Get logging configuration."""
    return get_config().logging


def get_cache_config() -> CacheConfig:
    """Get cache configuration."""
    return get_config().cache


def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration."""
    return get_config().monitoring
