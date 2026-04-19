#!/bin/bash
# =============================================================================
# DocSense AI - Setup Script
# =============================================================================
# This script sets up the Python virtual environment and installs all
# dependencies for the DocSense AI Graph RAG project.
#
# Usage:
#   chmod +x setup/setup.sh
#   ./setup/setup.sh
# =============================================================================

set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting DocSense AI setup..."

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
# 3. Upgrade core tools
# ============================
echo "⬆️  Upgrading pip, setuptools and wheel..."
pip install --upgrade pip setuptools wheel

# Optional: Install uv for much faster dependency installation (recommended)
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
# 5. Final checks and messages
# ============================
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "========================================"
echo "🎉 DocSense AI is now ready to develop!"
echo "========================================"
echo ""
echo "To activate the environment in the future, run:"
echo "    source .venv/bin/activate"
echo ""
echo "Next steps:"
echo "   1. Set up your Google Drive API credentials"
echo "   2. Populate the Home_Health_Knowledge_Base folder"
echo "   3. Run the ingestion pipeline (coming soon)"
echo ""
echo "Happy coding! 🚀"
