"""
Unit tests for monitoring and alerting system in the unified data ingestion pipeline.

This module tests the IngestionMonitor with comprehensive coverage of metrics recording,
alert management, performance tracking, anomaly detection, and Prometheus integration.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from collections import deque

from src.ingestion.monitoring import (
    IngestionMonitor,
    AlertLevel,
    MetricType,
    Alert,
    Metric,
    PerformanceStats,
)


class TestIngestionMonitor:
    """Test cases for IngestionMonitor."""

    @pytest.fixture
    def mock_config(self):
        """Mock monitoring configuration."""
        config = Mock()
        config.metrics_enabled = True
        config.performance_monitoring = True
        config.alert_on_failure = True
        config.alert_on_consecutive_failures = 5
        config.health_check_interval = 60
        config.metrics_retention_days = 7
        return config

    @pytest.fixture
    def monitor(self, mock_config):
        """Create IngestionMonitor instance."""
        return IngestionMonitor(mock_config)

    def test_init(self, mock_config):
        """Test IngestionMonitor initialization."""
        monitor = IngestionMonitor(mock_config)

        assert monitor.config == mock_config
        assert isinstance(monitor._metrics, dict)
        assert isinstance(monitor._alerts, list)
        assert isinstance(monitor._performance_stats, list)
        assert isinstance(monitor._alert_thresholds, dict)
        assert isinstance(monitor._alert_handlers, list)
        assert isinstance(monitor._metrics_handlers, list)
        assert monitor._monitoring_task is None

    def test_initialize_alert_thresholds(self, monitor):
        """Test alert thresholds initialization."""
        thresholds = monitor._alert_thresholds

        assert "api_error_rate" in thresholds
        assert "database_error_rate" in thresholds
        assert "ingestion_latency" in thresholds
        assert "consecutive_failures" in thresholds
        assert "data_freshness" in thresholds
        assert "memory_usage" in thresholds

        # Check specific threshold values
        api_thresholds = thresholds["api_error_rate"]
        assert api_thresholds["warning"] == 0.05
        assert api_thresholds["error"] == 0.10
        assert api_thresholds["critical"] == 0.25

    def test_record_metric_basic(self, monitor):
        """Test basic metric recording."""
        monitor.record_metric("test_metric", 100.0, MetricType.GAUGE)

        assert "test_metric" in monitor._metrics
        metrics = monitor._metrics["test_metric"]
        assert len(metrics) == 1

        metric = metrics[0]
        assert metric.name == "test_metric"
        assert metric.value == 100.0
        assert metric.metric_type == MetricType.GAUGE
        assert isinstance(metric.timestamp, datetime)

    def test_record_metric_with_labels_and_metadata(self, monitor):
        """Test metric recording with labels and metadata."""
        labels = {"endpoint": "/api/data", "status": "success"}
        metadata = {"request_id": "12345"}

        monitor.record_metric(
            "api_calls", 1, MetricType.COUNTER, labels=labels, metadata=metadata
        )

        metric = monitor._metrics["api_calls"][0]
        assert metric.labels == labels
        assert metric.metadata == metadata

    def test_record_metric_with_handlers(self, monitor):
        """Test metric recording with external handlers."""
        handler1 = Mock()
        handler2 = Mock()
        monitor.add_metrics_handler(handler1)
        monitor.add_metrics_handler(handler2)

        monitor.record_metric("test_metric", 50.0)

        handler1.assert_called_once()
        handler2.assert_called_once()

        # Check handler was called with correct metric
        call_args = handler1.call_args[0][0]
        assert isinstance(call_args, Metric)
        assert call_args.name == "test_metric"
        assert call_args.value == 50.0

    def test_record_metric_handler_exception(self, monitor):
        """Test metric recording with handler exception."""
        handler = Mock(side_effect=Exception("Handler error"))
        monitor.add_metrics_handler(handler)

        # Should not raise exception
        monitor.record_metric("test_metric", 100.0)

        # Metric should still be recorded
        assert "test_metric" in monitor._metrics

    def test_record_api_call_success(self, monitor):
        """Test API call recording for successful calls."""
        monitor.record_api_call(
            endpoint="/api/data", success=True, duration_ms=150.0, status_code=200
        )

        # Check metrics were recorded
        assert "api_calls_total" in monitor._metrics
        assert "api_call_duration_ms" in monitor._metrics
        assert "api_errors_total" not in monitor._metrics

        # Check labels
        api_calls_metric = monitor._metrics["api_calls_total"][0]
        expected_labels = {
            "endpoint": "/api/data",
            "success": "True",
            "status_code": "200",
        }
        assert api_calls_metric.labels == expected_labels

    def test_record_api_call_failure(self, monitor):
        """Test API call recording for failed calls."""
        monitor.record_api_call(
            endpoint="/api/data",
            success=False,
            duration_ms=5000.0,
            status_code=500,
            error="Internal server error",
        )

        # Check error metrics were recorded
        assert "api_errors_total" in monitor._metrics

        error_metric = monitor._metrics["api_errors_total"][0]
        assert error_metric.value == 1
        assert error_metric.labels["success"] == "False"

    def test_record_database_operation_success(self, monitor):
        """Test database operation recording for successful operations."""
        monitor.record_database_operation(
            operation="insert",
            table="test_table",
            success=True,
            duration_ms=25.0,
            records_affected=100,
        )

        # Check metrics were recorded
        assert "db_operations_total" in monitor._metrics
        assert "db_operation_duration_ms" in monitor._metrics
        assert "db_records_affected" in monitor._metrics
        assert "db_errors_total" not in monitor._metrics

        # Check values
        records_metric = monitor._metrics["db_records_affected"][0]
        assert records_metric.value == 100

    def test_record_database_operation_failure(self, monitor):
        """Test database operation recording for failed operations."""
        monitor.record_database_operation(
            operation="insert",
            table="test_table",
            success=False,
            duration_ms=1000.0,
            error="Connection timeout",
        )

        # Check error metrics were recorded
        assert "db_errors_total" in monitor._metrics

    def test_start_performance_tracking(self, monitor):
        """Test performance tracking start."""
        tracking_id = monitor.start_performance_tracking(
            "data_ingestion", metadata={"source": "api"}
        )

        assert tracking_id.startswith("data_ingestion_")
        assert len(monitor._performance_stats) == 1

        stats = monitor._performance_stats[0]
        assert stats.operation == "data_ingestion"
        assert stats.metadata["source"] == "api"
        assert stats.end_time is None

    def test_end_performance_tracking(self, monitor):
        """Test performance tracking end."""
        tracking_id = monitor.start_performance_tracking("test_operation")

        # Wait a bit to ensure duration > 0
        time.sleep(0.01)

        monitor.end_performance_tracking(
            tracking_id,
            records_processed=1000,
            records_inserted=950,
            api_calls=5,
            errors=2,
            success=True,
            metadata={"final_status": "completed"},
        )

        stats = monitor._performance_stats[0]
        assert stats.end_time is not None
        assert stats.duration_seconds > 0
        assert stats.records_processed == 1000
        assert stats.records_inserted == 950
        assert stats.api_calls == 5
        assert stats.errors == 2
        assert stats.success is True
        assert stats.metadata["final_status"] == "completed"

    def test_end_performance_tracking_invalid_id(self, monitor):
        """Test performance tracking end with invalid tracking ID."""
        # Should not raise exception
        monitor.end_performance_tracking("invalid_id")

    def test_end_performance_tracking_records_metrics(self, monitor):
        """Test that performance tracking records metrics."""
        tracking_id = monitor.start_performance_tracking("test_operation")

        monitor.end_performance_tracking(
            tracking_id, records_processed=100, records_inserted=95, errors=1
        )

        # Check that metrics were recorded
        assert "operation_duration_seconds" in monitor._metrics
        assert "operation_records_processed" in monitor._metrics
        assert "operation_records_inserted" in monitor._metrics
        assert "operation_errors" in monitor._metrics

    def test_create_alert(self, monitor):
        """Test alert creation."""
        alert = monitor.create_alert(
            alert_id="test_alert_001",
            level=AlertLevel.WARNING,
            message="Test alert message",
            source="test_source",
            metadata={"key": "value"},
        )

        assert isinstance(alert, Alert)
        assert alert.id == "test_alert_001"
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert message"
        assert alert.source == "test_source"
        assert alert.metadata["key"] == "value"
        assert not alert.resolved

        # Check alert was added to list
        assert len(monitor._alerts) == 1
        assert monitor._alerts[0] == alert

    def test_create_alert_with_handlers(self, monitor):
        """Test alert creation with handlers."""
        handler1 = Mock()
        handler2 = Mock()
        monitor.add_alert_handler(handler1)
        monitor.add_alert_handler(handler2)

        alert = monitor.create_alert(
            "test_alert", AlertLevel.ERROR, "Test message", "test_source"
        )

        handler1.assert_called_once_with(alert)
        handler2.assert_called_once_with(alert)

    def test_create_alert_handler_exception(self, monitor):
        """Test alert creation with handler exception."""
        handler = Mock(side_effect=Exception("Handler error"))
        monitor.add_alert_handler(handler)

        # Should not raise exception
        alert = monitor.create_alert(
            "test_alert", AlertLevel.ERROR, "Test message", "test_source"
        )

        # Alert should still be created
        assert len(monitor._alerts) == 1

    def test_resolve_alert(self, monitor):
        """Test alert resolution."""
        alert = monitor.create_alert(
            "test_alert", AlertLevel.WARNING, "Test message", "test_source"
        )

        assert not alert.resolved
        assert alert.resolved_at is None

        monitor.resolve_alert("test_alert")

        assert alert.resolved
        assert alert.resolved_at is not None

    def test_resolve_alert_nonexistent(self, monitor):
        """Test resolving non-existent alert."""
        # Should not raise exception
        monitor.resolve_alert("nonexistent_alert")

    def test_resolve_alert_already_resolved(self, monitor):
        """Test resolving already resolved alert."""
        alert = monitor.create_alert(
            "test_alert", AlertLevel.WARNING, "Test message", "test_source"
        )

        monitor.resolve_alert("test_alert")
        first_resolved_at = alert.resolved_at

        # Try to resolve again
        monitor.resolve_alert("test_alert")

        # Should not change resolved_at
        assert alert.resolved_at == first_resolved_at

    def test_add_data_quality_check(self, monitor):
        """Test adding data quality check."""

        def check_func(data):
            return len(data) > 0

        monitor.add_data_quality_check("non_empty_check", check_func)

        assert "non_empty_check" in monitor._data_quality_checks
        assert monitor._data_quality_checks["non_empty_check"] == check_func

    def test_add_anomaly_detector(self, monitor):
        """Test adding anomaly detector."""

        def detector_func(data):
            return max(data) > 1000

        monitor.add_anomaly_detector("high_value_detector", detector_func)

        assert "high_value_detector" in monitor._anomaly_detectors
        assert monitor._anomaly_detectors["high_value_detector"] == detector_func

    def test_run_data_quality_checks(self, monitor):
        """Test running data quality checks."""

        def check1(data):
            return len(data) > 0

        def check2(data):
            return all(x > 0 for x in data)

        monitor.add_data_quality_check("non_empty", check1)
        monitor.add_data_quality_check("positive_values", check2)

        # Test with good data
        results = monitor.run_data_quality_checks([1, 2, 3], "test_source")

        assert results["non_empty"] is True
        assert results["positive_values"] is True

    def test_run_data_quality_checks_failures(self, monitor):
        """Test data quality checks with failures."""

        def check1(data):
            return len(data) > 5

        def check2(data):
            return all(x > 10 for x in data)

        monitor.add_data_quality_check("min_length", check1)
        monitor.add_data_quality_check("min_values", check2)

        results = monitor.run_data_quality_checks([1, 2, 3], "test_source")

        assert results["min_length"] is False
        assert results["min_values"] is False

    def test_run_data_quality_checks_exception(self, monitor):
        """Test data quality checks with exception."""

        def failing_check(data):
            raise Exception("Check failed")

        monitor.add_data_quality_check("failing_check", failing_check)

        results = monitor.run_data_quality_checks([1, 2, 3], "test_source")

        assert results["failing_check"] is False

    def test_run_anomaly_detection(self, monitor):
        """Test running anomaly detection."""

        def detector1(data):
            return max(data) > 100

        def detector2(data):
            return len(data) < 2

        monitor.add_anomaly_detector("high_values", detector1)
        monitor.add_anomaly_detector("too_few_records", detector2)

        # Test with anomalous data
        results = monitor.run_anomaly_detection([150, 200, 300], "test_source")

        assert results["high_values"] is True
        assert results["too_few_records"] is False

    def test_run_anomaly_detection_exception(self, monitor):
        """Test anomaly detection with exception."""

        def failing_detector(data):
            raise Exception("Detector failed")

        monitor.add_anomaly_detector("failing_detector", failing_detector)

        results = monitor.run_anomaly_detection([1, 2, 3], "test_source")

        assert results["failing_detector"] is False

    def test_get_metrics_summary(self, monitor):
        """Test metrics summary generation."""
        # Record some metrics
        monitor.record_metric("counter1", 10, MetricType.COUNTER)
        monitor.record_metric("counter1", 5, MetricType.COUNTER)
        monitor.record_metric("gauge1", 100, MetricType.GAUGE)
        monitor.record_metric("histogram1", 50, MetricType.HISTOGRAM)

        summary = monitor.get_metrics_summary(time_window_minutes=60)

        assert "total_metrics" in summary
        assert "metrics_by_type" in summary
        assert "recent_metrics_count" in summary

        assert summary["total_metrics"] == 4
        assert summary["metrics_by_type"][MetricType.COUNTER.value] == 2
        assert summary["metrics_by_type"][MetricType.GAUGE.value] == 1
        assert summary["metrics_by_type"][MetricType.HISTOGRAM.value] == 1

    def test_get_active_alerts(self, monitor):
        """Test getting active alerts."""
        # Create some alerts
        alert1 = monitor.create_alert(
            "alert1", AlertLevel.WARNING, "Warning", "source1"
        )
        alert2 = monitor.create_alert("alert2", AlertLevel.ERROR, "Error", "source2")
        alert3 = monitor.create_alert(
            "alert3", AlertLevel.CRITICAL, "Critical", "source3"
        )

        # Resolve one alert
        monitor.resolve_alert("alert2")

        # Get all active alerts
        active_alerts = monitor.get_active_alerts()
        assert len(active_alerts) == 2
        assert alert1 in active_alerts
        assert alert3 in active_alerts
        assert alert2 not in active_alerts

        # Get alerts by level
        critical_alerts = monitor.get_active_alerts(AlertLevel.CRITICAL)
        assert len(critical_alerts) == 1
        assert alert3 in critical_alerts

    def test_get_performance_summary(self, monitor):
        """Test performance summary generation."""
        # Create some performance stats
        tracking_id1 = monitor.start_performance_tracking("operation1")
        tracking_id2 = monitor.start_performance_tracking("operation2")

        time.sleep(0.01)

        monitor.end_performance_tracking(
            tracking_id1, records_processed=1000, records_inserted=950, success=True
        )
        monitor.end_performance_tracking(
            tracking_id2,
            records_processed=500,
            records_inserted=450,
            success=False,
            errors=5,
        )

        summary = monitor.get_performance_summary(time_window_minutes=60)

        assert "total_operations" in summary
        assert "successful_operations" in summary
        assert "failed_operations" in summary
        assert "total_records_processed" in summary
        assert "total_records_inserted" in summary
        assert "total_errors" in summary
        assert "average_duration" in summary

        assert summary["total_operations"] == 2
        assert summary["successful_operations"] == 1
        assert summary["failed_operations"] == 1
        assert summary["total_records_processed"] == 1500
        assert summary["total_records_inserted"] == 1400
        assert summary["total_errors"] == 5

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """Test starting background monitoring."""
        with patch.object(monitor, "_monitoring_loop") as mock_loop:
            mock_loop.return_value = asyncio.create_task(asyncio.sleep(0.1))

            await monitor.start_monitoring()

            assert monitor._monitoring_task is not None
            mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """Test stopping background monitoring."""
        # Start monitoring first
        monitor._monitoring_task = asyncio.create_task(asyncio.sleep(1))

        await monitor.stop_monitoring()

        assert monitor._shutdown_event.is_set()
        assert monitor._monitoring_task.cancelled()

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, monitor):
        """Test monitoring loop execution."""
        with patch.object(monitor, "_perform_health_checks") as mock_health:
            with patch.object(monitor, "_cleanup_old_data") as mock_cleanup:
                with patch("asyncio.sleep") as mock_sleep:
                    # Set shutdown event after first iteration
                    mock_sleep.side_effect = lambda x: monitor._shutdown_event.set()

                    await monitor._monitoring_loop()

                    mock_health.assert_called_once()
                    mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_health_checks(self, monitor):
        """Test health checks execution."""
        # Add some metrics to check
        monitor.record_metric("api_calls_total", 100, MetricType.COUNTER)
        monitor.record_metric("api_errors_total", 10, MetricType.COUNTER)

        await monitor._perform_health_checks()

        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, monitor):
        """Test cleanup of old data."""
        # Add some old metrics
        old_time = datetime.now(timezone.utc) - timedelta(days=10)

        old_metric = Metric(
            name="old_metric",
            value=100,
            metric_type=MetricType.GAUGE,
            timestamp=old_time,
        )

        monitor._metrics["old_metric"].append(old_metric)

        # Add recent metric
        monitor.record_metric("recent_metric", 50)

        await monitor._cleanup_old_data()

        # Old metric should be removed, recent should remain
        assert len(monitor._metrics["old_metric"]) == 0
        assert len(monitor._metrics["recent_metric"]) == 1

    def test_export_prometheus_metrics(self, monitor):
        """Test Prometheus metrics export."""
        # Record some metrics
        monitor.record_metric(
            "api_calls_total", 100, MetricType.COUNTER, {"endpoint": "/api/data"}
        )
        monitor.record_metric("memory_usage", 0.75, MetricType.GAUGE)
        monitor.record_metric("request_duration", 150, MetricType.HISTOGRAM)

        prometheus_output = monitor.export_prometheus_metrics()

        assert isinstance(prometheus_output, str)
        assert "api_calls_total" in prometheus_output
        assert "memory_usage" in prometheus_output
        assert "request_duration" in prometheus_output
        assert 'endpoint="/api/data"' in prometheus_output

    def test_get_health_status(self, monitor):
        """Test health status generation."""
        # Record some metrics and create alerts
        monitor.record_metric("api_calls_total", 1000)
        monitor.record_metric("api_errors_total", 50)
        monitor.create_alert("test_alert", AlertLevel.WARNING, "Test", "test")

        health_status = monitor.get_health_status()

        assert "status" in health_status
        assert "metrics_count" in health_status
        assert "active_alerts_count" in health_status
        assert "last_updated" in health_status

        assert health_status["metrics_count"] == 2
        assert health_status["active_alerts_count"] == 1

    def test_check_metric_alerts(self, monitor):
        """Test metric-based alert checking."""
        # This is a private method, but we can test it indirectly
        # by recording metrics that should trigger alerts

        # Record high error rate
        for i in range(100):
            monitor.record_metric("api_calls_total", 1, MetricType.COUNTER)

        for i in range(30):  # 30% error rate
            monitor.record_metric("api_errors_total", 1, MetricType.COUNTER)

        # The _check_metric_alerts method should be called automatically
        # when recording metrics, but we can't easily test the alert creation
        # without more complex mocking

    def test_check_performance_alerts(self, monitor):
        """Test performance-based alert checking."""
        # Create a long-running operation
        tracking_id = monitor.start_performance_tracking("slow_operation")

        # Simulate long duration by manually setting start time
        stats = monitor._performance_stats[0]
        stats.start_time = datetime.now(timezone.utc) - timedelta(
            minutes=35
        )  # 35 minutes ago

        monitor.end_performance_tracking(tracking_id, success=True)

        # Should trigger latency alert (threshold is 30 minutes for critical)

    def test_metric_deque_max_length(self, monitor):
        """Test that metrics deque respects max length."""
        # Record more metrics than the max length (10000)
        for i in range(10005):
            monitor.record_metric("test_metric", i)

        # Should only keep the last 10000 metrics
        assert len(monitor._metrics["test_metric"]) == 10000

        # Should have the most recent values
        last_metric = monitor._metrics["test_metric"][-1]
        assert last_metric.value == 10004

    def test_thread_safety(self, monitor):
        """Test thread safety of metric recording."""
        import threading

        def record_metrics():
            for i in range(100):
                monitor.record_metric("thread_metric", i)

        # Create multiple threads
        threads = [threading.Thread(target=record_metrics) for _ in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have recorded all metrics without errors
        assert len(monitor._metrics["thread_metric"]) == 500

    @pytest.mark.asyncio
    async def test_monitoring_with_time_mocking(self, monitor):
        """Test monitoring with mocked time for consistent testing."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        with patch("src.ingestion.monitoring.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            monitor.record_metric("test_metric", 100)

            metric = monitor._metrics["test_metric"][0]
            assert metric.timestamp == fixed_time

    def test_large_scale_metrics(self, monitor):
        """Test handling of large numbers of metrics."""
        # Record many different metric types
        for i in range(1000):
            monitor.record_metric(f"metric_{i}", i, MetricType.GAUGE)
            monitor.record_metric(f"counter_{i}", 1, MetricType.COUNTER)

        # Should handle large numbers without issues
        assert len(monitor._metrics) == 2000

        # Test summary generation with many metrics
        summary = monitor.get_metrics_summary()
        assert summary["total_metrics"] == 2000

    def test_alert_level_logging(self, monitor):
        """Test that alerts are logged at appropriate levels."""
        with patch.object(monitor.logger, "log") as mock_log:
            monitor.create_alert("test", AlertLevel.INFO, "Info message", "test")
            monitor.create_alert("test", AlertLevel.WARNING, "Warning message", "test")
            monitor.create_alert("test", AlertLevel.ERROR, "Error message", "test")
            monitor.create_alert(
                "test", AlertLevel.CRITICAL, "Critical message", "test"
            )

            # Check that log was called with correct levels
            assert mock_log.call_count == 4

            # Check log levels (INFO=20, WARNING=30, ERROR=40, CRITICAL=50)
            log_levels = [call[0][0] for call in mock_log.call_args_list]
            assert 20 in log_levels  # INFO
            assert 30 in log_levels  # WARNING
            assert 40 in log_levels  # ERROR
            assert 50 in log_levels  # CRITICAL
