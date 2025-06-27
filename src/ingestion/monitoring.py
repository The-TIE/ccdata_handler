"""
Advanced monitoring and alerting system for the unified data ingestion pipeline.

This module provides comprehensive monitoring capabilities including real-time metrics
tracking, alert thresholds, performance monitoring, and integration hooks for external
monitoring systems like Prometheus/Grafana.
"""

import asyncio
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import threading

from ..logger_config import setup_logger


logger = setup_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics that can be tracked."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Alert:
    """Represents an alert condition."""

    id: str
    level: AlertLevel
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class Metric:
    """Represents a metric measurement."""

    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics for ingestion operations."""

    operation: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_processed: int = 0
    records_inserted: int = 0
    api_calls: int = 0
    errors: int = 0
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class IngestionMonitor:
    """
    Comprehensive monitoring system for data ingestion operations.

    Provides real-time metrics tracking, alerting, performance monitoring,
    and data quality checks with support for external monitoring integrations.
    """

    def __init__(self, config: Any):
        """
        Initialize the ingestion monitor.

        Args:
            config: Configuration object with monitoring settings
        """
        self.config = config
        self.logger = logger

        # Metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._alerts: List[Alert] = []
        self._performance_stats: List[PerformanceStats] = []

        # Alert thresholds
        self._alert_thresholds = self._initialize_alert_thresholds()

        # Alert handlers
        self._alert_handlers: List[Callable[[Alert], None]] = []

        # Metrics handlers for external systems
        self._metrics_handlers: List[Callable[[Metric], None]] = []

        # Thread safety
        self._lock = threading.RLock()

        # Background monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Data quality tracking
        self._data_quality_checks: Dict[str, Callable] = {}
        self._anomaly_detectors: Dict[str, Callable] = {}

        self.logger.info("IngestionMonitor initialized")

    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default alert thresholds."""
        return {
            "api_error_rate": {
                "warning": 0.05,  # 5% error rate
                "error": 0.10,  # 10% error rate
                "critical": 0.25,  # 25% error rate
                "window_minutes": 5,
            },
            "database_error_rate": {
                "warning": 0.02,  # 2% error rate
                "error": 0.05,  # 5% error rate
                "critical": 0.15,  # 15% error rate
                "window_minutes": 5,
            },
            "ingestion_latency": {
                "warning": 300,  # 5 minutes
                "error": 600,  # 10 minutes
                "critical": 1800,  # 30 minutes
            },
            "consecutive_failures": {
                "warning": 3,
                "error": 5,
                "critical": 10,
            },
            "data_freshness": {
                "warning": 3600,  # 1 hour
                "error": 7200,  # 2 hours
                "critical": 14400,  # 4 hours
            },
            "memory_usage": {
                "warning": 0.80,  # 80%
                "error": 0.90,  # 90%
                "critical": 0.95,  # 95%
            },
        }

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a metric measurement.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            labels: Optional labels for the metric
            metadata: Optional metadata
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(timezone.utc),
            labels=labels or {},
            metadata=metadata or {},
        )

        with self._lock:
            self._metrics[name].append(metric)

        # Send to external handlers
        for handler in self._metrics_handlers:
            try:
                handler(metric)
            except Exception as e:
                self.logger.error(f"Error in metrics handler: {e}")

        # Check for alert conditions
        self._check_metric_alerts(metric)

    def record_api_call(
        self,
        endpoint: str,
        success: bool,
        duration_ms: float,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ):
        """
        Record an API call for monitoring.

        Args:
            endpoint: API endpoint called
            success: Whether the call was successful
            duration_ms: Duration in milliseconds
            status_code: HTTP status code
            error: Error message if failed
        """
        labels = {"endpoint": endpoint, "success": str(success)}
        if status_code:
            labels["status_code"] = str(status_code)

        # Record metrics
        self.record_metric("api_calls_total", 1, MetricType.COUNTER, labels)
        self.record_metric(
            "api_call_duration_ms", duration_ms, MetricType.HISTOGRAM, labels
        )

        if not success:
            self.record_metric("api_errors_total", 1, MetricType.COUNTER, labels)
            if error:
                self.logger.warning(f"API call failed: {endpoint} - {error}")

    def record_database_operation(
        self,
        operation: str,
        table: str,
        success: bool,
        duration_ms: float,
        records_affected: int = 0,
        error: Optional[str] = None,
    ):
        """
        Record a database operation for monitoring.

        Args:
            operation: Type of operation (insert, update, select, etc.)
            table: Database table name
            success: Whether the operation was successful
            duration_ms: Duration in milliseconds
            records_affected: Number of records affected
            error: Error message if failed
        """
        labels = {"operation": operation, "table": table, "success": str(success)}

        # Record metrics
        self.record_metric("db_operations_total", 1, MetricType.COUNTER, labels)
        self.record_metric(
            "db_operation_duration_ms", duration_ms, MetricType.HISTOGRAM, labels
        )
        self.record_metric(
            "db_records_affected", records_affected, MetricType.HISTOGRAM, labels
        )

        if not success:
            self.record_metric("db_errors_total", 1, MetricType.COUNTER, labels)
            if error:
                self.logger.error(
                    f"Database operation failed: {operation} on {table} - {error}"
                )

    def start_performance_tracking(
        self, operation: str, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking performance for an operation.

        Args:
            operation: Name of the operation
            metadata: Optional metadata

        Returns:
            Tracking ID for the operation
        """
        tracking_id = f"{operation}_{int(time.time() * 1000)}"

        stats = PerformanceStats(
            operation=operation,
            start_time=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

        with self._lock:
            # Store with tracking ID for later retrieval
            setattr(stats, "tracking_id", tracking_id)
            self._performance_stats.append(stats)

        return tracking_id

    def end_performance_tracking(
        self,
        tracking_id: str,
        records_processed: int = 0,
        records_inserted: int = 0,
        api_calls: int = 0,
        errors: int = 0,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        End performance tracking for an operation.

        Args:
            tracking_id: Tracking ID returned by start_performance_tracking
            records_processed: Number of records processed
            records_inserted: Number of records inserted
            api_calls: Number of API calls made
            errors: Number of errors encountered
            success: Whether the operation was successful
            metadata: Additional metadata
        """
        with self._lock:
            # Find the performance stats by tracking ID
            stats = None
            for s in reversed(self._performance_stats):
                if hasattr(s, "tracking_id") and s.tracking_id == tracking_id:
                    stats = s
                    break

            if not stats:
                self.logger.warning(
                    f"Performance tracking not found for ID: {tracking_id}"
                )
                return

            # Update stats
            end_time = datetime.now(timezone.utc)
            stats.end_time = end_time
            stats.duration_seconds = (end_time - stats.start_time).total_seconds()
            stats.records_processed = records_processed
            stats.records_inserted = records_inserted
            stats.api_calls = api_calls
            stats.errors = errors
            stats.success = success

            if metadata:
                stats.metadata.update(metadata)

        # Record performance metrics
        labels = {"operation": stats.operation, "success": str(success)}
        self.record_metric(
            "operation_duration_seconds",
            stats.duration_seconds,
            MetricType.HISTOGRAM,
            labels,
        )
        self.record_metric(
            "operation_records_processed",
            records_processed,
            MetricType.HISTOGRAM,
            labels,
        )
        self.record_metric(
            "operation_records_inserted", records_inserted, MetricType.HISTOGRAM, labels
        )

        if errors > 0:
            self.record_metric("operation_errors", errors, MetricType.COUNTER, labels)

        # Check for performance alerts
        self._check_performance_alerts(stats)

    def create_alert(
        self,
        alert_id: str,
        level: AlertLevel,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """
        Create and record an alert.

        Args:
            alert_id: Unique identifier for the alert
            level: Alert severity level
            message: Alert message
            source: Source of the alert
            metadata: Optional metadata

        Returns:
            Created Alert object
        """
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            timestamp=datetime.now(timezone.utc),
            source=source,
            metadata=metadata or {},
        )

        with self._lock:
            self._alerts.append(alert)

        # Send to alert handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

        # Log the alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }.get(level, logging.INFO)

        self.logger.log(log_level, f"ALERT [{level.value.upper()}] {source}: {message}")

        return alert

    def resolve_alert(self, alert_id: str):
        """
        Resolve an alert by ID.

        Args:
            alert_id: ID of the alert to resolve
        """
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(timezone.utc)
                    self.logger.info(f"Alert resolved: {alert_id}")
                    break

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """
        Add an alert handler function.

        Args:
            handler: Function that takes an Alert object
        """
        self._alert_handlers.append(handler)

    def add_metrics_handler(self, handler: Callable[[Metric], None]):
        """
        Add a metrics handler function for external systems.

        Args:
            handler: Function that takes a Metric object
        """
        self._metrics_handlers.append(handler)

    def add_data_quality_check(self, name: str, check_func: Callable[[Any], bool]):
        """
        Add a data quality check function.

        Args:
            name: Name of the check
            check_func: Function that returns True if data passes quality check
        """
        self._data_quality_checks[name] = check_func

    def add_anomaly_detector(self, name: str, detector_func: Callable[[Any], bool]):
        """
        Add an anomaly detection function.

        Args:
            name: Name of the detector
            detector_func: Function that returns True if anomaly is detected
        """
        self._anomaly_detectors[name] = detector_func

    def run_data_quality_checks(self, data: Any, source: str) -> Dict[str, bool]:
        """
        Run all data quality checks on the provided data.

        Args:
            data: Data to check
            source: Source identifier for the data

        Returns:
            Dictionary mapping check names to results
        """
        results = {}

        for check_name, check_func in self._data_quality_checks.items():
            try:
                result = check_func(data)
                results[check_name] = result

                if not result:
                    self.create_alert(
                        alert_id=f"data_quality_{check_name}_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        message=f"Data quality check failed: {check_name}",
                        source=source,
                        metadata={"check": check_name, "data_source": source},
                    )
            except Exception as e:
                self.logger.error(f"Error in data quality check {check_name}: {e}")
                results[check_name] = False

        return results

    def run_anomaly_detection(self, data: Any, source: str) -> Dict[str, bool]:
        """
        Run all anomaly detectors on the provided data.

        Args:
            data: Data to analyze
            source: Source identifier for the data

        Returns:
            Dictionary mapping detector names to results
        """
        results = {}

        for detector_name, detector_func in self._anomaly_detectors.items():
            try:
                result = detector_func(data)
                results[detector_name] = result

                if result:  # Anomaly detected
                    self.create_alert(
                        alert_id=f"anomaly_{detector_name}_{int(time.time())}",
                        level=AlertLevel.WARNING,
                        message=f"Anomaly detected: {detector_name}",
                        source=source,
                        metadata={"detector": detector_name, "data_source": source},
                    )
            except Exception as e:
                self.logger.error(f"Error in anomaly detector {detector_name}: {e}")
                results[detector_name] = False

        return results

    def get_metrics_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get a summary of metrics for the specified time window.

        Args:
            time_window_minutes: Time window in minutes

        Returns:
            Dictionary containing metrics summary
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=time_window_minutes
        )
        summary = {}
        total_metrics = 0

        with self._lock:
            for metric_name, metric_deque in self._metrics.items():
                recent_metrics = [m for m in metric_deque if m.timestamp >= cutoff_time]

                if recent_metrics:
                    values = [m.value for m in recent_metrics]
                    summary[metric_name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "latest": values[-1],
                        "latest_timestamp": recent_metrics[-1].timestamp.isoformat(),
                    }
                    total_metrics += len(values)

        summary["total_metrics"] = total_metrics
        return summary

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        Get active (unresolved) alerts.

        Args:
            level: Optional filter by alert level

        Returns:
            List of active alerts
        """
        with self._lock:
            alerts = [a for a in self._alerts if not a.resolved]

            if level:
                alerts = [a for a in alerts if a.level == level]

            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Get performance summary for the specified time window.

        Args:
            time_window_minutes: Time window in minutes

        Returns:
            Dictionary containing performance summary
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=time_window_minutes
        )

        with self._lock:
            recent_stats = [
                s
                for s in self._performance_stats
                if s.start_time >= cutoff_time and s.end_time is not None
            ]

        if not recent_stats:
            return {"total_operations": 0}

        # Group by operation
        by_operation = defaultdict(list)
        for stat in recent_stats:
            by_operation[stat.operation].append(stat)

        summary = {"total_operations": len(recent_stats)}

        for operation, stats in by_operation.items():
            durations = [s.duration_seconds for s in stats if s.duration_seconds]
            success_count = sum(1 for s in stats if s.success)

            summary[operation] = {
                "total_operations": len(stats),
                "successful_operations": success_count,
                "success_rate": success_count / len(stats) if stats else 0,
                "avg_duration_seconds": (
                    sum(durations) / len(durations) if durations else 0
                ),
                "total_records_processed": sum(s.records_processed for s in stats),
                "total_records_inserted": sum(s.records_inserted for s in stats),
                "total_errors": sum(s.errors for s in stats),
            }

        return summary

    def _check_metric_alerts(self, metric: Metric):
        """Check if a metric triggers any alerts."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated alerting logic
        pass

    def _check_performance_alerts(self, stats: PerformanceStats):
        """Check if performance stats trigger any alerts."""
        if not stats.success:
            self.create_alert(
                alert_id=f"operation_failure_{stats.operation}_{int(time.time())}",
                level=AlertLevel.ERROR,
                message=f"Operation failed: {stats.operation}",
                source="performance_monitor",
                metadata={
                    "operation": stats.operation,
                    "duration": stats.duration_seconds,
                },
            )

        # Check latency thresholds
        if stats.duration_seconds and "ingestion_latency" in self._alert_thresholds:
            thresholds = self._alert_thresholds["ingestion_latency"]

            if stats.duration_seconds >= thresholds["critical"]:
                level = AlertLevel.CRITICAL
            elif stats.duration_seconds >= thresholds["error"]:
                level = AlertLevel.ERROR
            elif stats.duration_seconds >= thresholds["warning"]:
                level = AlertLevel.WARNING
            else:
                level = None

            if level:
                self.create_alert(
                    alert_id=f"high_latency_{stats.operation}_{int(time.time())}",
                    level=level,
                    message=f"High latency detected: {stats.operation} took {stats.duration_seconds:.2f}s",
                    source="performance_monitor",
                    metadata={
                        "operation": stats.operation,
                        "duration": stats.duration_seconds,
                    },
                )

    async def start_monitoring(self):
        """Start the background monitoring task."""
        if self._monitoring_task and not self._monitoring_task.done():
            self.logger.warning("Monitoring task already running")
            return

        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Background monitoring started")

    async def stop_monitoring(self):
        """Stop the background monitoring task."""
        if self._monitoring_task:
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
            self.logger.info("Background monitoring stopped")

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                # Perform periodic health checks
                await self._perform_health_checks()

                # Clean up old metrics and alerts
                await self._cleanup_old_data()

                # Wait for next check
                await asyncio.sleep(self.config.monitoring.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _perform_health_checks(self):
        """Perform periodic health checks."""
        # Check system resources
        try:
            import psutil

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent / 100.0
            self.record_metric("system_memory_usage", memory_percent, MetricType.GAUGE)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1) / 100.0
            self.record_metric("system_cpu_usage", cpu_percent, MetricType.GAUGE)

            # Check memory thresholds
            if "memory_usage" in self._alert_thresholds:
                thresholds = self._alert_thresholds["memory_usage"]

                if memory_percent >= thresholds["critical"]:
                    level = AlertLevel.CRITICAL
                elif memory_percent >= thresholds["error"]:
                    level = AlertLevel.ERROR
                elif memory_percent >= thresholds["warning"]:
                    level = AlertLevel.WARNING
                else:
                    level = None

                if level:
                    self.create_alert(
                        alert_id=f"high_memory_usage_{int(time.time())}",
                        level=level,
                        message=f"High memory usage: {memory_percent:.1%}",
                        source="system_monitor",
                        metadata={"memory_percent": memory_percent},
                    )

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            self.logger.error(f"Error in health checks: {e}")

    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts."""
        retention_days = self.config.monitoring.metrics_retention_days
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days)

        with self._lock:
            # Clean up old metrics
            for metric_name, metric_deque in self._metrics.items():
                # Remove old metrics (deque automatically limits size, but we can clean by time too)
                while metric_deque and metric_deque[0].timestamp < cutoff_time:
                    metric_deque.popleft()

            # Clean up old performance stats
            self._performance_stats = [
                s for s in self._performance_stats if s.start_time >= cutoff_time
            ]

            # Clean up old resolved alerts
            self._alerts = [
                a
                for a in self._alerts
                if not a.resolved or (a.resolved_at and a.resolved_at >= cutoff_time)
            ]

    def export_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            String containing Prometheus-formatted metrics
        """
        lines = []

        with self._lock:
            for metric_name, metric_deque in self._metrics.items():
                if not metric_deque:
                    continue

                latest_metric = metric_deque[-1]

                # Convert metric name to Prometheus format
                prom_name = metric_name.replace("-", "_").replace(".", "_")

                # Add labels
                labels_str = ""
                if latest_metric.labels:
                    label_pairs = [
                        f'{k}="{v}"' for k, v in latest_metric.labels.items()
                    ]
                    labels_str = "{" + ",".join(label_pairs) + "}"

                lines.append(f"{prom_name}{labels_str} {latest_metric.value}")

        return "\n".join(lines)

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of the ingestion system.

        Returns:
            Dictionary containing health status information
        """
        active_alerts = self.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in active_alerts if a.level == AlertLevel.ERROR]

        # Determine overall health
        if critical_alerts:
            health = "critical"
        elif error_alerts:
            health = "degraded"
        elif active_alerts:
            health = "warning"
        else:
            health = "healthy"

        return {
            "status": health,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_alerts_count": len(active_alerts),
            "alerts": {
                "total": len(active_alerts),
                "critical": len(critical_alerts),
                "error": len(error_alerts),
                "warning": len(
                    [a for a in active_alerts if a.level == AlertLevel.WARNING]
                ),
            },
            "metrics_count": sum(len(deque) for deque in self._metrics.values()),
            "monitoring_active": self._monitoring_task is not None
            and not self._monitoring_task.done(),
        }
