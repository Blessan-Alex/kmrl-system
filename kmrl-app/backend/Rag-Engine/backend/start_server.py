#!/usr/bin/env python3
"""
Startup script for the RAG Backend Server
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_cors
        import google.generativeai
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
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
    print("🚀 Starting KMRM RAG Backend Server")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check OpenSearch
    if not check_opensearch():
        print("⚠️  Warning: OpenSearch not running. Some features may not work.")
    
    print("\n🌐 Starting Flask server...")
    print("📱 Frontend will be available at: http://localhost:5000")
    print("🔧 API endpoints:")
    print("   - GET  /api/health")
    print("   - POST /api/query")
    print("   - GET  /api/departments")
    print("   - GET  /api/stats")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the Flask app
    try:
        from app import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

if __name__ == '__main__':
    main()
