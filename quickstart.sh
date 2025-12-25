#!/bin/bash

# 🚀 Quick Start Script for RAG Chatbot
# This script helps you get up and running quickly

set -e  # Exit on error

echo "======================================"
echo "🤖 RAG Chatbot - Quick Start"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ .env created. Please edit it with your API keys:"
        echo ""
        echo "   1. Get Groq API Key from: https://console.groq.com/keys"
        echo "   2. Get Pinecone API Key from: https://app.pinecone.io"
        echo "   3. Get Tavily API Key from: https://app.tavily.com"
        echo ""
        echo "   Edit .env file and add your keys:"
        echo "   nano .env  # or use your favorite editor"
        echo ""
        read -p "Press Enter after updating .env file..."
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Verify API keys are set
echo ""
echo "🔐 Checking API keys..."

if grep -q "your_groq_api_key_here" .env; then
    echo "⚠️  GROQ_API_KEY not set properly in .env"
    echo "   Update it at: https://console.groq.com/keys"
fi

if grep -q "your_pinecone_api_key_here" .env; then
    echo "⚠️  PINECONE_API_KEY not set properly in .env"
    echo "   Update it at: https://app.pinecone.io"
fi

if grep -q "your_tavily_api_key_here" .env; then
    echo "⚠️  TAVILY_API_KEY not set properly in .env"
    echo "   Update it at: https://app.tavily.com"
fi

echo ""
echo "🏗️  Building Docker images..."
docker-compose build --quiet

echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start (this may take 30-60 seconds)..."

for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready"
        break
    fi
    echo -n "."
    sleep 1
done

for i in {1..30}; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "✅ Frontend is ready"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "======================================"
echo "✨ RAG Chatbot is Ready!"
echo "======================================"
echo ""
echo "🌐 Access the application at:"
echo "   Frontend:  http://localhost:8501"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📚 Useful Commands:"
echo "   View logs:     docker-compose logs -f"
echo "   View backend:  docker-compose logs -f backend"
echo "   View frontend: docker-compose logs -f frontend"
echo "   Stop services: docker-compose down"
echo "   Clean up:      docker-compose down -v"
echo ""
echo "📖 For more information, see README.md"
echo ""
