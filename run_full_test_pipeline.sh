#!/bin/bash
# =============================================================================
# DocSense AI - Full Test Pipeline Runner
# =============================================================================
# This script runs the complete end-to-end workflow:
#   1. Full ingestion (download → extract → chunk & embed)
#   2. All tests in the testing/ directory
#   3. Cleanup of temporary files
#
# Usage:
#   ./run_full_test_pipeline.sh
#   ./run_full_test_pipeline.sh --no-cleanup   # skip final cleanup
#
# Author: Grok (for Dennis)
# =============================================================================

set -e  # Exit immediately if any command fails

echo "🚀 Starting DocSense AI Full Test Pipeline..."
echo "================================================================="

# ----------------------------- 1. Full Ingestion -----------------------------
echo "📥 Step 1: Running full ingestion pipeline (download + extract + embed)..."
echo "   (Temporary folders will be kept for testing)"

python -m ingestion.ingest --full --reset-db --force

echo "✅ Ingestion completed successfully."
echo ""

# ----------------------------- 2. Run All Tests ------------------------------
echo "🧪 Step 2: Running all tests..."
echo "   (This requires extracted_texts/ and vector_store/ to exist)"

pytest testing/ -v --tb=short

echo ""
echo "✅ All tests completed."
echo ""

# ----------------------------- 3. Cleanup (Optional) -------------------------
if [[ "$1" == "--no-cleanup" || "$1" == "-k" ]]; then
    echo "⏭️  Skipping cleanup as requested (--no-cleanup)."
    echo "   You can manually clean later with: python -m ingestion.cleanup --clean --force"
else
    echo "🧹 Step 3: Cleaning up temporary files..."
    python -m ingestion.cleanup --clean --force
    echo "✅ Cleanup completed."
fi

echo ""
echo "🎉 Full test pipeline finished successfully!"
echo "   Vector store is ready at: ./vector_store/chroma_db"
echo ""
echo "Next time you can run this script with:"
echo "   ./run_full_test_pipeline.sh --no-cleanup   (if you want to inspect temp files)"
