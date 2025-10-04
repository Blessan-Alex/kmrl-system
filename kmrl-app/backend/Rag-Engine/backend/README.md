# KMRM RAG Backend & Frontend

A complete RAG (Retrieval-Augmented Generation) system with Gemini 2.0 Flash integration and OpenSearch similarity search.

## 🚀 Features

- **Gemini 2.0 Flash Integration**: Uses your API key for intelligent response generation
- **OpenSearch Similarity Search**: Fast vector search using krutrim-ai-labs/vyakyarth embeddings
- **Modern Web Interface**: Beautiful, responsive frontend
- **Department Filtering**: Filter results by department
- **Real-time Processing**: Fast query processing with progress indicators

## 📁 Project Structure

```
backend/
├── app.py                 # Main Flask backend
├── start_server.py        # Server startup script
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Frontend interface
└── README.md             # This file
```

## 🛠️ Setup & Installation

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start OpenSearch
```bash
# Make sure OpenSearch is running
docker-compose up -d
```

### 3. Start the Server
```bash
python start_server.py
```

### 4. Access the Interface
Open your browser and go to: `http://localhost:5000`

## 🔧 API Endpoints

### Health Check
```http
GET /api/health
```
Returns server status and connection information.

### Process Query
```http
POST /api/query
Content-Type: application/json

{
    "query": "What are the safety requirements?",
    "department": "engineering",
    "top_k": 5
}
```

### Get Departments
```http
GET /api/departments
```
Returns list of available departments for filtering.

### Get Statistics
```http
GET /api/stats
```
Returns system statistics including document counts and model information.

## 🎯 How It Works

### 1. Query Processing Flow
```
User Query → Embedding Generation → OpenSearch Search → Gemini Summarization → Response
```

### 2. Components
- **Frontend**: Modern HTML/JS interface with real-time updates
- **Backend**: Flask API with CORS support
- **Embeddings**: krutrim-ai-labs/vyakyarth for fast vector generation
- **Search**: OpenSearch k-NN search for similarity matching
- **AI**: Gemini 2.0 Flash for intelligent response generation

### 3. Query Example
```
Input: "What are the safety requirements for metro operations?"

1. Generate embedding using krutrim-ai-labs/vyakyarth
2. Search OpenSearch for similar documents
3. Send context + query to Gemini 2.0 Flash
4. Return structured response with sources
```

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Loading**: Progress indicators during processing
- **Department Filtering**: Dropdown to filter by department
- **Result Visualization**: Clear display of AI responses and source documents
- **Statistics**: Processing time and document counts
- **Error Handling**: User-friendly error messages

## 🔍 Usage Examples

### Basic Query
```
"What are the maintenance schedules for metro trains?"
```

### Department-Specific Query
```
"What safety protocols are in place?" (Department: Safety)
```

### Technical Query
```
"How does the procurement process work for new equipment?"
```

## 📊 Performance

- **Embedding Generation**: ~0.1-0.3 seconds
- **OpenSearch Search**: ~0.05-0.2 seconds
- **Gemini Response**: ~1-3 seconds
- **Total Query Time**: ~1.5-3.5 seconds

## 🛠️ Configuration

### Environment Variables
```bash
export GEMINI_API_KEY="your_api_key_here"
export OPENSEARCH_HOST="localhost"
export OPENSEARCH_PORT="9200"
```

### Model Configuration
- **Embedding Model**: krutrim-ai-labs/vyakyarth (768 dimensions)
- **AI Model**: gemini-2.0-flash-exp
- **Search Method**: k-NN with cosine similarity

## 🚨 Troubleshooting

### Common Issues

1. **OpenSearch Connection Failed**
   ```bash
   # Check if OpenSearch is running
   curl http://localhost:9200
   
   # Start OpenSearch
   docker-compose up -d
   ```

2. **Gemini API Error**
   - Verify your API key is correct
   - Check API quota and billing
   - Ensure internet connection

3. **No Documents Found**
   - Verify embeddings are uploaded to OpenSearch
   - Check index name and configuration
   - Try different query terms

### Debug Mode
```bash
# Run with debug logging
FLASK_DEBUG=1 python app.py
```

## 🔧 Development

### Adding New Features
1. Modify `app.py` for backend changes
2. Update `templates/index.html` for frontend changes
3. Test with `python start_server.py`

### API Testing
```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test query endpoint
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## 📈 Monitoring

The system provides real-time statistics:
- Query processing time
- Number of documents found
- Department filtering
- Search performance metrics

## 🎉 Success!

Your RAG system is now ready! Users can:
- Ask natural language questions
- Get intelligent AI responses
- See source documents
- Filter by department
- View processing statistics

The system combines the power of OpenSearch similarity search with Gemini 2.0 Flash's advanced language understanding for accurate, contextual responses.
