#!/usr/bin/env python3
"""
FastAPI RAG Backend with Gemini 2.0 Flash Integration
Modern, fast, and async-enabled RAG system
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import google.generativeai as genai
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensearch_query_processor import OpenSearchQueryProcessor
from query_to_embedding import query_to_embedding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Initialize FastAPI app
app = FastAPI(
    title="KMRM RAG API",
    description="Retrieval-Augmented Generation API with Gemini 2.0 Flash and OpenSearch",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCn10Dq_CBqwllD3R3Qt8oh2VLIZkrpbCY"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model (Gemini 2.0 Flash)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Global variables
opensearch_processor = None
executor = ThreadPoolExecutor(max_workers=4)

# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="The search query")
    department: Optional[str] = Field(None, description="Department filter")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to return")
    search_type: str = Field("vector", pattern="^(vector|text|hybrid)$", description="Search type")

class QueryResponse(BaseModel):
    query: str
    response: str
    context_documents: List[Dict[str, Any]]
    search_time: float
    total_documents_searched: int
    department_filter: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    opensearch_connected: bool
    gemini_configured: bool
    total_documents: int = 0

class StatsResponse(BaseModel):
    opensearch_stats: Dict[str, Any]
    gemini_model: str
    embedding_model: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global opensearch_processor
    try:
        opensearch_processor = OpenSearchQueryProcessor()
        logging.info("✅ OpenSearch connected successfully")
    except Exception as e:
        logging.error(f"❌ OpenSearch connection failed: {e}")
        opensearch_processor = None

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    executor.shutdown(wait=True)

# Async helper functions
async def generate_embedding_async(query: str) -> List[float]:
    """Generate embedding asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, query_to_embedding, query)

