#!/bin/bash

# KMRM Development Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting KMRM Development Environment"
echo "======================================"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $1 is already in use"
        return 1
    else
        echo "✅ Port $1 is available"
        return 0
    fi
}

# Check if ports are available
echo "🔍 Checking port availability..."
check_port 8000 || exit 1
check_port 3000 || exit 1

# Start FastAPI backend
echo "🐍 Starting FastAPI Backend (Port 8000)..."
cd backend/Rag-Engine/backend
python fastapi_app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Next.js frontend
echo "⚛️  Starting Next.js Frontend (Port 3000)..."
cd ../../frontend/frnt-km
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Development servers started!"
echo "======================================"
echo "📚 FastAPI Backend: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo "💬 Chat Interface: http://localhost:3000/home/chat"
echo "======================================"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping development servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
