"""
Unit tests for the ingestion configuration management system.

This module tests the configuration classes and IngestionConfigManager,
including environment loading, validation, type checking, and
environment-specific overrides.
"""

import pytest
import os
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from dataclasses import asdict

from src.ingestion.config import (
    DatabaseConfig,
    ApiConfig,
    IngestionConfig,
    LoggingConfig,
    MonitoringConfig,
    IngestionConfigManager,
    get_config,
    reset_config,
    get_database_config,
    get_api_config,
    get_ingestion_config,
    get_logging_config,
    get_monitoring_config,
)


class TestDatabaseConfig:
    """Test cases for DatabaseConfig dataclass."""

    def test_default_values(self):
        """Test DatabaseConfig default values."""
        config = DatabaseConfig()

        assert config.host == ""
        assert config.port == 3306
        assert config.user == ""
        assert config.password == ""
        assert config.database == ""
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_timeout == 30
        assert config.pool_recycle == 3600

    def test_custom_values(self):
        """Test DatabaseConfig with custom values."""
        config = DatabaseConfig(
            host="test-host",
            port=5432,
            user="test-user",
            password="test-pass",
            database="test-db",
            pool_size=5,
            max_overflow=10,
            pool_timeout=60,
            pool_recycle=7200,
        )

        assert config.host == "test-host"
        assert config.port == 5432
        assert config.user == "test-user"
        assert config.password == "test-pass"
        assert config.database == "test-db"
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.pool_timeout == 60
        assert config.pool_recycle == 7200


class TestApiConfig:
    """Test cases for ApiConfig dataclass."""

    def test_default_values(self):
        """Test ApiConfig default values."""
        config = ApiConfig()

        assert config.ccdata_api_key == ""
        assert config.min_api_base_url == "https://min-api.cryptocompare.com/data"
        assert config.data_api_base_url == "https://data-api.cryptocompare.com"
        assert config.request_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.rate_limit_calls_per_second == 10.0
        assert config.rate_limit_calls_per_minute == 300
        assert config.rate_limit_calls_per_hour == 10000

    def test_custom_values(self):
        """Test ApiConfig with custom values."""
        config = ApiConfig(
            ccdata_api_key="test-key",
            min_api_base_url="https://test-min-api.com",
            data_api_base_url="https://test-data-api.com",
            request_timeout=60,
            max_retries=5,
            retry_delay=2.0,
            rate_limit_calls_per_second=5.0,
            rate_limit_calls_per_minute=150,
            rate_limit_calls_per_hour=5000,
        )

        assert config.ccdata_api_key == "test-key"
        assert config.min_api_base_url == "https://test-min-api.com"
        assert config.data_api_base_url == "https://test-data-api.com"
        assert config.request_timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.rate_limit_calls_per_second == 5.0
        assert config.rate_limit_calls_per_minute == 150
        assert config.rate_limit_calls_per_hour == 5000


class TestIngestionConfig:
    """Test cases for IngestionConfig dataclass."""

    def test_default_values(self):
        """Test IngestionConfig default values."""
        config = IngestionConfig()

        assert config.batch_size == 1000
        assert config.max_api_limit == 5000
        assert config.api_call_delay == 0.1
        assert config.backfill_enabled is True
        assert config.max_backfill_days == 365
        assert config.metadata_full_refresh is False
        assert config.metadata_change_detection is True
        assert config.parallel_workers == 4
        assert config.chunk_size == 10000
        assert config.default_intervals == ["1d", "1h", "1m"]
        assert config.max_limit_per_call == {"1d": 5000, "1h": 2000, "1m": 2000}
        assert config.futures_exchanges == []
        assert config.futures_instrument_statuses == ["ACTIVE", "EXPIRED"]
        assert config.max_consecutive_failures == 5
        assert config.failure_backoff_multiplier == 2.0
        assert config.max_failure_backoff == 300

    def test_custom_values(self):
        """Test IngestionConfig with custom values."""
        config = IngestionConfig(
            batch_size=500,
            max_api_limit=2000,
            api_call_delay=0.2,
            backfill_enabled=False,
            max_backfill_days=30,
            metadata_full_refresh=True,
            metadata_change_detection=False,
            parallel_workers=2,
            chunk_size=5000,
            default_intervals=["1d"],
            max_limit_per_call={"1d": 1000},
            futures_exchanges=["BINANCE", "COINBASE"],
            futures_instrument_statuses=["ACTIVE"],
            max_consecutive_failures=3,
            failure_backoff_multiplier=1.5,
            max_failure_backoff=120,
        )

        assert config.batch_size == 500
        assert config.max_api_limit == 2000
        assert config.api_call_delay == 0.2
        assert config.backfill_enabled is False
        assert config.max_backfill_days == 30
        assert config.metadata_full_refresh is True
        assert config.metadata_change_detection is False
        assert config.parallel_workers == 2
        assert config.chunk_size == 5000
        assert config.default_intervals == ["1d"]
        assert config.max_limit_per_call == {"1d": 1000}
        assert config.futures_exchanges == ["BINANCE", "COINBASE"]
        assert config.futures_instrument_statuses == ["ACTIVE"]
        assert config.max_consecutive_failures == 3
        assert config.failure_backoff_multiplier == 1.5
        assert config.max_failure_backoff == 120


