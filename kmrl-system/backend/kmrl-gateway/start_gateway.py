#!/usr/bin/env python3
"""
KMRL Gateway System Startup Script
Starts MinIO, PostgreSQL, Redis, and FastAPI Gateway
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
        
        # Ensure data directory exists
        data_dir = Path("minio-data")
        data_dir.mkdir(exist_ok=True)
        
        # Set MinIO environment variables
        env = os.environ.copy()
        env['MINIO_ROOT_USER'] = 'minioadmin'
        env['MINIO_ROOT_PASSWORD'] = 'minioadmin'
        
        # Start MinIO
        cmd = [
            str(minio_binary), 'server', 
            str(data_dir), 
            '--console-address', ':9001'
        ]
        
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        time.sleep(5)
        
        # Check if MinIO is running
        if check_service("MinIO", "curl -s http://localhost:9000/minio/health/live"):
            return True, process
        else:
            process.terminate()
            return False, None
            
    except Exception as e:
        print(f"❌ Failed to start MinIO: {e}")
        return False, None

def start_postgresql():
    """Start PostgreSQL service"""
    try:
        print("🔄 Starting PostgreSQL...")
        
        # Try to start PostgreSQL
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'postgresql'], 
                         check=True, capture_output=True)
            print("✅ PostgreSQL started via systemctl")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  PostgreSQL systemctl not available, assuming it's running")
        
        time.sleep(2)
        return check_service("PostgreSQL", "pg_isready")
        
    except Exception as e:
        print(f"❌ Failed to start PostgreSQL: {e}")
        return False

def start_gateway():
    """Start FastAPI Gateway"""
    try:
        print("🔄 Starting FastAPI Gateway...")
        
        # Check if app.py exists
        if not Path("app.py").exists():
            print("❌ app.py not found. Please run from gateway directory.")
            return False, None
        
        # Start the gateway
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "3000", 
            "--log-level", "info"
        ]
        
        process = subprocess.Popen(cmd)
        
        # Wait for startup
        time.sleep(5)
        
        # Check if gateway is running
        if check_service("Gateway", "curl -s http://localhost:3000/health"):
            return True, process
        else:
            process.terminate()
            return False, None
            
    except Exception as e:
        print(f"❌ Failed to start Gateway: {e}")
        return False, None

def main():
    """Start KMRL Gateway System"""
    print("🚀 Starting KMRL Gateway System")
    print("=" * 50)
    
    # Ensure directories exist
    directories = ['storage', 'logs', 'minio-data']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Set up environment
    if not os.getenv('REDIS_URL'):
        os.environ['REDIS_URL'] = 'redis://localhost:6379'
    if not os.getenv('MINIO_ENDPOINT'):
        os.environ['MINIO_ENDPOINT'] = 'localhost:9000'
    if not os.getenv('MINIO_ACCESS_KEY'):
        os.environ['MINIO_ACCESS_KEY'] = 'minioadmin'
    if not os.getenv('MINIO_SECRET_KEY'):
        os.environ['MINIO_SECRET_KEY'] = 'minioadmin'
    
    processes = {}
    
    try:
        # 1. Start Redis
        print("🔍 Starting Redis...")
        if not start_redis():
            print("❌ Cannot start system without Redis")
            return False
        
        # 2. Start MinIO
        print("🔍 Starting MinIO...")
        minio_success, minio_process = start_minio()
        if minio_success:
            processes['minio'] = minio_process
        else:
            print("⚠️  MinIO failed to start, will use local storage")
        
        # 3. Start PostgreSQL
        print("🔍 Starting PostgreSQL...")
        if not start_postgresql():
            print("⚠️  PostgreSQL failed to start, will use Redis for metadata")
        
        # 4. Start Gateway
        print("🔍 Starting Gateway...")
        gateway_success, gateway_process = start_gateway()
        if not gateway_success:
            print("❌ Cannot start system without Gateway")
            return False
        processes['gateway'] = gateway_process
        
        print("\n🎉 KMRL Gateway System started successfully!")
        print("📋 Services running:")
        print("  ✅ Redis")
        if 'minio' in processes:
            print("  ✅ MinIO")
        else:
            print("  ⚠️  MinIO (using local storage)")
        print("  ✅ PostgreSQL (or Redis fallback)")
        print("  ✅ FastAPI Gateway")
        
        print("\n📝 System Information:")
        print(f"  Gateway: http://localhost:3000")
        print(f"  Health Check: http://localhost:3000/health")
        print(f"  API Docs: http://localhost:3000/docs")
        print(f"  MinIO Console: http://localhost:9001")
        print(f"  Redis URL: {os.getenv('REDIS_URL')}")
        
        print("\n📊 Use Ctrl+C to stop the system")
        
        # Keep running and monitor
        while True:
            time.sleep(30)
            
            # Check if processes are still running
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"⚠️  {name} has stopped")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping KMRL Gateway System...")
        
        # Stop all processes
        for name, process in processes.items():
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
        
        print("🎉 System stopped")
        return True
    
    except Exception as e:
        print(f"❌ Failed to start system: {e}")
        return False

if __name__ == "__main__":
    main()