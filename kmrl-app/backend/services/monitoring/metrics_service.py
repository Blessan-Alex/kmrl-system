"""
Metrics Service for KMRL Gateway
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

class MetricsService:
    """Enhanced metrics service for KMRL gateway"""
    
    def __init__(self, port: int = 8002):
        self.redis_client = self._connect_redis()
        self.port = port
        self.registry = CollectorRegistry()
        self.start_time = time.time()
        
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
            'kmrl_gateway_requests_total',
            'Total gateway requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'kmrl_gateway_request_duration_seconds',
            'Gateway request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Document processing metrics
        self.documents_uploaded = Counter(
            'kmrl_gateway_documents_uploaded_total',
            'Total documents uploaded',
            ['source', 'status'],
            registry=self.registry
        )
        
        self.document_upload_duration = Histogram(
            'kmrl_gateway_document_upload_duration_seconds',
            'Document upload duration',
            ['source'],
            registry=self.registry
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'kmrl_gateway_queue_size',
            'Queue size',
            ['queue_name'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'kmrl_gateway_errors_total',
            'Total errors',
            ['error_type', 'endpoint'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'kmrl_gateway_active_connections',
            'Active connections',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'kmrl_gateway_memory_usage_bytes',
            'Memory usage',
            registry=self.registry
        )
        
        # Health metrics
        self.health_status = Gauge(
            'kmrl_gateway_health_status',
            'Health status (1=healthy, 0=unhealthy)',
            registry=self.registry
        )
        
        # Processing metrics
        self.processing_duration = Histogram(
            'kmrl_gateway_processing_duration_seconds',
            'Document processing duration',
            ['stage'],
            registry=self.registry
        )
        
        # File size metrics
        self.file_size = Histogram(
            'kmrl_gateway_file_size_bytes',
            'Uploaded file sizes',
            ['source'],
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
            
            # Update memory usage
            self.memory_usage.set(memory_usage)
            
            # Update health status (simplified)
            self.health_status.set(1)  # Assume healthy for now
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _collect_redis_metrics(self):
        """Collect Redis metrics"""
        try:
            # Get queue sizes
            queue_keys = [
                'document_processing',
                'rag_processing',
                'notifications',
                'celery'
            ]
            
            for queue_key in queue_keys:
                try:
                    size = self.redis_client.llen(queue_key)
                    self.queue_size.labels(queue_name=queue_key).set(size)
                except Exception:
                    self.queue_size.labels(queue_name=queue_key).set(0)
                    
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record request metrics"""
        try:
            self.requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            self.request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record request metrics: {e}")
    
    def record_document_upload(self, source: str, file_size: int, duration: float, status: str = "success"):
        """Record document upload metrics"""
        try:
            self.documents_uploaded.labels(
                source=source,
                status=status
            ).inc()
            
            self.document_upload_duration.labels(
                source=source
            ).observe(duration)
            
            self.file_size.labels(
                source=source
            ).observe(file_size)
            
        except Exception as e:
            logger.error(f"Failed to record document upload metrics: {e}")
    
    def record_error(self, error_type: str, endpoint: str = "unknown"):
        """Record error metrics"""
        try:
            self.errors_total.labels(
                error_type=error_type,
                endpoint=endpoint
            ).inc()
            
        except Exception as e:
            logger.error(f"Failed to record error metrics: {e}")
    
    def record_processing_duration(self, stage: str, duration: float):
        """Record processing duration metrics"""
        try:
            self.processing_duration.labels(stage=stage).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record processing duration metrics: {e}")
    
    def update_active_connections(self, count: int):
        """Update active connections metric"""
        try:
            self.active_connections.set(count)
        except Exception as e:
            logger.error(f"Failed to update active connections metric: {e}")
    
    async def get_metrics(self) -> str:
        """Get Prometheus metrics report"""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics report: {e}")
            return f"# Error generating metrics: {e}"
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics summary"""
        try:
            # Get current metrics values
            summary = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': time.time() - self.start_time,
                'metrics': {
                    'requests_total': 'Available via /metrics endpoint',
                    'document_uploads': 'Available via /metrics endpoint',
                    'queue_sizes': 'Available via /metrics endpoint',
                    'error_rates': 'Available via /metrics endpoint'
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {'error': str(e)}
    
    async def get_processing_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        try:
            # Get processing statistics from Redis
            processing_stats = {
                'documents_processed_today': 0,
                'average_processing_time': 0,
                'error_rate': 0,
                'queue_backlog': 0
            }
            
            # Get queue sizes
            queue_keys = ['document_processing', 'rag_processing', 'notifications']
            for queue_key in queue_keys:
                try:
                    size = self.redis_client.llen(queue_key)
                    processing_stats['queue_backlog'] += size
                except Exception:
                    pass
            
            return processing_stats
            
        except Exception as e:
            logger.error(f"Failed to get processing metrics: {e}")
            return {'error': str(e)}
    
    def create_alert_conditions(self) -> List[Dict[str, Any]]:
        """Create alert conditions for monitoring"""
        return [
            {
                'name': 'high_error_rate',
                'condition': 'kmrl_gateway_errors_total > 10',
                'severity': 'warning',
                'description': 'High error rate detected'
            },
            {
                'name': 'queue_backlog',
                'condition': 'kmrl_gateway_queue_size > 100',
                'severity': 'warning',
                'description': 'Queue backlog detected'
            },
            {
                'name': 'gateway_down',
                'condition': 'kmrl_gateway_health_status == 0',
                'severity': 'critical',
                'description': 'Gateway is down'
            },
            {
                'name': 'high_memory_usage',
                'condition': 'kmrl_gateway_memory_usage_bytes > 1000000000',  # 1GB
                'severity': 'warning',
                'description': 'High memory usage detected'
            },
            {
                'name': 'slow_processing',
                'condition': 'kmrl_gateway_processing_duration_seconds > 30',
                'severity': 'warning',
                'description': 'Slow document processing detected'
            }
        ]

class MetricsMiddleware:
    """Middleware for automatic metrics collection"""
    
    def __init__(self, metrics_service: MetricsService):
        self.metrics_service = metrics_service
    
    def record_endpoint_metrics(self, endpoint: str, method: str, func):
        """Decorator to record endpoint metrics"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                self.metrics_service.record_error(type(e).__name__, endpoint)
                raise
            finally:
                duration = time.time() - start_time
                self.metrics_service.record_request(method, endpoint, 200 if status == 'success' else 500, duration)
        
        return wrapper

if __name__ == '__main__':
    # Test metrics service
    service = MetricsService()
    
    # Record some test metrics
    service.record_request('POST', '/api/v1/documents/upload', 200, 1.5)
    service.record_document_upload('gmail', 1024, 2.0)
    service.record_processing_duration('ocr', 5.0)
    
    # Get metrics summary
    import asyncio
    async def test_metrics():
        summary = await service.get_system_metrics()
        print(json.dumps(summary, indent=2))
    
    asyncio.run(test_metrics())
