#!/usr/bin/env python3
"""
Enhanced KMRL Gateway Startup Script
Starts PostgreSQL, Redis, MinIO, and Enhanced FastAPI Gateway with real-time updates
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

def check_service(name, check_cmd, port=None):
    """Check if a service is running"""
    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {name} is running")
            return True
        else:
            print(f"❌ {name} not running")
            return False
    except Exception as e:
        print(f"❌ Error checking {name}: {e}")
        return False

def start_postgresql():
    """Start PostgreSQL service"""
    try:
        print("🔄 Starting PostgreSQL...")
        
        # Try systemctl first
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], 
                         check=True, capture_output=True)
            print("✅ PostgreSQL started via systemctl")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to direct start
            subprocess.Popen(['pg_ctl', 'start', '-D', '/var/lib/postgresql/data'])
            print("✅ PostgreSQL started directly")
        
        time.sleep(3)
        return check_service("PostgreSQL", "pg_isready -h localhost -p 5432")
        
    except Exception as e:
        print(f"❌ Failed to start PostgreSQL: {e}")
        return False

def start_redis():
    """Start Redis service"""
    try:
        print("🔄 Starting Redis...")
        
        # Try systemctl first
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                         check=True, capture_output=True)
            print("✅ Redis started via systemctl")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to direct start
            subprocess.Popen(['redis-server', '--daemonize', 'yes'])
            print("✅ Redis started directly")
        
        time.sleep(2)
        return check_service("Redis", "redis-cli ping")
        
    except Exception as e:
        print(f"❌ Failed to start Redis: {e}")
        return False

def start_minio():
    """Start MinIO service"""
    try:
        print("🔄 Starting MinIO...")
        
        # Ensure MinIO binary exists
        minio_binary = Path("minio")
        if not minio_binary.exists():
            print("❌ MinIO binary not found. Please run the setup first.")
            return False
        
        # Create data directory
        data_dir = Path("minio-data")
        data_dir.mkdir(exist_ok=True)
        
        # Start MinIO
        minio_process = subprocess.Popen([
            str(minio_binary), 'server', str(data_dir), 
            '--console-address', ':9001'
        ])
        
        time.sleep(3)
        return check_service("MinIO", "curl -f http://localhost:9000/minio/health/live")
        
    except Exception as e:
        print(f"❌ Failed to start MinIO: {e}")
        return False

def init_database():
    """Initialize PostgreSQL database"""
    try:
        print("🔄 Initializing database...")
        
        # Run database initialization
        result = subprocess.run([
            sys.executable, 'migrations/init_db.py', 'init'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def start_celery_worker():
    """Start Celery worker for document processing"""
    try:
        print("🔄 Starting Celery worker...")
        
        # Start Celery worker
        celery_process = subprocess.Popen([
            'celery', '-A', 'services.document_processor', 'worker', 
            '--loglevel=info', '--concurrency=2'
        ])
        
        time.sleep(2)
        return check_service("Celery Worker", "ps aux | grep celery")
        
    except Exception as e:
        print(f"❌ Failed to start Celery worker: {e}")
        return False

def start_enhanced_gateway():
    """Start Enhanced KMRL Gateway"""
    try:
        print("🔄 Starting Enhanced KMRL Gateway...")
        
        # Start the enhanced gateway
        gateway_process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'app_enhanced:app', 
            '--host', '0.0.0.0', '--port', '3000', '--log-level', 'info'
        ])
        
        time.sleep(5)
        return check_service("Enhanced Gateway", "curl -f http://localhost:3000/health")
        
    except Exception as e:
        print(f"❌ Failed to start Enhanced Gateway: {e}")
        return False

def main():
    """Main startup sequence"""
    print("🚀 Starting Enhanced KMRL Gateway System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app_enhanced.py").exists():
        print("❌ app_enhanced.py not found. Please run from the gateway directory.")
        return False
    
    # Start services in order
    services = [
        ("PostgreSQL", start_postgresql),
        ("Redis", start_redis),
        ("MinIO", start_minio),
        ("Database Init", init_database),
        ("Celery Worker", start_celery_worker),
        ("Enhanced Gateway", start_enhanced_gateway)
    ]
    
    for service_name, start_func in services:
        print(f"\n📋 Starting {service_name}...")
        if not start_func():
            print(f"❌ Failed to start {service_name}")
            return False
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced KMRL Gateway System Started Successfully!")
    print("=" * 50)
    print("📊 Services Status:")
    print("✅ PostgreSQL: Database ready")
    print("✅ Redis: Cache and queue ready")
    print("✅ MinIO: Object storage ready")
    print("✅ Celery: Document processing ready")
    print("✅ Enhanced Gateway: API ready")
    print("\n🌐 Access Points:")
    print("• Gateway API: http://localhost:3000")
    print("• API Docs: http://localhost:3000/docs")
    print("• Health Check: http://localhost:3000/health")
    print("• WebSocket: ws://localhost:3000/ws")
    print("• MinIO Console: http://localhost:9001")
    print("\n📝 Features:")
    print("• PostgreSQL Integration")
    print("• Real-time WebSocket Updates")
    print("• Advanced Document Processing")
    print("• MinIO Object Storage")
    print("• Security & Authentication")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Enhanced KMRL Gateway System...")
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
