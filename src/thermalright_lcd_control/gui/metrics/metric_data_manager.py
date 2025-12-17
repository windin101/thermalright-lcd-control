"""
Metric Data Manager - Centralized system metrics collection and distribution
"""
import threading
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from ...common.logging_config import get_gui_logger


class MetricType(Enum):
    """Types of metrics supported"""
    CPU_USAGE = "cpu_usage"
    CPU_TEMPERATURE = "cpu_temperature"
    CPU_FREQUENCY = "cpu_frequency"
    RAM_USAGE = "ram_usage"
    GPU_USAGE = "gpu_usage"
    GPU_TEMPERATURE = "gpu_temperature"
    NETWORK_UPLOAD = "network_upload"
    NETWORK_DOWNLOAD = "network_download"


@dataclass
class MetricValue:
    """Container for metric value with timestamp"""
    value: float
    unit: str
    timestamp: float
    label: str


class MetricDataManager:
    """Manages collection and distribution of system metrics"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize metric data manager"""
        if self._initialized:
            return
        
        self.logger = get_gui_logger()
        self.metrics: Dict[MetricType, MetricValue] = {}
        self.subscribers: Dict[str, Callable] = {}  # widget_id -> callback
        self.update_interval = 1.0  # seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Initialize metric collectors
        self._init_metric_collectors()
        
        self._initialized = True
        self.logger.info("MetricDataManager initialized")
    
    def _init_metric_collectors(self):
        """Initialize system metric collectors"""
        try:
            # Try to import CPU metrics
            from ...device_controller.metrics.cpu_metrics import CpuMetrics
            self.cpu_metrics = CpuMetrics()
            self.logger.info("CPU metrics collector initialized")
        except ImportError as e:
            self.logger.warning(f"Could not import CPU metrics: {e}")
            self.cpu_metrics = None
        
        try:
            # Try to import GPU metrics
            from ...device_controller.metrics.gpu_metrics import GpuMetrics
            self.gpu_metrics = GpuMetrics()
            self.logger.info("GPU metrics collector initialized")
        except ImportError as e:
            self.logger.warning(f"Could not import GPU metrics: {e}")
            self.gpu_metrics = None
        
        # Initialize psutil for RAM/network metrics
        try:
            import psutil
            self.psutil = psutil
            self.logger.info("psutil initialized for RAM/network metrics")
        except ImportError as e:
            self.logger.warning(f"Could not import psutil: {e}")
            self.psutil = None
    
    def start(self):
        """Start metric collection thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        self.logger.info("MetricDataManager started")
    
    def stop(self):
        """Stop metric collection thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("MetricDataManager stopped")
    
    def _update_loop(self):
        """Main update loop for collecting metrics"""
        while self.running:
            try:
                self._collect_metrics()
                self._notify_subscribers()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error in metric update loop: {e}")
                time.sleep(self.update_interval)
    
    def _collect_metrics(self):
        """Collect all system metrics"""
        timestamp = time.time()
        
        # CPU metrics
        if self.cpu_metrics:
            try:
                # CPU usage
                cpu_usage = self.cpu_metrics.get_usage_percentage()
                if cpu_usage is not None:
                    self.metrics[MetricType.CPU_USAGE] = MetricValue(
                        value=cpu_usage,
                        unit="%",
                        timestamp=timestamp,
                        label="CPU Usage"
                    )
                
                # CPU temperature
                cpu_temp = self.cpu_metrics.get_temperature()
                if cpu_temp is not None:
                    self.metrics[MetricType.CPU_TEMPERATURE] = MetricValue(
                        value=cpu_temp,
                        unit="°C",
                        timestamp=timestamp,
                        label="CPU Temp"
                    )
                
                # CPU frequency
                cpu_freq = self.cpu_metrics.get_frequency()
                if cpu_freq is not None:
                    self.metrics[MetricType.CPU_FREQUENCY] = MetricValue(
                        value=cpu_freq,
                        unit="MHz",
                        timestamp=timestamp,
                        label="CPU Freq"
                    )
            except Exception as e:
                self.logger.error(f"Error collecting CPU metrics: {e}")
        
        # GPU metrics
        if self.gpu_metrics:
            try:
                # GPU usage
                gpu_usage = self.gpu_metrics.get_usage_percentage()
                if gpu_usage is not None:
                    self.metrics[MetricType.GPU_USAGE] = MetricValue(
                        value=gpu_usage,
                        unit="%",
                        timestamp=timestamp,
                        label="GPU Usage"
                    )
                
                # GPU temperature
                gpu_temp = self.gpu_metrics.get_temperature()
                if gpu_temp is not None:
                    self.metrics[MetricType.GPU_TEMPERATURE] = MetricValue(
                        value=gpu_temp,
                        unit="°C",
                        timestamp=timestamp,
                        label="GPU Temp"
                    )
            except Exception as e:
                self.logger.error(f"Error collecting GPU metrics: {e}")
        
        # RAM metrics (using psutil)
        if self.psutil:
            try:
                ram = self.psutil.virtual_memory()
                ram_usage = ram.percent
                self.metrics[MetricType.RAM_USAGE] = MetricValue(
                    value=ram_usage,
                    unit="%",
                    timestamp=timestamp,
                    label="RAM Usage"
                )
            except Exception as e:
                self.logger.error(f"Error collecting RAM metrics: {e}")
    
    def get_metric(self, metric_type: MetricType) -> Optional[MetricValue]:
        """Get current value for a metric type"""
        return self.metrics.get(metric_type)
    
    def get_metric_value(self, metric_type_str: str) -> Optional[float]:
        """Get metric value by string type"""
        try:
            metric_type = MetricType(metric_type_str)
            metric = self.metrics.get(metric_type)
            return metric.value if metric else None
        except (ValueError, KeyError):
            return None
    
    def subscribe(self, widget_id: str, callback: Callable):
        """Subscribe widget to metric updates"""
        self.subscribers[widget_id] = callback
        self.logger.debug(f"Widget {widget_id} subscribed to metric updates")
    
    def unsubscribe(self, widget_id: str):
        """Unsubscribe widget from metric updates"""
        if widget_id in self.subscribers:
            del self.subscribers[widget_id]
            self.logger.debug(f"Widget {widget_id} unsubscribed from metric updates")
    
    def _notify_subscribers(self):
        """Notify all subscribers of metric updates"""
        for widget_id, callback in self.subscribers.items():
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error notifying widget {widget_id}: {e}")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all current metrics as dictionary"""
        result = {}
        for metric_type, metric_value in self.metrics.items():
            result[metric_type.value] = {
                'value': metric_value.value,
                'unit': metric_value.unit,
                'label': metric_value.label,
                'timestamp': metric_value.timestamp
            }
        return result


# Global instance
_metric_manager: Optional[MetricDataManager] = None


def get_metric_manager() -> MetricDataManager:
    """Get global metric data manager instance"""
    global _metric_manager
    if _metric_manager is None:
        _metric_manager = MetricDataManager()
    return _metric_manager