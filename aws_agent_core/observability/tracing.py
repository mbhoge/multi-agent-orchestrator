"""Tracing utilities using AWS Agent Core Runtime SDK."""

import logging
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from shared.utils.exceptions import ObservabilityError

logger = logging.getLogger(__name__)


class AgentCoreTracer:
    """Tracer for AWS Agent Core operations."""
    
    def __init__(self):
        """Initialize the tracer."""
        self.traces: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized Agent Core Tracer")
    
    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing operations.
        
        Args:
            operation_name: Name of the operation being traced
            trace_id: Optional trace ID
            metadata: Optional metadata to include in trace
        
        Yields:
            Trace context dictionary
        """
        if not trace_id:
            trace_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        start_time = time.time()
        trace_context = {
            "trace_id": trace_id,
            "operation": operation_name,
            "start_time": start_time,
            "metadata": metadata or {},
        }
        
        try:
            logger.debug(f"Starting trace for operation: {operation_name}, trace_id: {trace_id}")
            yield trace_context
            
            # Record successful completion
            trace_context["duration"] = time.time() - start_time
            trace_context["status"] = "success"
            self.traces[trace_id] = trace_context
            logger.debug(f"Completed trace for operation: {operation_name}, duration: {trace_context['duration']:.2f}s")
            
        except Exception as e:
            # Record failure
            trace_context["duration"] = time.time() - start_time
            trace_context["status"] = "error"
            trace_context["error"] = str(e)
            self.traces[trace_id] = trace_context
            logger.error(f"Trace error for operation: {operation_name}, error: {str(e)}")
            raise
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get trace information by trace ID.
        
        Args:
            trace_id: Trace identifier
        
        Returns:
            Trace information or None if not found
        """
        return self.traces.get(trace_id)
    
    def get_all_traces(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all traces.
        
        Returns:
            Dictionary of all traces
        """
        return self.traces.copy()


# Global tracer instance
tracer = AgentCoreTracer()