async def search_documents_async(query: str, top_k: int = 5, department: str = None) -> List[Dict[str, Any]]:
    """Search documents asynchronously"""
    if not opensearch_processor:
        raise HTTPException(status_code=503, detail="OpenSearch not available")
    
    try:
        # Generate query embedding
        query_embedding = await generate_embedding_async(query)
        
        # Search OpenSearch
        results = opensearch_processor.search_by_embedding(
            query_embedding, 
            size=top_k, 
            department=department
        )
        
        return results
    except Exception as e:
        logging.error(f"Document search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

async def generate_gemini_response_async(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """Generate Gemini response asynchronously"""
    try:
        # Prepare context from retrieved documents
        context_text = "\n\n".join([
            f"Document {i+1}: {doc.get('text', '')[:500]}..."
            for i, doc in enumerate(context_documents[:3])  # Use top 3 documents
        ])
        
        # Create prompt for Gemini
        prompt = f"""
You are a helpful assistant for a metro/railway management system (KMRM). 
Based on the following context documents, please provide a comprehensive and accurate answer to the user's question.

Context Documents:
{context_text}

User Question: {query}

Instructions:
1. If the user’s question is written in Malayalam, respond entirely in Malayalam with a translated section of the same.
2. If the user’s question is written in English, respond entirely in English.
3. If the context documents do not have enough information, do NOT leave the answer empty. 
   - Clearly mention that some details are missing.
   - Still provide a meaningful, helpful response by adding reasonable background knowledge or best practices for metro/railway management.
4. Always give a detailed, well-structured response that:
   - Directly answers the user’s question
   - Uses information from the context documents (when available)
   - Is specific to metro/railway operations
   - Includes relevant details, steps, or examples where appropriate
"""
        
        # Generate response with Gemini (run in thread pool)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(executor, lambda: model.generate_content(prompt))
        
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini response generation failed: {e}")
        return f"Error generating response: {str(e)}"

# API Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main frontend page"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>RAG API is running!</h1><p>Visit /docs for API documentation</p>")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        total_docs = 0
        opensearch_connected = False
        
        if opensearch_processor:
            try:
                # Test OpenSearch connection
                stats = opensearch_processor.get_index_stats()
                total_docs = stats.get('total_documents', 0)
                opensearch_connected = True
            except Exception as e:
                logging.warning(f"OpenSearch health check failed: {e}")
                opensearch_connected = False
        
        return HealthResponse(
            status="healthy",
            opensearch_connected=opensearch_connected,
            gemini_configured=GEMINI_API_KEY is not None,
            total_documents=total_docs
        )
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            opensearch_connected=False,
            gemini_configured=False,
            total_documents=0
        )

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process RAG query with Gemini summarization"""
    try:
        start_time = time.time()
        
        # Step 1: Search for similar documents
        logging.info(f"Searching for documents related to: '{request.query}'")
        similar_docs = await search_documents_async(
            request.query, 
            request.top_k, 
            request.department
        )
        
        if not similar_docs:
            return QueryResponse(
                query=request.query,
                response="No relevant documents found in the knowledge base.",
                context_documents=[],
                search_time=time.time() - start_time,
                total_documents_searched=0,
                department_filter=request.department
            )
        
        # Step 2: Generate summary with Gemini
        logging.info(f"Generating response with Gemini for query: '{request.query}'")
        summary = await generate_gemini_response_async(request.query, similar_docs)
        
        total_time = time.time() - start_time
        
        # Format context documents
        context_docs = [
            {
                'document_id': doc.get('document_id', 'Unknown'),
                'chunk_index': doc.get('chunk_index', 0),
                'text': doc.get('text', '')[:200] + '...',
                'similarity_score': doc.get('similarity_score', 0),
                'department': doc.get('metadata', {}).get('department', 'Unknown')
            }
            for doc in similar_docs
        ]
        
        logging.info(f"Query processed successfully in {total_time:.2f} seconds")
        
        return QueryResponse(
            query=request.query,
            response=summary,
            context_documents=context_docs,
            search_time=total_time,
            total_documents_searched=len(similar_docs),
            department_filter=request.department
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/api/departments")
async def get_departments():
    """Get available departments"""
    try:
        if not opensearch_processor:
            raise HTTPException(status_code=503, detail="OpenSearch not connected")
        
        departments = opensearch_processor.search_departments()
        
        # Fallback if no departments found or error
        if not departments:
            logging.warning("No departments found in OpenSearch, using default list")
            departments = ["general", "operations", "finance", "hr", "planning", "accounts", "engineering", "maintenance"]
        
        return {"departments": departments}
        
    except Exception as e:
        logging.error(f"Failed to get departments: {e}")
        # Return default departments as fallback
        return {"departments": ["general", "operations", "finance", "hr", "planning", "accounts", "engineering", "maintenance"]}

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    try:
        if not opensearch_processor:
            raise HTTPException(status_code=503, detail="OpenSearch not connected")
        
        stats = opensearch_processor.get_index_stats()
        return StatsResponse(
            opensearch_stats=stats,
            gemini_model="gemini-2.0-flash-exp",
            embedding_model="krutrim-ai-labs/vyakyarth"
        )
        
    except Exception as e:
        logging.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """Convert audio file to text using Gemini's audio capabilities"""
    try:
        # Check if file is audio
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read the audio file
        audio_data = await file.read()
        
        # Use Gemini to transcribe the audio
        try:
            # Create a temporary file-like object for Gemini
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = file.filename or "audio.webm"
            
            # Use Gemini's audio transcription
            response = model.generate_content([
                "Please transcribe this audio file to text. Return only the transcribed text without any additional formatting or explanations.",
                audio_file
            ])
            
            transcription = response.text.strip()
            
            if not transcription:
                raise HTTPException(status_code=400, detail="Could not transcribe audio. Please try again.")
            
            return {"text": transcription}
            
        except Exception as e:
            logging.error(f"Gemini transcription failed: {e}")
            raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Speech-to-text error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error"}

def main():
    """Main function to start the server"""
    print("🚀 Starting KMRM RAG FastAPI Server")
    print("=" * 50)
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 Web Interface: http://localhost:8000")
    print("🔧 Health Check: http://localhost:8000/api/health")
    print("=" * 50)
    
    import uvicorn
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
