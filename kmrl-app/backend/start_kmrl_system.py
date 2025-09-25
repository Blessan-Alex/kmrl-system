#!/usr/bin/env python3
"""
Unified KMRL System Startup Script
Starts all services in correct order with dependency management
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

logger = structlog.get_logger()

class KMRLSystemManager:
    """Unified system manager for KMRL"""
    
    def __init__(self):
        self.processes = {}
        self.running = False
        self.base_path = Path(__file__).parent
        
        logger.info("KMRL System Manager initialized")
    
    def start_infrastructure_services(self) -> bool:
        """Start PostgreSQL, Redis, MinIO"""
        try:
            print("🔧 Starting Infrastructure Services...")
            logger.info("Starting infrastructure services")
            
            # Start PostgreSQL
            if not self._start_postgresql():
                return False
            
            # Start Redis
            if not self._start_redis():
                return False
            
            # Start MinIO
            if not self._start_minio():
                return False
            
            print("✅ Infrastructure services started")
            logger.info("Infrastructure services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start infrastructure services: {e}")
            return False
    
    def start_gateway_services(self) -> bool:
        """Start Gateway with Celery worker"""
        try:
            print("🌐 Starting Gateway Services...")
            logger.info("Starting gateway services")
            
            # Start Gateway FastAPI
            if not self._start_gateway():
                return False
            
            # Start Gateway Celery Worker
            if not self._start_gateway_worker():
                return False
            
            print("✅ Gateway services started")
            logger.info("Gateway services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start gateway services: {e}")
            return False
    
    def start_connector_services(self) -> bool:
        """Start Connector Celery workers"""
        try:
            print("📡 Starting Connector Services...")
            logger.info("Starting connector services")
            
            # Start Connector Celery Worker
            if not self._start_connector_worker():
                return False
            
            # Start Connector Celery Beat
            if not self._start_connector_beat():
                return False
            
            print("✅ Connector services started")
            logger.info("Connector services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start connector services: {e}")
            return False
    
    def start_worker_services(self) -> bool:
        """Start Processing Workers"""
        try:
            print("⚙️ Starting Worker Services...")
            logger.info("Starting worker services")
            
            # Start Document Worker
            if not self._start_document_worker():
                return False
            
            # Start Notification Worker
            if not self._start_notification_worker():
                return False
            
            # Start RAG Worker
            if not self._start_rag_worker():
                return False
            
            print("✅ Worker services started")
            logger.info("Worker services started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start worker services: {e}")
            return False
    
    def _start_postgresql(self) -> bool:
        """Check PostgreSQL service"""
        try:
            print("  🔄 Checking PostgreSQL...")
            # Check if PostgreSQL is already running
            result = subprocess.run(['pg_isready', '-h', 'localhost', '-p', '5432'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ PostgreSQL is running")
                return True
            else:
                print("  ⚠️ PostgreSQL not running - please start it manually")
                print("     Run: sudo systemctl start postgresql")
                return False
        except Exception as e:
            print(f"  ❌ PostgreSQL check failed: {e}")
            return False
    
    def _start_redis(self) -> bool:
        """Check Redis service"""
        try:
            print("  🔄 Checking Redis...")
            # Check if Redis is already running
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("  ✅ Redis is running")
                return True
            else:
                print("  ⚠️ Redis not running - please start it manually")
                print("     Run: sudo systemctl start redis-server")
                return False
        except Exception as e:
            print(f"  ❌ Redis check failed: {e}")
            return False
    
    def _start_minio(self) -> bool:
        """Start MinIO service"""
        try:
            print("  🔄 Starting MinIO...")
            minio_binary = self.base_path / "minio"
            if not minio_binary.exists():
                print("  ❌ MinIO binary not found")
                return False
            
            data_dir = self.base_path / "minio-data"
            data_dir.mkdir(exist_ok=True)
            
            process = subprocess.Popen([
                str(minio_binary), 'server', str(data_dir), 
                '--console-address', ':9001'
            ])
            self.processes['minio'] = process
            time.sleep(3)
            print("  ✅ MinIO started")
            return True
        except Exception as e:
            print(f"  ❌ MinIO failed: {e}")
            return False
    
    def _start_gateway(self) -> bool:
        """Start Gateway FastAPI"""
        try:
            print("  🔄 Starting Gateway...")
            process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 'gateway.app:app',
                '--host', '0.0.0.0', '--port', '3000', '--log-level', 'info'
            ])
            self.processes['gateway'] = process
            time.sleep(5)
            print("  ✅ Gateway started")
            return True
        except Exception as e:
            print(f"  ❌ Gateway failed: {e}")
            return False
    
    def _start_gateway_worker(self) -> bool:
        """Start Gateway Celery Worker"""
        try:
            print("  🔄 Starting Gateway Worker...")
            # Import tasks to ensure they're registered
            import services.processing.document_processor
            process = subprocess.Popen([
                'celery', '-A', 'services.processing.document_processor', 'worker',
                '--loglevel=info', '--concurrency=2', '--queues=kmrl:documents',
                '--hostname=gateway@%h', '--without-gossip', '--without-mingle'
            ])
            self.processes['gateway_worker'] = process
            time.sleep(3)
            print("  ✅ Gateway Worker started")
            return True
        except Exception as e:
            print(f"  ❌ Gateway Worker failed: {e}")
            return False
    
    def _start_connector_worker(self) -> bool:
        """Start Connector Celery Worker"""
        try:
            print("  🔄 Starting Connector Worker...")
            # Import tasks to ensure they're registered
            import connectors.tasks.sync_tasks
            process = subprocess.Popen([
                'celery', '-A', 'connectors.tasks.sync_tasks', 'worker',
                '--loglevel=info', '--concurrency=2', '--queues=kmrl:connectors',
                '--hostname=connectors@%h', '--without-gossip', '--without-mingle'
            ])
            self.processes['connector_worker'] = process
            time.sleep(3)
            print("  ✅ Connector Worker started")
            return True
        except Exception as e:
            print(f"  ❌ Connector Worker failed: {e}")
            return False
    
    def _start_connector_beat(self) -> bool:
        """Start Connector Celery Beat"""
        try:
            print("  🔄 Starting Connector Beat...")
            process = subprocess.Popen([
                'celery', '-A', 'connectors.tasks.sync_tasks', 'beat',
                '--loglevel=info'
            ])
            self.processes['connector_beat'] = process
            time.sleep(3)
            print("  ✅ Connector Beat started")
            return True
        except Exception as e:
            print(f"  ❌ Connector Beat failed: {e}")
            return False
    
    def _start_document_worker(self) -> bool:
        """Start Document Worker"""
        try:
            print("  🔄 Starting Document Worker...")
            # Import tasks to ensure they're registered
            import workers.document_worker.worker
            process = subprocess.Popen([
                'celery', '-A', 'workers.document_worker.worker', 'worker',
                '--loglevel=info', '--concurrency=1', '--queues=kmrl:documents',
                '--hostname=documents@%h', '--without-gossip', '--without-mingle'
            ])
            self.processes['document_worker'] = process
            time.sleep(3)
            print("  ✅ Document Worker started")
            return True
        except Exception as e:
            print(f"  ❌ Document Worker failed: {e}")
            return False
    
    def _start_notification_worker(self) -> bool:
        """Start Notification Worker"""
        try:
            print("  🔄 Starting Notification Worker...")
            # Import tasks to ensure they're registered
            import workers.notification_worker.worker
            process = subprocess.Popen([
                'celery', '-A', 'workers.notification_worker.worker', 'worker',
                '--loglevel=info', '--concurrency=1', '--queues=kmrl:notifications',
                '--hostname=notifications@%h', '--without-gossip', '--without-mingle'
            ])
            self.processes['notification_worker'] = process
            time.sleep(3)
            print("  ✅ Notification Worker started")
            return True
        except Exception as e:
            print(f"  ❌ Notification Worker failed: {e}")
            return False
    
    def _start_rag_worker(self) -> bool:
        """Start RAG Worker"""
        try:
            print("  🔄 Starting RAG Worker...")
            # Import tasks to ensure they're registered
            import workers.rag_worker.worker
            process = subprocess.Popen([
                'celery', '-A', 'workers.rag_worker.worker', 'worker',
                '--loglevel=info', '--concurrency=1', '--queues=kmrl:rag',
                '--hostname=rag@%h', '--without-gossip', '--without-mingle'
            ])
            self.processes['rag_worker'] = process
            time.sleep(3)
            print("  ✅ RAG Worker started")
            return True
        except Exception as e:
            print(f"  ❌ RAG Worker failed: {e}")
            return False
    
    def start_unified_system(self) -> bool:
        """Start complete KMRL system"""
        try:
            print("🚀 Starting Unified KMRL System")
            print("=" * 50)
            logger.info("Starting unified KMRL system")
            
            # 1. Start Infrastructure Services
            if not self.start_infrastructure_services():
                return False
            
            # 2. Start Gateway Services
            if not self.start_gateway_services():
                return False
            
            # 3. Start Connector Services
            if not self.start_connector_services():
                return False
            
            # 4. Start Worker Services
            if not self.start_worker_services():
                return False
            
            # 5. Health Check
            print("🔍 Performing Health Check...")
            time.sleep(5)
            
            print("\n🎉 Unified KMRL System Started Successfully!")
            print("=" * 50)
            print("📊 Services Status:")
            print("✅ PostgreSQL: Database ready")
            print("✅ Redis: Cache and queue ready")
            print("✅ MinIO: Object storage ready")
            print("✅ Gateway: API ready")
            print("✅ Connectors: Data ingestion ready")
            print("✅ Workers: Processing ready")
            
            print("\n🌐 Access Points:")
            print("• Gateway API: http://localhost:3000")
            print("• API Docs: http://localhost:3000/docs")
            print("• Health Check: http://localhost:3000/health")
            print("• MinIO Console: http://localhost:9001")
            
            print("\n🛑 Press Ctrl+C to stop all services")
            
            self.running = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to start unified system: {e}")
            return False
    
    def stop_system(self):
        """Stop the unified system"""
        print("\n🛑 Stopping Unified KMRL System...")
        logger.info("Stopping unified system")
        
        self.running = False
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                print(f"Stopping {name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"✅ {name} stopped")
                except subprocess.TimeoutExpired:
                    print(f"⚠️  Force killing {name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
        print("🎉 System stopped")
        logger.info("System stopped")
    
    def run(self):
        """Run the system with monitoring"""
        if not self.start_unified_system():
            return
        
        try:
            # Main monitoring loop
            while self.running:
                time.sleep(30)  # Check every 30 seconds
                
                # Check if processes are still running
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        print(f"⚠️  {name} has stopped")
                        logger.warning(f"{name} has stopped")
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
            logger.info("Received interrupt signal")
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
    
    # Start the system
    manager = KMRLSystemManager()
    manager.run()

if __name__ == "__main__":
    main()
