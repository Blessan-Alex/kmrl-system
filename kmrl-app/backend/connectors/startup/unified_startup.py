#!/usr/bin/env python3
"""
Start Unified KMRL Connector System
Starts all connectors with Celery task scheduling
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = structlog.get_logger()

class UnifiedSystemManager:
    """Manages the unified KMRL connector system"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        
        # Ensure required directories exist
        self.ensure_directories()
        
        logger.info("Unified system manager initialized")
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            'downloads',
            'logs',
            'temp'
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def check_redis(self) -> bool:
        """Check if Redis is running"""
        try:
            import redis
            redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
            redis_client.ping()
            logger.info("✅ Redis is running")
            return True
        except Exception as e:
            logger.error(f"❌ Redis not available: {e}")
            return False
    
    def start_redis(self) -> bool:
        """Start Redis service"""
        try:
            logger.info("Starting Redis service...")
            
            # Try to start Redis
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                             check=True, capture_output=True)
                logger.info("✅ Redis started via systemctl")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to direct start
                subprocess.Popen(['redis-server', '--daemonize', 'yes'])
                logger.info("✅ Redis started directly")
            
            # Wait a moment and verify
            time.sleep(2)
            return self.check_redis()
            
        except Exception as e:
            logger.error(f"❌ Failed to start Redis: {e}")
            return False
    
    def start_celery_worker(self) -> bool:
        """Start Celery worker"""
        try:
            print("⚡ Starting Celery worker...")
            logger.info("Starting Celery worker...")
            
            cmd = [
                sys.executable, '-m', 'celery', 
                '--app=tasks.celery_app',
                'worker', 
                '--loglevel=info',
                '--concurrency=2'
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['celery_worker'] = process
            
            # Wait a moment and check if it's still running
            time.sleep(3)
            if process.poll() is None:
                print("✅ Celery worker started successfully")
                logger.info("✅ Celery worker started")
                return True
            else:
                stdout, stderr = process.communicate()
                error_msg = stderr.decode()
                print(f"❌ Celery worker failed to start: {error_msg}")
                logger.error(f"❌ Celery worker failed to start: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Celery worker: {e}")
            return False
    
    def start_celery_beat(self) -> bool:
        """Start Celery beat scheduler"""
        try:
            logger.info("Starting Celery beat scheduler...")
            
            cmd = [
                sys.executable, '-m', 'celery', 
                '--app=tasks.celery_app',
                'beat', 
                '--loglevel=info'
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['celery_beat'] = process
            
            # Wait a moment and check if it's still running
            time.sleep(3)
            if process.poll() is None:
                logger.info("✅ Celery beat scheduler started")
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"❌ Celery beat scheduler failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Celery beat scheduler: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start system monitoring"""
        try:
            logger.info("Starting system monitoring...")
            
            # Create a simple monitoring script
            monitor_script = '''
import time
import redis
import os
from datetime import datetime

def monitor_system():
    redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
    
    while True:
        try:
            # Check Redis connection
            redis_client.ping()
            
            # Check connector health
            health_data = redis_client.hget('connector_health', 'status')
            if health_data:
                print(f"[{datetime.now()}] Health check data available")
            
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"[{datetime.now()}] Monitoring error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_system()
'''
            
            monitor_file = Path('temp/monitor.py')
            with open(monitor_file, 'w') as f:
                f.write(monitor_script)
            
            cmd = [sys.executable, str(monitor_file)]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes['monitor'] = process
            
            logger.info("✅ System monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")
            return False
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health = {
            'timestamp': time.time(),
            'services': {},
            'overall': 'unknown'
        }
        
        # Check Redis
        health['services']['redis'] = self.check_redis()
        
        # Check Celery processes
        for process_name, process in self.processes.items():
            if process.poll() is None:
                health['services'][process_name] = True
            else:
                health['services'][process_name] = False
        
        # Determine overall health
        all_services_healthy = all(health['services'].values())
        if all_services_healthy:
            health['overall'] = 'healthy'
        else:
            health['overall'] = 'degraded'
        
        return health
    
    def start_system(self) -> bool:
        """Start the unified system"""
        try:
            print("🚀 Starting Unified KMRL Connector System")
            print("=" * 60)
            logger.info("🚀 Starting Unified KMRL Connector System")
            logger.info("=" * 60)
            
            # Check/start Redis
            print("🔍 Checking Redis connection...")
            if not self.check_redis():
                print("🔄 Starting Redis service...")
                if not self.start_redis():
                    print("❌ Cannot start system without Redis")
                    logger.error("❌ Cannot start system without Redis")
                    return False
            
            # Start Celery worker
            print("⚡ Starting Celery worker...")
            if not self.start_celery_worker():
                print("❌ Failed to start Celery worker")
                logger.error("❌ Failed to start Celery worker")
                return False
            
            # Start Celery beat scheduler
            print("⏰ Starting Celery beat scheduler...")
            if not self.start_celery_beat():
                print("❌ Failed to start Celery beat scheduler")
                logger.error("❌ Failed to start Celery beat scheduler")
                return False
            
            # Start monitoring
            print("📊 Starting system monitoring...")
            if not self.start_monitoring():
                print("⚠️  Failed to start monitoring (non-critical)")
                logger.warning("⚠️  Failed to start monitoring (non-critical)")
            
            self.running = True
            
            # Initial health check
            print("🔍 Performing initial health check...")
            time.sleep(5)
            health = self.check_system_health()
            
            print("\n🎉 Unified system started successfully!")
            print(f"📊 System health: {health['overall']}")
            print("📋 Services running:")
            for service, status in health['services'].items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {service}")
            
            print("\n📝 System Information:")
            print(f"  Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
            print(f"  API Endpoint: {os.getenv('API_ENDPOINT', 'http://localhost:3000')}")
            print(f"  OAuth2 Port: {os.getenv('OAUTH2_REDIRECT_PORT', '8080')}")
            print(f"  Download Directory: {Path('downloads').absolute()}")
            
            print("\n🔄 Connectors will sync every 2 minutes")
            print("📊 Use Ctrl+C to stop the system")
            
            logger.info("🎉 Unified system started successfully!")
            logger.info(f"📊 System health: {health['overall']}")
            logger.info("📋 Services running:")
            for service, status in health['services'].items():
                status_icon = "✅" if status else "❌"
                logger.info(f"  {status_icon} {service}")
            
            logger.info("\n📝 System Information:")
            logger.info(f"  Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
            logger.info(f"  API Endpoint: {os.getenv('API_ENDPOINT', 'http://localhost:3000')}")
            logger.info(f"  OAuth2 Port: {os.getenv('OAUTH2_REDIRECT_PORT', '8080')}")
            logger.info(f"  Download Directory: {Path('downloads').absolute()}")
            
            logger.info("\n🔄 Connectors will sync every 2 minutes")
            logger.info("📊 Use Ctrl+C to stop the system")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start unified system: {e}")
            return False
    
    def stop_system(self):
        """Stop the unified system"""
        logger.info("🛑 Stopping Unified KMRL Connector System")
        
        self.running = False
        
        # Stop all processes
        for process_name, process in self.processes.items():
            try:
                logger.info(f"Stopping {process_name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"✅ {process_name} stopped")
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️  Force killing {process_name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                logger.error(f"❌ Error stopping {process_name}: {e}")
        
        self.processes.clear()
        logger.info("🎉 System stopped")
    
    def run(self):
        """Run the system with monitoring"""
        if not self.start_system():
            return
        
        try:
            # Main monitoring loop
            while self.running:
                time.sleep(30)  # Check every 30 seconds
                
                # Check system health
                health = self.check_system_health()
                
                if health['overall'] == 'degraded':
                    logger.warning("⚠️  System health degraded")
                    for service, status in health['services'].items():
                        if not status:
                            logger.warning(f"  ❌ {service} is down")
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Received interrupt signal")
        finally:
            self.stop_system()

def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)

def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Start the system
    manager = UnifiedSystemManager()
    manager.run()

if __name__ == "__main__":
    main()
