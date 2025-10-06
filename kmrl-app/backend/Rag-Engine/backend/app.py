#!/usr/bin/env python3
"""
RAG Backend API with Gemini 2.0 Flash Integration
"""

import os
import sys
import json
import time
import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opensearch_query_processor import OpenSearchQueryProcessor
from query_to_embedding import query_to_embedding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCn10Dq_CBqwllD3R3Qt8oh2VLIZkrpbCY"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model (Gemini 2.0 Flash)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Initialize OpenSearch processor
opensearch_processor = None

def initialize_opensearch():
    """Initialize OpenSearch connection"""
    global opensearch_processor
    try:
        opensearch_processor = OpenSearchQueryProcessor()
        # Test connection
        try:
            stats = opensearch_processor.get_index_stats()
            logging.info(f"OpenSearch connected: {stats.get('total_documents', 0)} documents")
        except Exception as e:
            logging.warning(f"Index stats failed: {e}")
            logging.info("OpenSearch connected but index may be empty")
        return True
    except Exception as e:
        logging.error(f"OpenSearch connection failed: {e}")
        return False

def generate_embedding(query: str) -> List[float]:
    """Generate embedding for query using krutrim-ai-labs/vyakyarth"""
    try:
        return query_to_embedding(query)
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        raise

def search_similar_documents(query: str, top_k: int = 5, department: str = None, search_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Search for similar documents using improved search methods"""
    try:
        if not opensearch_processor:
            raise Exception("OpenSearch not initialized")
        
        # Generate query embedding
        query_embedding = generate_embedding(query)
        
        if search_type == "hybrid":
            # Use hybrid search (vector + text)
            results = opensearch_processor.hybrid_search(
                query, 
                query_embedding, 
                size=top_k, 
                department=department
            )
        elif search_type == "vector":
            # Use improved vector search with normalization
            results = opensearch_processor.improved_vector_search(
                query_embedding, 
                size=top_k, 
                department=department
            )
        else:
            # Fallback to original search
            results = opensearch_processor.search_by_embedding(
                query_embedding, 
                size=top_k, 
                department=department
            )
        
        return results
    except Exception as e:
        logging.error(f"Document search failed: {e}")
        return []

def generate_summary_with_gemini(query: str, context_documents: List[Dict[str, Any]]) -> str:
    """Generate summary using Gemini 2.0 Flash"""
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

Please provide a detailed, well-structured response that:
1. Directly answers the user's question
2. Uses information from the context documents
3. Is specific to metro/railway operations
4. Includes relevant details and examples where appropriate

If the context doesn't contain enough information to fully answer the question, please mention this and provide what information is available.
"""
        
        # Generate response with Gemini
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        logging.error(f"Gemini response generation failed: {e}")
        return f"Error generating response: {str(e)}"

@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'opensearch_connected': opensearch_processor is not None,
        'gemini_configured': GEMINI_API_KEY is not None
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process RAG query with Gemini summarization"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        department = data.get('department', None)
        top_k = data.get('top_k', 5)
        search_type = data.get('search_type', 'hybrid')  # Default to hybrid search
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        start_time = time.time()
        
        # Step 1: Search for similar documents using improved search
        logging.info(f"Searching for documents related to: '{query}' using {search_type} search")
        similar_docs = search_similar_documents(query, top_k, department, search_type)
        
        if not similar_docs:
            return jsonify({
                'query': query,
                'response': 'No relevant documents found in the knowledge base.',
                'context_documents': [],
                'search_time': time.time() - start_time,
                'total_documents_searched': 0
            })
        
        # Step 2: Generate summary with Gemini
        logging.info(f"Generating response with Gemini for query: '{query}'")
        summary = generate_summary_with_gemini(query, similar_docs)
        
        total_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            'query': query,
            'response': summary,
            'search_type': search_type,
            'context_documents': [
                {
                    'document_id': doc.get('document_id', 'Unknown'),
                    'chunk_index': doc.get('chunk_index', 0),
                    'text': doc.get('text', '')[:200] + '...',
                    'similarity_score': doc.get('similarity_score', 0),
                    'department': doc.get('metadata', {}).get('department', 'Unknown')
                }
                for doc in similar_docs
            ],
            'search_time': total_time,
            'total_documents_searched': len(similar_docs),
            'department_filter': department
        }
        
        logging.info(f"Query processed successfully in {total_time:.2f} seconds")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Query processing failed: {e}")
        return jsonify({'error': f'Query processing failed: {str(e)}'}), 500

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get available departments"""
    try:
        if not opensearch_processor:
            return jsonify({'error': 'OpenSearch not connected'}), 500
        
        departments = opensearch_processor.search_departments()
        return jsonify({'departments': departments})
        
    except Exception as e:
        logging.error(f"Failed to get departments: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        if not opensearch_processor:
            return jsonify({'error': 'OpenSearch not connected'}), 500
        
        stats = opensearch_processor.get_index_stats()
        return jsonify({
            'opensearch_stats': stats,
            'gemini_model': 'gemini-2.0-flash-exp',
            'embedding_model': 'krutrim-ai-labs/vyakyarth'
        })
        
    except Exception as e:
        logging.error(f"Failed to get stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main function to start the server"""
    print("🚀 Starting KMRM RAG Backend Server")
    print("=" * 50)
    
    # Initialize OpenSearch
    print("🔌 Connecting to OpenSearch...")
    if not initialize_opensearch():
        print("❌ Failed to connect to OpenSearch")
        print("   Make sure OpenSearch is running on localhost:9200")
        return
    
    print("✅ OpenSearch connected successfully")
    print("🤖 Gemini 2.0 Flash configured")
    print("🌐 Starting Flask server...")
    
    # Start Flask server
    app.run(
        host='0.0.0.0',
        port=5001,  # Changed from 5000 to 5001
        debug=True,
        threaded=True
    )

if __name__ == '__main__':
    main()
