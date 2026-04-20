# testing/test_chunk_and_embed.py
"""
DocSense AI - Chunking & Vector Store Tests

Purpose: Ensure chunk_and_embed.py correctly splits documents and stores 
them in ChromaDB with all necessary metadata for retrieval and access control.
"""

import chromadb
from pathlib import Path


def test_chroma_collection_health():
    """
    Verify ChromaDB is properly set up and contains expected data.
    
    This acts as a smoke test for the entire ingestion pipeline.
    """
    chroma_path = Path("vector_store/chroma_db")
    assert chroma_path.exists(), "ChromaDB directory not found — run ingestion first"

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection("docsense_knowledge_base")

    count = collection.count()
    assert count > 1000, f"Expected >1000 chunks, got only {count}"

    # Check metadata fields critical for access control
    sample_meta = collection.peek(1)["metadatas"][0]
    assert "relative_folder" in sample_meta
    assert "document_name" in sample_meta
    assert "chunk_id" in sample_meta

    print(f"✅ ChromaDB healthy: {count:,} chunks with proper metadata")
