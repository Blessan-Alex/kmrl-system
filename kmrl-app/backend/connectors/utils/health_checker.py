"""
Enhanced Health Checker for KMRL Connectors
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

class ConnectorHealthChecker:
    """Enhanced health checker for KMRL connector system"""
    
    def __init__(self):
        self.redis_client = self._connect_redis()
        self.api_endpoint = os.getenv('API_ENDPOINT', 'http://localhost:3000')
        self.health_thresholds = {
            'cpu_usage': 80.0,  # CPU usage threshold
            'memory_usage': 85.0,  # Memory usage threshold
            'disk_usage': 90.0,  # Disk usage threshold
            'response_time': 5.0,  # API response time threshold
            'error_rate': 10.0,  # Error rate threshold (%)
            'queue_size': 1000,  # Queue size threshold
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
    
    def check_redis_health(self) -> Dict[str, Any]:
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
            
            # Test set operations (for processed documents)
            test_set_key = f"health_check_set_{int(time.time())}"
            self.redis_client.sadd(test_set_key, "test_doc")
            assert self.redis_client.sismember(test_set_key, "test_doc")
            self.redis_client.delete(test_set_key)
            
            # Test hash operations (for connector state)
            test_hash_key = f"health_check_hash_{int(time.time())}"
            self.redis_client.hset(test_hash_key, "test_field", "test_value")
            assert self.redis_client.hget(test_hash_key, "test_field") == "test_value"
            self.redis_client.delete(test_hash_key)
            
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
    
    def check_system_resources(self) -> Dict[str, Any]:
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
    
    def check_api_gateway_health(self) -> Dict[str, Any]:
        """Check API gateway connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test health endpoint
            response = requests.get(
                f"{self.api_endpoint}/health",
                timeout=10
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "gateway_status": response.json().get('status', 'unknown')
                }
            else:
                return {
                    "status": "unhealthy",
                    "response_time_ms": round(response_time, 2),
                    "error": f"Gateway returned status {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "error": "Gateway timeout"
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "error": "Gateway connection failed"
            }
        except Exception as e:
            logger.error(f"API gateway health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "error": str(e)
            }
    
    def check_connector_health(self) -> Dict[str, Any]:
        """Check health of all connectors"""
        try:
            # Get connector health from Redis
            health_data = self.redis_client.hget('connector_health', 'status')
            
            if health_data:
                connector_status = json.loads(health_data)
                
                # Analyze connector status
                healthy_connectors = 0
                total_connectors = 0
                connector_alerts = []
                
                for connector_name, status in connector_status.items():
                    if isinstance(status, dict) and 'error' not in status:
                        healthy_connectors += 1
                    else:
                        connector_alerts.append(f"{connector_name}: {status.get('error', 'Unknown error')}")
                    total_connectors += 1
                
                return {
                    "status": "healthy" if healthy_connectors == total_connectors else "degraded",
                    "healthy_connectors": healthy_connectors,
                    "total_connectors": total_connectors,
                    "connector_status": connector_status,
                    "alerts": connector_alerts
                }
            else:
                return {
                    "status": "unknown",
                    "error": "No connector health data available"
                }
                
        except Exception as e:
            logger.error(f"Connector health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_queue_health(self) -> Dict[str, Any]:
        """Check queue health and performance"""
        try:
            # Get queue sizes
            queue_sizes = {}
            queue_keys = [
                'celery',
                'document_processing',
                'rag_processing',
                'notifications'
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
    
    def check_error_rates(self) -> Dict[str, Any]:
        """Check error rates and patterns"""
        try:
            # Get recent errors from Redis
            error_keys = [
                'sync_errors:gmail',
                'sync_errors:google_drive',
                'sync_errors:maximo',
                'sync_errors:whatsapp'
            ]
            
            total_errors = 0
            connector_errors = {}
            
            for error_key in error_keys:
                try:
                    errors = self.redis_client.lrange(error_key, 0, 99)  # Last 100 errors
                    error_count = len(errors)
                    connector_errors[error_key.split(':')[1]] = error_count
                    total_errors += error_count
                except Exception:
                    connector_errors[error_key.split(':')[1]] = 0
            
            # Calculate error rate (simplified)
            # In a real implementation, you'd track total operations
            error_rate = min(total_errors * 10, 100)  # Simplified calculation
            
            alerts = []
            if error_rate > self.health_thresholds['error_rate']:
                alerts.append(f"High error rate: {error_rate}%")
            
            for connector, errors in connector_errors.items():
                if errors > 10:  # Threshold for individual connector
                    alerts.append(f"High {connector} error count: {errors}")
            
            return {
                "status": "healthy" if not alerts else "warning",
                "total_errors": total_errors,
                "error_rate_percent": round(error_rate, 2),
                "connector_errors": connector_errors,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Error rate check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_storage_health(self) -> Dict[str, Any]:
        """Check storage health and capacity"""
        try:
            # Check downloads directory
            downloads_dir = Path('downloads')
            if downloads_dir.exists():
                # Get directory size
                total_size = 0
                file_count = 0
                
                for file_path in downloads_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                
                # Convert to MB
                size_mb = total_size / (1024 * 1024)
                
                # Check for storage issues
                alerts = []
                if size_mb > 1000:  # 1GB threshold
                    alerts.append(f"Large downloads directory: {size_mb:.2f}MB")
                
                if file_count > 10000:  # File count threshold
                    alerts.append(f"High file count: {file_count}")
                
                return {
                    "status": "healthy" if not alerts else "warning",
                    "downloads_size_mb": round(size_mb, 2),
                    "file_count": file_count,
                    "alerts": alerts
                }
            else:
                return {
                    "status": "warning",
                    "error": "Downloads directory not found"
                }
                
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        start_time = time.time()
        
        logger.info("Starting comprehensive health check")
        
        # Run all health checks
        checks = {
            'redis': self.check_redis_health(),
            'system_resources': self.check_system_resources(),
            'api_gateway': self.check_api_gateway_health(),
            'connectors': self.check_connector_health(),
            'queues': self.check_queue_health(),
            'error_rates': self.check_error_rates(),
            'storage': self.check_storage_health()
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
            self.redis_client.hset('system_health', mapping={
                'timestamp': health_report['timestamp'],
                'status': overall_status,
                'score': str(health_score),
                'report': json.dumps(health_report)
            })
        except Exception as e:
            logger.warning(f"Failed to store health report in Redis: {e}")
        
        logger.info(f"Health check completed: {overall_status} (score: {health_score}%)")
        
        return health_report
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        try:
            # This is a simplified implementation
            # In production, you'd store historical data in a time-series database
            current_health = self.comprehensive_health_check()
            
            return [current_health]
            
        except Exception as e:
            logger.error(f"Failed to get health history: {e}")
            return []
    
    def generate_health_alert(self, health_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate health alert if needed"""
        if health_report['overall_status'] == 'unhealthy':
            return {
                'type': 'critical',
                'title': 'KMRL Connector System Unhealthy',
                'message': f"System health score: {health_report['health_score']}%",
                'critical_issues': health_report['critical_issues'],
                'timestamp': health_report['timestamp']
            }
        elif health_report['overall_status'] == 'warning' and health_report['warnings']:
            return {
                'type': 'warning',
                'title': 'KMRL Connector System Warning',
                'message': f"System health score: {health_report['health_score']}%",
                'warnings': health_report['warnings'],
                'timestamp': health_report['timestamp']
            }
        
        return None

if __name__ == '__main__':
    # Test health checker
    checker = ConnectorHealthChecker()
    health_report = checker.comprehensive_health_check()
    print(json.dumps(health_report, indent=2))
