#!/bin/bash
# =============================================================================
# DocSense AI - Setup Script (Fully Local / Private)
# =============================================================================
# This script sets up the environment and pulls all required Ollama models
# so that everything runs locally with zero external API calls after setup.
# =============================================================================

set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting DocSense AI setup (Privacy-First Mode)..."

# ============================
# 1. Create virtual environment
# ============================
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "✅ Virtual environment already exists at $VENV_DIR"
fi

# ============================
# 2. Activate virtual environment
# ============================
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# ============================
# 3. Upgrade core tools + install uv
# ============================
echo "⬆️ Upgrading pip, setuptools and wheel..."
pip install --upgrade pip setuptools wheel

if ! command -v uv &> /dev/null; then
    echo "⚡ Installing uv (fast Python package installer)..."
    pip install uv
fi

# ============================
# 4. Install project dependencies
# ============================
echo "📚 Installing project dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv for faster installation..."
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# ============================
# 5. Pull required Ollama models (Fully Local)
# ============================
echo ""
echo "🤖 Pulling Ollama models (this may take a while the first time)..."

# Embedding model - excellent quality and fully local
echo "   → Pulling nomic-embed-text (embedding model)..."
ollama pull nomic-embed-text

# Vision model for image captions
echo "   → Pulling llama3.2-vision:11b (for image captions)..."
ollama pull llama3.2-vision:11b

echo "✅ All Ollama models pulled successfully!"

# ============================
# 6. Final messages
# ============================
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "========================================"
echo "🎉 DocSense AI is now ready (Fully Local Mode)!"
echo "========================================"
echo ""
echo "To activate the environment in the future, run:"
echo " source .venv/bin/activate"
echo ""
echo "Next steps:"
echo "  1. Set up your Google Drive API credentials"
echo "  2. Populate the Home_Health_Knowledge_Base folder"
echo "  3. Run: python ingestion/chunk_and_embed.py"
echo ""
echo "Happy coding! 🚀"