class TestLoggingConfig:
    """Test cases for LoggingConfig dataclass."""

    def test_default_values(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.file_enabled is True
        assert config.file_path == "logs/ingestion.log"
        assert config.file_max_bytes == 10 * 1024 * 1024
        assert config.file_backup_count == 5
        assert config.console_enabled is True

    def test_custom_values(self):
        """Test LoggingConfig with custom values."""
        config = LoggingConfig(
            level="DEBUG",
            format="%(levelname)s - %(message)s",
            file_enabled=False,
            file_path="test.log",
            file_max_bytes=1024,
            file_backup_count=2,
            console_enabled=False,
        )

        assert config.level == "DEBUG"
        assert config.format == "%(levelname)s - %(message)s"
        assert config.file_enabled is False
        assert config.file_path == "test.log"
        assert config.file_max_bytes == 1024
        assert config.file_backup_count == 2
        assert config.console_enabled is False


class TestMonitoringConfig:
    """Test cases for MonitoringConfig dataclass."""

    def test_default_values(self):
        """Test MonitoringConfig default values."""
        config = MonitoringConfig()

        assert config.metrics_enabled is True
        assert config.performance_monitoring is True
        assert config.alert_on_failure is True
        assert config.alert_on_consecutive_failures == 3
        assert config.health_check_interval == 300
        assert config.metrics_retention_days == 30

    def test_custom_values(self):
        """Test MonitoringConfig with custom values."""
        config = MonitoringConfig(
            metrics_enabled=False,
            performance_monitoring=False,
            alert_on_failure=False,
            alert_on_consecutive_failures=5,
            health_check_interval=600,
            metrics_retention_days=7,
        )

        assert config.metrics_enabled is False
        assert config.performance_monitoring is False
        assert config.alert_on_failure is False
        assert config.alert_on_consecutive_failures == 5
        assert config.health_check_interval == 600
        assert config.metrics_retention_days == 7


class TestIngestionConfigManager:
    """Test cases for IngestionConfigManager class."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear environment variables
        env_vars_to_clear = [
            "S2_HOST",
            "S2_PORT",
            "S2_USER",
            "S2_PASSWORD",
            "S2_DATABASE",
            "CCDATA_API_KEY",
            "INGESTION_BATCH_SIZE",
            "LOG_LEVEL",
            "FUTURES_EXCHANGES",
            "FUTURES_INSTRUMENT_STATUSES",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]

    @patch("src.ingestion.config.find_dotenv")
    @patch("src.ingestion.config.load_dotenv")
    def test_initialization_development(self, mock_load_dotenv, mock_find_dotenv):
        """Test IngestionConfigManager initialization in development environment."""
        mock_find_dotenv.return_value = ".env"

        with patch.dict(
            os.environ,
            {
                "S2_HOST": "dev-host",
                "S2_USER": "dev-user",
                "S2_PASSWORD": "dev-pass",
                "S2_DATABASE": "dev-db",
                "CCDATA_API_KEY": "dev-key",
            },
        ):
            config_manager = IngestionConfigManager("development")

        assert config_manager.env == "development"
        assert config_manager.database.host == "dev-host"
        assert config_manager.database.user == "dev-user"
        assert config_manager.api.ccdata_api_key == "dev-key"

        # Verify dotenv loading was called
        mock_find_dotenv.assert_called_once()
        assert mock_load_dotenv.call_count >= 1

    @patch("src.ingestion.config.find_dotenv")
    @patch("src.ingestion.config.load_dotenv")
    @patch("pathlib.Path.exists")
    def test_environment_specific_config_loading(
        self, mock_exists, mock_load_dotenv, mock_find_dotenv
    ):
        """Test loading of environment-specific configuration files."""
        mock_find_dotenv.return_value = ".env"
        mock_exists.return_value = True

        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-pass",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("staging")

        # Should load both base .env and .env.staging
        assert mock_load_dotenv.call_count == 2

        # Check that environment-specific file was attempted
        mock_exists.assert_called_once()

    def test_database_config_loading(self):
        """Test database configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-db-host",
                "S2_PORT": "5432",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-database",
                "DB_POOL_SIZE": "15",
                "DB_MAX_OVERFLOW": "25",
                "DB_POOL_TIMEOUT": "45",
                "DB_POOL_RECYCLE": "7200",
            },
        ):
            config_manager = IngestionConfigManager("test")

        db_config = config_manager.database
        assert db_config.host == "test-db-host"
        assert db_config.port == 5432
        assert db_config.user == "test-user"
        assert db_config.password == "test-password"
        assert db_config.database == "test-database"
        assert db_config.pool_size == 15
        assert db_config.max_overflow == 25
        assert db_config.pool_timeout == 45
        assert db_config.pool_recycle == 7200

    def test_api_config_loading(self):
        """Test API configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "CCDATA_API_KEY": "test-api-key",
                "MIN_API_BASE_URL": "https://test-min-api.com",
                "DATA_API_BASE_URL": "https://test-data-api.com",
                "API_REQUEST_TIMEOUT": "60",
                "API_MAX_RETRIES": "5",
                "API_RETRY_DELAY": "2.5",
                "API_RATE_LIMIT_PER_SECOND": "5.0",
                "API_RATE_LIMIT_PER_MINUTE": "150",
                "API_RATE_LIMIT_PER_HOUR": "5000",
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-pass",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        api_config = config_manager.api
        assert api_config.ccdata_api_key == "test-api-key"
        assert api_config.min_api_base_url == "https://test-min-api.com"
        assert api_config.data_api_base_url == "https://test-data-api.com"
        assert api_config.request_timeout == 60
        assert api_config.max_retries == 5
        assert api_config.retry_delay == 2.5
        assert api_config.rate_limit_calls_per_second == 5.0
        assert api_config.rate_limit_calls_per_minute == 150
        assert api_config.rate_limit_calls_per_hour == 5000

    def test_ingestion_config_loading(self):
        """Test ingestion configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "INGESTION_BATCH_SIZE": "500",
                "INGESTION_MAX_API_LIMIT": "2000",
                "INGESTION_API_CALL_DELAY": "0.2",
                "INGESTION_BACKFILL_ENABLED": "false",
                "INGESTION_MAX_BACKFILL_DAYS": "30",
                "METADATA_FULL_REFRESH": "true",
                "METADATA_CHANGE_DETECTION": "false",
                "INGESTION_PARALLEL_WORKERS": "2",
                "INGESTION_CHUNK_SIZE": "5000",
                "FUTURES_EXCHANGES": "BINANCE,COINBASE,KRAKEN",
                "FUTURES_INSTRUMENT_STATUSES": "ACTIVE,PENDING",
                "INGESTION_MAX_CONSECUTIVE_FAILURES": "3",
                "INGESTION_FAILURE_BACKOFF_MULTIPLIER": "1.5",
                "INGESTION_MAX_FAILURE_BACKOFF": "120",
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-pass",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        ingestion_config = config_manager.ingestion
        assert ingestion_config.batch_size == 500
        assert ingestion_config.max_api_limit == 2000
        assert ingestion_config.api_call_delay == 0.2
        assert ingestion_config.backfill_enabled is False
        assert ingestion_config.max_backfill_days == 30
        assert ingestion_config.metadata_full_refresh is True
        assert ingestion_config.metadata_change_detection is False
        assert ingestion_config.parallel_workers == 2
        assert ingestion_config.chunk_size == 5000
        assert ingestion_config.futures_exchanges == ["BINANCE", "COINBASE", "KRAKEN"]
        assert ingestion_config.futures_instrument_statuses == ["ACTIVE", "PENDING"]
        assert ingestion_config.max_consecutive_failures == 3
        assert ingestion_config.failure_backoff_multiplier == 1.5
        assert ingestion_config.max_failure_backoff == 120

    def test_logging_config_loading(self):
        """Test logging configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "LOG_LEVEL": "DEBUG",
                "LOG_FORMAT": "%(levelname)s - %(message)s",
                "LOG_FILE_ENABLED": "false",
                "LOG_FILE_PATH": "test.log",
                "LOG_FILE_MAX_BYTES": "1024",
                "LOG_FILE_BACKUP_COUNT": "2",
                "LOG_CONSOLE_ENABLED": "false",
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-pass",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        logging_config = config_manager.logging
        assert logging_config.level == "DEBUG"
        assert logging_config.format == "%(levelname)s - %(message)s"
        assert logging_config.file_enabled is False
        assert logging_config.file_path == "test.log"
        assert logging_config.file_max_bytes == 1024
        assert logging_config.file_backup_count == 2
        assert logging_config.console_enabled is False

    def test_monitoring_config_loading(self):
        """Test monitoring configuration loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "MONITORING_METRICS_ENABLED": "false",
                "MONITORING_PERFORMANCE_ENABLED": "false",
                "MONITORING_ALERT_ON_FAILURE": "false",
                "MONITORING_ALERT_CONSECUTIVE_FAILURES": "5",
                "MONITORING_HEALTH_CHECK_INTERVAL": "600",
                "MONITORING_METRICS_RETENTION_DAYS": "7",
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-pass",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        monitoring_config = config_manager.monitoring
        assert monitoring_config.metrics_enabled is False
        assert monitoring_config.performance_monitoring is False
        assert monitoring_config.alert_on_failure is False
        assert monitoring_config.alert_on_consecutive_failures == 5
        assert monitoring_config.health_check_interval == 600
        assert monitoring_config.metrics_retention_days == 7

    def test_validation_success(self):
        """Test successful configuration validation."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "CCDATA_API_KEY": "test-key",
                "LOG_LEVEL": "INFO",
            },
        ):
            # Should not raise any exceptions
            config_manager = IngestionConfigManager("test")
            assert config_manager.env == "test"

    def test_validation_missing_database_config(self):
        """Test validation failure with missing database configuration."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "",  # Empty required field
                "S2_PASSWORD": "",  # Empty required field
                "S2_DATABASE": "",  # Empty required field
            },
            clear=True,  # Clear all environment variables first
        ):
            with pytest.raises(ValueError, match="Database configuration incomplete"):
                IngestionConfigManager("test")

    def test_validation_invalid_batch_size(self):
        """Test validation failure with invalid batch size."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "INGESTION_BATCH_SIZE": "0",  # Invalid
            },
        ):
            with pytest.raises(
                ValueError, match="Ingestion batch_size must be positive"
            ):
                IngestionConfigManager("test")

    def test_validation_invalid_log_level(self):
        """Test validation failure with invalid log level."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "LOG_LEVEL": "INVALID",
            },
        ):
            with pytest.raises(ValueError, match="Invalid log level"):
                IngestionConfigManager("test")

    def test_validation_missing_api_key_warning(self):
        """Test that missing API key generates warning but doesn't fail validation."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                # CCDATA_API_KEY not set
            },
        ):
            # Should not raise exception, but should log warning
            config_manager = IngestionConfigManager("test")
            assert config_manager.api.ccdata_api_key == ""

    def test_get_environment_info(self):
        """Test getting environment information."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "CCDATA_API_KEY": "test-key",
            },
        ):
            config_manager = IngestionConfigManager("test")

        env_info = config_manager.get_environment_info()

        assert env_info["environment"] == "test"
        assert env_info["database_host"] == "test-host"
        assert env_info["database_name"] == "test-db"
        assert "api_base_urls" in env_info
        assert "ingestion_settings" in env_info
        assert env_info["logging_level"] == "INFO"
        assert env_info["monitoring_enabled"] is True

    def test_update_config_database(self):
        """Test updating database configuration at runtime."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "original-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        # Update database config
        config_manager.update_config("database", host="new-host", port=5432)

        assert config_manager.database.host == "new-host"
        assert config_manager.database.port == 5432

    def test_update_config_api(self):
        """Test updating API configuration at runtime."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        # Update API config
        config_manager.update_config(
            "api", ccdata_api_key="new-key", request_timeout=60
        )

        assert config_manager.api.ccdata_api_key == "new-key"
        assert config_manager.api.request_timeout == 60

    def test_update_config_ingestion(self):
        """Test updating ingestion configuration at runtime."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        # Update ingestion config
        config_manager.update_config(
            "ingestion", batch_size=500, backfill_enabled=False
        )

        assert config_manager.ingestion.batch_size == 500
        assert config_manager.ingestion.backfill_enabled is False

    def test_update_config_invalid_section(self):
        """Test updating configuration with invalid section."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        with pytest.raises(ValueError, match="Unknown configuration section"):
            config_manager.update_config("invalid_section", some_key="some_value")

    def test_update_config_invalid_attribute(self):
        """Test updating configuration with invalid attribute."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        # Should not raise error, but should not update anything
        original_host = config_manager.database.host
        config_manager.update_config("database", invalid_attribute="value")

        assert config_manager.database.host == original_host
        assert not hasattr(config_manager.database, "invalid_attribute")


class TestGlobalConfigFunctions:
    """Test cases for global configuration functions."""

    def setup_method(self):
        """Setup for each test method."""
        reset_config()

    def teardown_method(self):
        """Cleanup after each test method."""
        reset_config()

    @patch.dict(
        os.environ,
        {
            "S2_HOST": "global-test-host",
            "S2_USER": "global-test-user",
            "S2_PASSWORD": "global-test-password",
            "S2_DATABASE": "global-test-db",
        },
    )
    def test_get_config_first_call(self):
        """Test get_config function on first call."""
        config = get_config("test")

        assert isinstance(config, IngestionConfigManager)
        assert config.env == "test"
        assert config.database.host == "global-test-host"

    @patch.dict(
        os.environ,
        {
            "S2_HOST": "global-test-host",
            "S2_USER": "global-test-user",
            "S2_PASSWORD": "global-test-password",
            "S2_DATABASE": "global-test-db",
            "ENVIRONMENT": "production",
        },
    )
    def test_get_config_default_environment(self):
        """Test get_config function with default environment from env var."""
        config = get_config()

        assert config.env == "production"

    @patch.dict(
        os.environ,
        {
            "S2_HOST": "global-test-host",
            "S2_USER": "global-test-user",
            "S2_PASSWORD": "global-test-password",
            "S2_DATABASE": "global-test-db",
        },
    )
    def test_get_config_subsequent_calls(self):
        """Test get_config function returns same instance on subsequent calls."""
        config1 = get_config("test")
        config2 = get_config("different")  # Should ignore this parameter

        assert config1 is config2
        assert config1.env == "test"  # Should keep original environment

    def test_reset_config(self):
        """Test reset_config function."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            config1 = get_config("test")
            reset_config()
            config2 = get_config("production")

        assert config1 is not config2
        assert config1.env == "test"
        assert config2.env == "production"

    @patch.dict(
        os.environ,
        {
            "S2_HOST": "convenience-test-host",
            "S2_USER": "convenience-test-user",
            "S2_PASSWORD": "convenience-test-password",
            "S2_DATABASE": "convenience-test-db",
        },
    )
    def test_convenience_functions(self):
        """Test convenience functions for getting specific config sections."""
        # Initialize global config
        get_config("test")

        db_config = get_database_config()
        api_config = get_api_config()
        ingestion_config = get_ingestion_config()
        logging_config = get_logging_config()
        monitoring_config = get_monitoring_config()

        assert isinstance(db_config, DatabaseConfig)
        assert isinstance(api_config, ApiConfig)
        assert isinstance(ingestion_config, IngestionConfig)
        assert isinstance(logging_config, LoggingConfig)
        assert isinstance(monitoring_config, MonitoringConfig)

        assert db_config.host == "convenience-test-host"


