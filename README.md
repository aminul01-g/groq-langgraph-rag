# 🤖 RAG Chatbot - Intelligent Document Q&A with Web Search

A sophisticated Retrieval-Augmented Generation (RAG) chatbot built with **LangGraph**, **Groq**, **Pinecone**, and **Streamlit**. Combines document-based knowledge retrieval with real-time web search capabilities for comprehensive answers.

## ✨ Features

- 📚 **Document Upload & Indexing** - Upload PDF documents and automatically index them in Pinecone vector database
- 🔍 **Semantic Search** - Retrieve relevant document chunks using semantic embeddings
- 🌐 **Web Search Integration** - Real-time web search via Tavily API for current information
- 🤖 **Intelligent Routing** - LLM-powered agent that decides between RAG, web search, or direct answer
- 💬 **Interactive Chat** - Beautiful Streamlit UI with conversation history and session management
- 📊 **Execution Tracing** - View detailed traces of how the agent processed your query
- 🚀 **Production Ready** - Docker support, health checks, and error handling
- ⚡ **Fast Processing** - Groq API integration for rapid LLM responses

## 🏗️ Architecture

```
┌─────────────────────┐
│   Streamlit UI      │ (Frontend)
│  - Chat Interface   │
│  - File Upload      │
│  - Trace Viewer     │
└──────────┬──────────┘
           │ HTTP/REST
           ▼
┌─────────────────────┐
│  FastAPI Backend    │ (Backend)
│  - Chat Endpoint    │
│  - Upload Endpoint  │
│  - Health Check     │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬─────────┐
    ▼             ▼          ▼         ▼
┌────────┐  ┌──────────┐ ┌─────┐  ┌──────────┐
│LangGraph│  │Pinecone  │ │Groq │  │ Tavily   │
│ Agent   │  │ Vector DB│ │ LLM │  │Web Search│
└────────┘  └──────────┘ └─────┘  └──────────┘
```

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- API Keys:
  - 🔑 **Groq API Key** - Get from [console.groq.com](https://console.groq.com)
  - 🔑 **Pinecone API Key** - Get from [pinecone.io](https://pinecone.io)
  - 🔑 **Tavily API Key** - Get from [tavily.com](https://tavily.com)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd RAG_Chatbot

# Create .env file with your API keys
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
TAVILY_API_KEY=your_tavily_api_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-index
EOF

# Start all services
docker-compose up -d

# Access the services
# Frontend: http://localhost:8501
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
TAVILY_API_KEY=your_tavily_api_key
EOF

# Run the backend
uvicorn main:app --reload
```

#### Frontend Setup (in another terminal)

```bash
cd frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run streamlit_app.py
```

## 📖 Usage

### Web Interface

1. **Chat Tab** 💬
   - Ask questions about your uploaded documents
   - Toggle web search on/off in the sidebar
   - View conversation history with timestamps
   - Messages are stored in session state

2. **Upload Documents Tab** 📤
   - Upload PDF files (one at a time)
   - View upload status and chunk count
   - Track all uploaded documents

3. **Trace Tab** 📊
   - View detailed execution traces
   - Understand agent decision-making
   - See routing decisions and data flow

### API Endpoints

#### Chat Endpoint
```bash
POST /chat/

Request:
{
    "session_id": "session_123",
    "query": "What is the capital of France?",
    "enable_web_search": true
}

Response:
{
    "response": "Paris is the capital of France...",
    "trace_events": [
        {
            "step": 1,
            "node_name": "router",
            "description": "Router decided: 'rag'",
            "event_type": "router_decision"
        },
        ...
    ]
}
```

#### Upload Document Endpoint
```bash
POST /upload-document/

Form Data:
- file: (PDF file)

Response:
{
    "message": "PDF successfully uploaded and indexed.",
    "filename": "document.pdf",
    "processed_chunks": 15
}
```

#### Health Check
```bash
GET /health

Response:
{
    "status": "ok"
}
```

## 🔧 Configuration

### Environment Variables

```env
# Groq Configuration
GROQ_API_KEY=gsk_xxxxx

# Pinecone Configuration
PINECONE_API_KEY=pcsk_xxxxx
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=rag-index

# Tavily Configuration
TAVILY_API_KEY=tvly-xxxxx

# Embedding Model
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Data Directory
DOC_SOURCE_DIR=data
```

### Backend Configuration (backend/config.py)

- **Vector Database**: Pinecone serverless
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **LLM Model**: llama-3.1-70b-versatile (via Groq)
- **Chunk Size**: 1000 characters with 200 character overlap

### Frontend Configuration (frontend/.streamlit/config.toml)

- **Primary Color**: #10a37f (green)
- **Port**: 8501
- **Theme**: Dark with custom modern styling

## 📁 Project Structure

```
RAG_Chatbot/
├── backend/
│   ├── agent.py              # LangGraph RAG agent
│   ├── config.py             # Configuration & API keys
│   ├── main.py               # FastAPI application
│   ├── vectorstore.py        # Pinecone integration
│   └── requirements.txt
│
├── frontend/
│   ├── streamlit_app.py      # Streamlit UI
│   ├── requirements.txt
│   └── .streamlit/
│       └── config.toml       # Streamlit configuration
│
├── Dockerfile.backend        # Backend container
├── Dockerfile.frontend       # Frontend container
├── docker-compose.yml        # Multi-container orchestration
├── .gitignore               # Git ignore rules
├── README.md                # This file
└── requirements.txt         # All dependencies
```

## 🔄 How It Works

### Chat Flow

1. **User Input** → Frontend sends query to backend
2. **Router Node** → LLM decides: RAG, Web Search, or Direct Answer
3. **RAG Node** (if selected) → Retrieves relevant document chunks
4. **Judge Node** → Evaluates if chunks are sufficient
5. **Web Node** (if needed) → Performs web search via Tavily
6. **Answer Node** → Generates final response using context
7. **Response** → Returns answer with execution trace

### Document Indexing

1. PDF file uploaded to backend
2. Text extracted using PyPDF
3. Text split into chunks (1000 chars, 200 char overlap)
4. Chunks converted to embeddings (384-dim vectors)
5. Embeddings stored in Pinecone vector database
6. Ready for semantic search queries

## 🐳 Docker Deployment

### Build Images
```bash
docker-compose build
```

### Start Services
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Clean Up
```bash
docker-compose down -v  # Remove volumes
```

## 🚨 Troubleshooting

### Backend Connection Issues
- Ensure backend is running on `http://localhost:8000`
- Check `API URL` in frontend sidebar
- Verify firewall isn't blocking port 8000

### API Key Errors
- Verify all keys in `.env` file
- Check keys are valid and not expired
- Ensure keys have proper permissions

### File Upload Issues
- Ensure file is a valid PDF
- Check file size isn't too large
- Verify `python-multipart` is installed
- Try uploading smaller PDFs first

### Streamlit Performance
- Clear browser cache
- Restart Streamlit app
- Check system resources
- Try `streamlit run streamlit_app.py --logger.level=debug`

### Docker Issues
```bash
# Check service health
docker-compose ps

# View detailed logs
docker-compose logs --tail=100

# Rebuild with no cache
docker-compose build --no-cache

# Reset everything
docker-compose down -v
docker-compose up -d --build
```

## 📊 Performance Metrics

- **Response Time**: ~2-5 seconds (RAG only), ~5-10 seconds (with web search)
- **Chunk Retrieval**: <100ms (Pinecone)
- **Embedding Generation**: ~200ms (HuggingFace)
- **LLM Inference**: ~1-3 seconds (Groq)
- **Max Concurrent Users**: Limited by Pinecone/Groq API quotas

## 🔐 Security Considerations

- Store API keys in environment variables (never in code)
- Use `.env` file with `.gitignore`
- For production:
  - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
  - Enable HTTPS/TLS
  - Set up authentication/authorization
  - Rate limiting on API endpoints
  - Run in isolated network

## 🚀 Deployment Options

### AWS
```bash
# ECR for images, ECS for orchestration
docker tag rag-chatbot-backend:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/rag-chatbot-backend
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/rag-chatbot-backend
```

### Google Cloud
```bash
gcloud builds submit --tag gcr.io/<project>/rag-chatbot-backend
gcloud run deploy rag-chatbot-backend --image gcr.io/<project>/rag-chatbot-backend
```

### Kubernetes
```yaml
# Use provided docker-compose as reference
# Create Kubernetes manifests for deployment
```

## 📚 Dependencies

### Backend
- `langgraph` - Agentic framework
- `langchain` - LLM orchestration
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langchain-groq` - Groq LLM integration
- `langchain-pinecone` - Pinecone vector store
- `langchain-tavily` - Web search tool
- `langchain-huggingface` - Embeddings

### Frontend
- `streamlit` - Web UI framework
- `requests` - HTTP client

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review execution traces for debugging

## 🙏 Acknowledgments

- **LangChain** - LLM framework
- **LangGraph** - Agentic orchestration
- **Groq** - Fast LLM inference
- **Pinecone** - Vector database
- **Tavily** - Web search API
- **Streamlit** - Frontend framework
- **FastAPI** - Backend framework

## 📈 Roadmap

- [ ] Multi-language support
- [ ] Advanced query expansion
- [ ] Custom prompt templates
- [ ] Document metadata filtering
- [ ] User authentication
- [ ] Analytics dashboard
- [ ] Response caching
- [ ] Batch document processing
- [ ] Export conversation as PDF
- [ ] Integration with more LLM providers

---

**Made with ❤️ for intelligent document Q&A**
