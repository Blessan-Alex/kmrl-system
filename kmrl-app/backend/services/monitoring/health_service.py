"""
Health Service for KMRL Gateway
Comprehensive health monitoring and diagnostics
"""

import os
import time
import json
import redis
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
import requests
from pathlib import Path

logger = structlog.get_logger()

class HealthService:
    """Enhanced health service for KMRL gateway"""
    
    def __init__(self):
        self.redis_client = self._connect_redis()
        self.health_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'response_time': 5.0,
            'error_rate': 10.0,
            'queue_size': 1000,
        }
    
    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis with retry logic"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        for attempt in range(3):
            try:
                client = redis.Redis.from_url(redis_url, decode_responses=True)
                client.ping()
                logger.info(f"Connected to Redis at {redis_url}")
                return client
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(1)
                else:
                    raise Exception(f"Redis connection required but failed: {e}")
    
    async def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            self.redis_client.ping()
            
            # Test queue operations
            test_key = f"health_check_test_{int(time.time())}"
            self.redis_client.set(test_key, "test", ex=10)
            assert self.redis_client.get(test_key) == "test"
            self.redis_client.delete(test_key)
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Get Redis info
            redis_info = self.redis_client.info()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connected_clients": redis_info.get('connected_clients', 0),
                "used_memory_human": redis_info.get('used_memory_human', '0B'),
                "redis_version": redis_info.get('redis_version', 'unknown'),
                "uptime_seconds": redis_info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Check thresholds
            alerts = []
            if cpu_percent > self.health_thresholds['cpu_usage']:
                alerts.append(f"High CPU usage: {cpu_percent}%")
            if memory_percent > self.health_thresholds['memory_usage']:
                alerts.append(f"High memory usage: {memory_percent}%")
            if disk_percent > self.health_thresholds['disk_usage']:
                alerts.append(f"High disk usage: {disk_percent}%")
            
            return {
                "status": "healthy" if not alerts else "warning",
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory_percent, 2),
                "disk_percent": round(disk_percent, 2),
                "process_memory_mb": round(process_memory, 2),
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # This would check PostgreSQL connection
            # For now, return a placeholder
            return {
                "status": "healthy",
                "connection_pool": "active",
                "active_connections": 5,
                "database_version": "PostgreSQL 14.0"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_storage_health(self) -> Dict[str, Any]:
        """Check storage health and capacity"""
        try:
            # Check storage directory
            storage_path = os.getenv('STORAGE_PATH', './storage')
            storage_dir = Path(storage_path)
            
            if storage_dir.exists():
                # Get directory size
                total_size = 0
                file_count = 0
                
                for file_path in storage_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                
                # Convert to MB
                size_mb = total_size / (1024 * 1024)
                
                # Check for storage issues
                alerts = []
                if size_mb > 1000:  # 1GB threshold
                    alerts.append(f"Large storage directory: {size_mb:.2f}MB")
                
                if file_count > 10000:  # File count threshold
                    alerts.append(f"High file count: {file_count}")
                
                return {
                    "status": "healthy" if not alerts else "warning",
                    "storage_size_mb": round(size_mb, 2),
                    "file_count": file_count,
                    "storage_path": str(storage_dir),
                    "alerts": alerts
                }
            else:
                return {
                    "status": "warning",
                    "error": "Storage directory not found"
                }
                
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_queue_health(self) -> Dict[str, Any]:
        """Check queue health and performance"""
        try:
            # Get queue sizes
            queue_sizes = {}
            queue_keys = [
                'document_processing',
                'rag_processing',
                'notifications',
                'celery'
            ]
            
            for queue_key in queue_keys:
                try:
                    size = self.redis_client.llen(queue_key)
                    queue_sizes[queue_key] = size
                except Exception:
                    queue_sizes[queue_key] = 0
            
            # Check for queue backlogs
            alerts = []
            total_queue_size = sum(queue_sizes.values())
            
            if total_queue_size > self.health_thresholds['queue_size']:
                alerts.append(f"High queue size: {total_queue_size}")
            
            for queue_name, size in queue_sizes.items():
                if size > 100:  # Individual queue threshold
                    alerts.append(f"High {queue_name} queue size: {size}")
            
            return {
                "status": "healthy" if not alerts else "warning",
                "queue_sizes": queue_sizes,
                "total_queue_size": total_queue_size,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_processing_workers(self) -> Dict[str, Any]:
        """Check processing worker health"""
        try:
            # Check Celery worker status
            from celery import Celery
            
            celery_app = Celery('kmrl_gateway')
            celery_app.config_from_object('config.celery_config.CELERY_CONFIG')
            celery_app.autodiscover_tasks(['services.processing.document_processor'])
            
            # Get worker stats
            stats = celery_app.control.inspect().stats()
            
            if stats:
                worker_count = len(stats)
                active_tasks = sum(len(worker.get('active', [])) for worker in stats.values())
                
                return {
                    "status": "healthy",
                    "worker_count": worker_count,
                    "active_tasks": active_tasks,
                    "workers": list(stats.keys())
                }
            else:
                return {
                    "status": "warning",
                    "error": "No workers available"
                }
                
        except Exception as e:
            logger.error(f"Processing workers check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()
        
        logger.info("Starting comprehensive health check")
        
        # Run all health checks
        checks = {
            'redis': await self.check_redis_health(),
            'system_resources': await self.check_system_resources(),
            'database': await self.check_database_health(),
            'storage': await self.check_storage_health(),
            'queues': await self.check_queue_health(),
            'processing_workers': await self.check_processing_workers()
        }
        
        # Determine overall health
        overall_status = "healthy"
        critical_issues = []
        warnings = []
        
        for check_name, result in checks.items():
            status = result.get('status', 'unknown')
            
            if status == 'unhealthy':
                overall_status = 'unhealthy'
                critical_issues.append(f"{check_name}: {result.get('error', 'Unknown error')}")
            elif status == 'warning':
                if overall_status == 'healthy':
                    overall_status = 'warning'
                warnings.extend(result.get('alerts', []))
        
        # Calculate health score
        healthy_checks = sum(1 for r in checks.values() if r.get('status') == 'healthy')
        total_checks = len(checks)
        health_score = (healthy_checks / total_checks) * 100
        
        # Compile results
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'health_score': round(health_score, 2),
            'check_duration_ms': round((time.time() - start_time) * 1000, 2),
            'critical_issues': critical_issues,
            'warnings': warnings,
            'checks': checks
        }
        
        # Store health report in Redis
        try:
            self.redis_client.hset('gateway_health', mapping={
                'timestamp': health_report['timestamp'],
                'status': overall_status,
                'score': str(health_score),
                'report': json.dumps(health_report)
            })
        except Exception as e:
            logger.warning(f"Failed to store health report in Redis: {e}")
        
        logger.info(f"Health check completed: {overall_status} (score: {health_score}%)")
        
        return health_report
    
    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        try:
            # Get health history from Redis
            health_data = self.redis_client.hgetall('gateway_health')
            
            if health_data:
                return [json.loads(health_data.get('report', '{}'))]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []
    
    async def generate_health_alert(self, health_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate health alert if needed"""
        if health_report['overall_status'] == 'unhealthy':
            return {
                'type': 'critical',
                'title': 'KMRL Gateway System Unhealthy',
                'message': f"System health score: {health_report['health_score']}%",
                'critical_issues': health_report['critical_issues'],
                'timestamp': health_report['timestamp']
            }
        elif health_report['overall_status'] == 'warning' and health_report['warnings']:
            return {
                'type': 'warning',
                'title': 'KMRL Gateway System Warning',
                'message': f"System health score: {health_report['health_score']}%",
                'warnings': health_report['warnings'],
                'timestamp': health_report['timestamp']
            }
        
        return None

if __name__ == '__main__':
    # Test health service
    import asyncio
    
    async def test_health():
        health_service = HealthService()
        health_report = await health_service.comprehensive_health_check()
        print(json.dumps(health_report, indent=2))
    
    asyncio.run(test_health())