class TestConfigEdgeCases:
    """Test edge cases and error conditions for configuration management."""

    def test_futures_exchanges_empty_string(self):
        """Test parsing of empty futures exchanges string."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "FUTURES_EXCHANGES": "",  # Empty string
            },
        ):
            config_manager = IngestionConfigManager("test")

        assert config_manager.ingestion.futures_exchanges == []

    def test_futures_exchanges_with_whitespace(self):
        """Test parsing of futures exchanges with whitespace."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "FUTURES_EXCHANGES": " BINANCE , COINBASE , KRAKEN ",  # With whitespace
            },
        ):
            config_manager = IngestionConfigManager("test")

        assert config_manager.ingestion.futures_exchanges == [
            "BINANCE",
            "COINBASE",
            "KRAKEN",
        ]

    def test_futures_instrument_statuses_custom(self):
        """Test parsing of custom futures instrument statuses."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "FUTURES_INSTRUMENT_STATUSES": "ACTIVE,PENDING,SUSPENDED",
            },
        ):
            config_manager = IngestionConfigManager("test")

        assert config_manager.ingestion.futures_instrument_statuses == [
            "ACTIVE",
            "PENDING",
            "SUSPENDED",
        ]

    def test_boolean_environment_variables(self):
        """Test parsing of boolean environment variables."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "INGESTION_BACKFILL_ENABLED": "TRUE",  # Uppercase
                "METADATA_FULL_REFRESH": "True",  # Mixed case
                "METADATA_CHANGE_DETECTION": "false",  # Lowercase
                "LOG_FILE_ENABLED": "FALSE",  # Uppercase false
            },
        ):
            config_manager = IngestionConfigManager("test")

        assert config_manager.ingestion.backfill_enabled is True
        assert config_manager.ingestion.metadata_full_refresh is True
        assert config_manager.ingestion.metadata_change_detection is False
        assert config_manager.logging.file_enabled is False

    def test_numeric_environment_variables_invalid(self):
        """Test handling of invalid numeric environment variables."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
                "S2_PORT": "invalid-port",  # Invalid integer
                "API_RETRY_DELAY": "invalid-float",  # Invalid float
            },
        ):
            # Should raise ValueError during int() or float() conversion
            with pytest.raises(ValueError):
                IngestionConfigManager("test")

    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are collected and reported."""
        with patch.dict(
            os.environ,
            {
                # Missing database config
                "INGESTION_BATCH_SIZE": "0",  # Invalid batch size
                "INGESTION_PARALLEL_WORKERS": "-1",  # Invalid worker count
                "LOG_LEVEL": "INVALID",  # Invalid log level
            },
        ):
            with pytest.raises(ValueError) as exc_info:
                IngestionConfigManager("test")

            error_message = str(exc_info.value)
            assert "Database configuration incomplete" in error_message
            assert "batch_size must be positive" in error_message
            assert "parallel_workers must be positive" in error_message
            assert "Invalid log level" in error_message

    @patch("src.ingestion.config.Path.exists")
    def test_environment_specific_file_not_exists(self, mock_exists):
        """Test behavior when environment-specific config file doesn't exist."""
        mock_exists.return_value = False

        with patch.dict(
            os.environ,
            {
                "S2_HOST": "test-host",
                "S2_USER": "test-user",
                "S2_PASSWORD": "test-password",
                "S2_DATABASE": "test-db",
            },
        ):
            # Should not raise error even if .env.test doesn't exist
            config_manager = IngestionConfigManager("test")
            assert config_manager.env == "test"

    def test_config_with_all_defaults(self):
        """Test configuration with all default values (minimal environment)."""
        with patch.dict(
            os.environ,
            {
                "S2_HOST": "minimal-host",
                "S2_USER": "minimal-user",
                "S2_PASSWORD": "minimal-password",
                "S2_DATABASE": "minimal-db",
            },
        ):
            config_manager = IngestionConfigManager("test")

        # Verify that defaults are used for non-required settings
        assert config_manager.ingestion.batch_size == 1000  # Default
        assert config_manager.api.request_timeout == 30  # Default
        assert config_manager.logging.level == "INFO"  # Default
        assert config_manager.monitoring.metrics_enabled is True  # Default
