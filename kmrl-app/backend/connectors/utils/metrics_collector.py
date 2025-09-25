"""
Metrics Collector for KMRL Connectors
Prometheus metrics collection and monitoring
"""

import os
import time
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry, generate_latest
import threading

logger = structlog.get_logger()

class ConnectorMetricsCollector:
    """Metrics collector for KMRL connector system"""
    
    def __init__(self, port: int = 8001):
        self.redis_client = self._connect_redis()
        self.port = port
        self.registry = CollectorRegistry()
        
        # Initialize metrics
        self._initialize_metrics()
        
        # Start metrics server
        self._start_metrics_server()
        
        # Start background metrics collection
        self._start_background_collection()
    
    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        return redis.Redis.from_url(redis_url, decode_responses=True)
    
    def _initialize_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Request metrics
        self.requests_total = Counter(
            'kmrl_connector_requests_total',
            'Total connector requests',
            ['connector', 'operation', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'kmrl_connector_request_duration_seconds',
            'Connector request duration',
            ['connector', 'operation'],
            registry=self.registry
        )
        
        # Document processing metrics
        self.documents_processed = Counter(
            'kmrl_connector_documents_processed_total',
            'Total documents processed',
            ['connector', 'status'],
            registry=self.registry
        )
        
        self.document_processing_time = Histogram(
            'kmrl_connector_document_processing_seconds',
            'Document processing time',
            ['connector'],
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'kmrl_connector_queue_size',
            'Queue size',
            ['queue_name'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'kmrl_connector_errors_total',
            'Total errors',
            ['connector', 'error_type'],
            registry=self.registry
        )
        
        # Sync metrics
        self.sync_duration = Histogram(
            'kmrl_connector_sync_duration_seconds',
            'Sync operation duration',
            ['connector'],
            registry=self.registry
        )
        
        self.sync_frequency = Counter(
            'kmrl_connector_sync_total',
            'Total sync operations',
            ['connector', 'status'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'kmrl_connector_active_connections',
            'Active connections',
            ['connector'],
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'kmrl_connector_memory_usage_bytes',
            'Memory usage',
            ['connector'],
            registry=self.registry
        )
        
        # Health metrics
        self.health_status = Gauge(
            'kmrl_connector_health_status',
            'Health status (1=healthy, 0=unhealthy)',
            ['connector'],
            registry=self.registry
        )
        
        # Performance metrics
        self.throughput = Gauge(
            'kmrl_connector_throughput_documents_per_second',
            'Documents processed per second',
            ['connector'],
            registry=self.registry
        )
        
        logger.info("Metrics initialized")
    
    def _start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            start_http_server(self.port, registry=self.registry)
            logger.info(f"Metrics server started on port {self.port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
    
    def _start_background_collection(self):
        """Start background metrics collection"""
        def collect_metrics():
            while True:
                try:
                    self._collect_system_metrics()
                    self._collect_redis_metrics()
                    self._collect_connector_metrics()
                    time.sleep(30)  # Collect every 30 seconds
                except Exception as e:
                    logger.error(f"Background metrics collection failed: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info("Background metrics collection started")
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            
            # Get process info
            process = psutil.Process()
            memory_usage = process.memory_info().rss
            
            # Update memory usage for each connector
            connectors = ['gmail', 'google_drive', 'maximo', 'whatsapp']
            for connector in connectors:
                self.memory_usage.labels(connector=connector).set(memory_usage)
                
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _collect_redis_metrics(self):
        """Collect Redis metrics"""
        try:
            # Get queue sizes
            queue_keys = [
                'celery',
                'document_processing',
                'rag_processing',
                'notifications'
            ]
            
            for queue_key in queue_keys:
                try:
                    size = self.redis_client.llen(queue_key)
                    self.queue_size.labels(queue_name=queue_key).set(size)
                except Exception:
                    self.queue_size.labels(queue_name=queue_key).set(0)
                    
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
    
    def _collect_connector_metrics(self):
        """Collect connector-specific metrics"""
        try:
            # Get connector health from Redis
            health_data = self.redis_client.hget('connector_health', 'status')
            
            if health_data:
                connector_status = json.loads(health_data)
                
                for connector_name, status in connector_status.items():
                    if isinstance(status, dict) and 'error' not in status:
                        self.health_status.labels(connector=connector_name).set(1)
                    else:
                        self.health_status.labels(connector=connector_name).set(0)
                        
        except Exception as e:
            logger.error(f"Failed to collect connector metrics: {e}")
    
    def record_request(self, connector: str, operation: str, status: str, duration: float):
        """Record connector request metrics"""
        try:
            self.requests_total.labels(
                connector=connector,
                operation=operation,
                status=status
            ).inc()
            
            self.request_duration.labels(
                connector=connector,
                operation=operation
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    def record_document_processing(self, connector: str, status: str, duration: float, count: int = 1):
        """Record document processing metrics"""
        try:
            self.documents_processed.labels(
                connector=connector,
                status=status
            ).inc(count)
            
            self.document_processing_time.labels(
                connector=connector
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record document processing metrics: {e}")
    
    def record_error(self, connector: str, error_type: str):
        """Record error metrics"""
        try:
            self.errors_total.labels(
                connector=connector,
                error_type=error_type
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def record_sync_operation(self, connector: str, status: str, duration: float):
        """Record sync operation metrics"""
        try:
            self.sync_duration.labels(connector=connector).observe(duration)
            self.sync_frequency.labels(
                connector=connector,
                status=status
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record sync metrics: {e}")
    
    def update_throughput(self, connector: str, documents_per_second: float):
        """Update throughput metrics"""
        try:
            self.throughput.labels(connector=connector).set(documents_per_second)
        except Exception as e:
            logger.error(f"Failed to update throughput metrics: {e}")
    
    def update_active_connections(self, connector: str, count: int):
        """Update active connections metric"""
        try:
            self.active_connections.labels(connector=connector).set(count)
        except Exception as e:
            logger.error(f"Failed to update active connections metric: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            # Get current metrics values
            summary = {
                'timestamp': datetime.now().isoformat(),
                'metrics': {}
            }
            
            # This is a simplified implementation
            # In production, you'd query the actual metric values
            summary['metrics'] = {
                'requests_total': 'Available via /metrics endpoint',
                'document_processing': 'Available via /metrics endpoint',
                'queue_sizes': 'Available via /metrics endpoint',
                'error_rates': 'Available via /metrics endpoint'
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {'error': str(e)}
    
    def generate_metrics_report(self) -> str:
        """Generate Prometheus metrics report"""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics report: {e}")
            return f"# Error generating metrics: {e}"
    
    def get_connector_performance_stats(self, connector: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for a specific connector"""
        try:
            # This is a simplified implementation
            # In production, you'd query historical metrics from a time-series database
            
            stats = {
                'connector': connector,
                'timeframe_hours': hours,
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'total_requests': 'Query from metrics endpoint',
                    'success_rate': 'Query from metrics endpoint',
                    'average_response_time': 'Query from metrics endpoint',
                    'documents_processed': 'Query from metrics endpoint',
                    'error_count': 'Query from metrics endpoint'
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get connector performance stats: {e}")
            return {'error': str(e)}
    
    def create_alert_conditions(self) -> List[Dict[str, Any]]:
        """Create alert conditions for monitoring"""
        return [
            {
                'name': 'high_error_rate',
                'condition': 'kmrl_connector_errors_total > 10',
                'severity': 'warning',
                'description': 'High error rate detected'
            },
            {
                'name': 'queue_backlog',
                'condition': 'kmrl_connector_queue_size > 100',
                'severity': 'warning',
                'description': 'Queue backlog detected'
            },
            {
                'name': 'connector_down',
                'condition': 'kmrl_connector_health_status == 0',
                'severity': 'critical',
                'description': 'Connector is down'
            },
            {
                'name': 'high_memory_usage',
                'condition': 'kmrl_connector_memory_usage_bytes > 1000000000',  # 1GB
                'severity': 'warning',
                'description': 'High memory usage detected'
            },
            {
                'name': 'slow_processing',
                'condition': 'kmrl_connector_document_processing_seconds > 30',
                'severity': 'warning',
                'description': 'Slow document processing detected'
            }
        ]

class MetricsMiddleware:
    """Middleware for automatic metrics collection"""
    
    def __init__(self, metrics_collector: ConnectorMetricsCollector):
        self.metrics_collector = metrics_collector
    
    def record_connector_operation(self, connector: str, operation: str, func):
        """Decorator to record connector operations"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                self.metrics_collector.record_error(connector, type(e).__name__)
                raise
            finally:
                duration = time.time() - start_time
                self.metrics_collector.record_request(connector, operation, status, duration)
        
        return wrapper

if __name__ == '__main__':
    # Test metrics collector
    collector = ConnectorMetricsCollector()
    
    # Record some test metrics
    collector.record_request('gmail', 'sync', 'success', 1.5)
    collector.record_document_processing('gmail', 'success', 2.0, 5)
    collector.record_sync_operation('gmail', 'success', 30.0)
    
    # Get metrics summary
    summary = collector.get_metrics_summary()
    print(json.dumps(summary, indent=2))
    
    # Generate metrics report
    report = collector.generate_metrics_report()
    print("\nMetrics Report:")
    print(report[:500] + "..." if len(report) > 500 else report)
