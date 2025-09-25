#!/usr/bin/env python3
"""
KMRL Connector System Startup Script
Starts Redis, Celery worker, and Celery beat scheduler for all connectors
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        redis_client.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis not available: {e}")
        return False

def start_redis():
    """Start Redis service"""
    try:
        print("🔄 Starting Redis service...")
        
        # Try to start Redis
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                         check=True, capture_output=True)
            print("✅ Redis started via systemctl")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to direct start
            subprocess.Popen(['redis-server', '--daemonize', 'yes'])
            print("✅ Redis started directly")
        
        # Wait and verify
        time.sleep(3)
        return check_redis()
        
    except Exception as e:
        print(f"❌ Failed to start Redis: {e}")
        return False

def main():
    """Start KMRL Connector System"""
    print("🚀 Starting KMRL Connector System")
    print("=" * 50)
    
    # Ensure directories exist
    directories = ['downloads', 'logs', 'temp']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Set up environment
    if not os.getenv('REDIS_URL'):
        os.environ['REDIS_URL'] = 'redis://localhost:6379'
    if not os.getenv('API_ENDPOINT'):
        os.environ['API_ENDPOINT'] = 'http://localhost:3000'
    
    processes = {}
    
    try:
        # 1. Check/Start Redis
        print("🔍 Checking Redis connection...")
        if not check_redis():
            if not start_redis():
                print("❌ Cannot start system without Redis")
                return False
        
        # 2. Start Celery worker
        print("⚡ Starting Celery worker...")
        worker_cmd = [
            sys.executable, '-m', 'celery', 
            '--app=tasks.celery_app',
            'worker', 
            '--loglevel=info',
            '--concurrency=2'
        ]
        
        worker_process = subprocess.Popen(worker_cmd)
        processes['celery_worker'] = worker_process
        
        # Wait and check
        time.sleep(3)
        if worker_process.poll() is None:
            print("✅ Celery worker started")
        else:
            print("❌ Celery worker failed to start")
            return False
        
        # 3. Start Celery beat scheduler
        print("⏰ Starting Celery beat scheduler...")
        beat_cmd = [
            sys.executable, '-m', 'celery', 
            '--app=tasks.celery_app',
            'beat', 
            '--loglevel=info'
        ]
        
        beat_process = subprocess.Popen(beat_cmd)
        processes['celery_beat'] = beat_process
        
        # Wait and check
        time.sleep(3)
        if beat_process.poll() is None:
            print("✅ Celery beat scheduler started")
        else:
            print("❌ Celery beat scheduler failed to start")
            return False
        
        print("\n🎉 KMRL Connector System started successfully!")
        print("📋 Services running:")
        print("  ✅ Redis")
        print("  ✅ Celery Worker")
        print("  ✅ Celery Beat Scheduler")
        
        print("\n📝 System Information:")
        print(f"  Redis URL: {os.getenv('REDIS_URL')}")
        print(f"  API Endpoint: {os.getenv('API_ENDPOINT')}")
        print(f"  Download Directory: {Path('downloads').absolute()}")
        
        print("\n🔄 Connectors will sync every 2 minutes")
        print("📊 Use Ctrl+C to stop the system")
        
        # Keep running
        while True:
            time.sleep(30)
            
            # Check if processes are still running
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"⚠️  {name} has stopped")
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping KMRL Connector System...")
        
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
