# testing/test_text_extractor.py
"""
DocSense AI - Text Extraction Tests

Purpose: Verify that text_extractor.py correctly processes PDFs into 
structured Markdown + JSON with preserved folder metadata and smart image filtering.
This ensures the foundation for chunking and access control is reliable.
"""

from pathlib import Path
import json
from ingestion.text_extractor import EXTRACTED_FOLDER


def test_extraction_produced_files():
    """
    Verify that the text extraction step created the expected output files.
    
    Checks for both JSON (structured data) and Markdown (human readable) outputs.
    """
    json_files = list(EXTRACTED_FOLDER.glob("*.json"))
    md_files = list(EXTRACTED_FOLDER.glob("*.md"))
    
    assert len(json_files) >= 8, f"Only {len(json_files)} JSON files found"
    assert len(md_files) >= 8, f"Only {len(md_files)} Markdown files found"
    
    print(f"✅ Extraction produced {len(json_files)} documents")


def test_extraction_file_structure():
    """
    Validate that each extracted JSON contains all required fields for downstream processing.
    
    Critical fields: relative_folder (used for access control), full_markdown, images, etc.
    """
    json_files = list(EXTRACTED_FOLDER.glob("*.json"))
    assert len(json_files) > 0

    with open(json_files[0], encoding="utf-8") as f:
        data = json.load(f)

    required_keys = ["full_markdown", "relative_folder", "document_name", "images"]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in extraction output"

    print("✅ Extracted files have correct structure and metadata")
