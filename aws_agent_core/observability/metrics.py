"""Metrics collection for AWS Agent Core."""

import logging
import time
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
from shared.utils.exceptions import ObservabilityError

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collector for metrics and performance data."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics: Dict[str, list] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        logger.info("Initialized Metrics Collector")
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        metric_entry = {
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "tags": tags or {},
        }
        self.metrics[metric_name].append(metric_entry)
        logger.debug(f"Recorded metric: {metric_name} = {value}")
    
    def increment_counter(
        self,
        counter_name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Increment a counter.
        
        Args:
            counter_name: Name of the counter
            value: Value to increment by
            tags: Optional tags for the counter
        """
        self.counters[counter_name] += value
        logger.debug(f"Incremented counter: {counter_name} by {value}")
    
    def record_timing(
        self,
        operation_name: str,
        duration: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record timing information for an operation.
        
        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
            tags: Optional tags
        """
        self.record_metric(f"{operation_name}.duration", duration, tags)
        self.record_metric(f"{operation_name}.duration_ms", duration * 1000, tags)
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a metric.
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            Summary statistics
        """
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {
                "name": metric_name,
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
            }
        
        values = [m["value"] for m in self.metrics[metric_name]]
        return {
            "name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary of all metrics and counters
        """
        return {
            "metrics": dict(self.metrics),
            "counters": dict(self.counters),
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()

