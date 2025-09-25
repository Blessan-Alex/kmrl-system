#!/usr/bin/env python3
"""
Simple KMRL System Startup
Starts just the gateway without complex worker management
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the KMRL system simply"""
    print("🚀 Starting KMRL System (Simple Mode)")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("gateway/app.py").exists():
        print("❌ Please run this from the kmrl-app/backend directory")
        return False
    
    # Start the gateway
    print("🌐 Starting Gateway...")
    try:
        # Start FastAPI gateway
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 'gateway.app:app',
            '--host', '0.0.0.0', '--port', '3000', '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print("\n🛑 Gateway stopped by user")
    except Exception as e:
        print(f"❌ Gateway failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
