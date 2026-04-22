#!/bin/bash
# DocSense AI - Quick Start Script

echo "🚀 Starting DocSense AI..."

# Activate virtual environment
source .venv/bin/activate

# Start Neo4j in background
echo "📊 Starting Neo4j..."
docker compose up -d

# Wait a moment for Neo4j to be ready
sleep 3

# Start Streamlit
echo "💬 Starting DocSense AI Chat Interface..."
echo "   Open your browser to http://localhost:8501"
streamlit run streamlit_app.py
