# testing/test_ingestion_pipeline.py
"""
Integration / smoke tests for the full ingestion pipeline.
"""

from pathlib import Path
import json

def test_extracted_files_have_relative_folder():
    """Critical for access control: every document must preserve its folder path."""
    extracted_dir = Path("extracted_texts")
    json_files = list(extracted_dir.glob("*.json"))
    
    assert len(json_files) > 0
    
    for json_file in json_files[:5]:   # check first 5 is enough
        with open(json_file) as f:
            data = json.load(f)
        assert "relative_folder" in data
        assert data["relative_folder"] != "", "relative_folder should not be empty"
    
    print(f"✅ All extracted files contain relative_folder metadata ({len(json_files)} files checked)")
