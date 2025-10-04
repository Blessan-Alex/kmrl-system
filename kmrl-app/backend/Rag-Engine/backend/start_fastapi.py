#!/usr/bin/env python3
"""
Startup script for the FastAPI RAG Backend Server
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Testing FastAPI dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✅ FastAPI dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements_fastapi.txt")
        return False

def check_opensearch():
    """Check if OpenSearch is running"""
    try:
        import requests
        response = requests.get('http://localhost:9200', timeout=5)
        if response.status_code == 200:
            print("✅ OpenSearch is running")
            return True
    except:
        pass
    
    print("❌ OpenSearch is not running")
    print("Please start OpenSearch: docker-compose up -d")
    return False

def main():
    """Main startup function"""
    print("🚀 Starting KMRM RAG FastAPI Backend Server")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return
    
    # Check OpenSearch
    opensearch_ok = check_opensearch()
    if not opensearch_ok:
        print("⚠️  Warning: OpenSearch not running. Some features may not work.")
    
    print("\n🌐 FastAPI Server Features:")
    print("   📚 Auto-generated API docs: http://localhost:8000/docs")
    print("   🔧 Interactive API testing: http://localhost:8000/redoc")
    print("   🌐 Web Interface: http://localhost:8000")
    print("   ❤️  Health Check: http://localhost:8000/api/health")
    print("\n🚀 Performance Improvements:")
    print("   ⚡ 2-3x faster than Flask")
    print("   🔄 Async operations for better I/O handling")
    print("   📝 Automatic API documentation")
    print("   🛡️  Type safety with Pydantic models")
    print("   🔍 Better error handling and validation")
    
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the FastAPI app
    try:
        from fastapi_app import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == "__main__":
    main()
