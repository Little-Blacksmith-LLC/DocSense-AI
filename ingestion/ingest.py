#!/usr/bin/env python3
"""
DocSense AI - Unified Ingestion Orchestrator
Stable reset using collection delete (no directory deletion)

Usage:

python -m ingestion.ingest --full --reset-db --force
"""
import argparse
import shutil
import sys
import os
import chromadb
from pathlib import Path

from ingestion.cleanup import cleanup_temp_directories
from ingestion.config import (
    DOWNLOAD_FOLDER, EXTRACTED_FOLDER, IMAGES_BASE, CHROMA_PATH,
)

from ingestion.drive_explorer import main as run_download
from ingestion.text_extractor import main as run_extract
from ingestion.chunk_and_embed import main as run_chunk_embed
from ingestion.graph_builder import build_graph


def reset_chroma_db(force: bool = False):
    """Clear Chroma data by deleting the collection only (fixes readonly error)."""
    if not CHROMA_PATH.exists():
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        os.chmod(str(CHROMA_PATH), 0o777)
        print("✅ Chroma directory ready.")
        return True

    print(f"\n⚠️ WARNING: This will CLEAR ALL data in the vector database at:")
    print(f" {CHROMA_PATH.resolve()}")
    print(" The directory itself will NOT be deleted.")

    if not force:
        confirm = input("\nType 'RESET' to confirm: ").strip()
        if confirm != "RESET":
            print("Reset cancelled.")
            return False

    try:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collection_name = "docsense_knowledge_base"
        
        try:
            client.delete_collection(collection_name)
            print(f"✅ Deleted existing collection: {collection_name}")
        except Exception:
            pass  # Collection didn't exist

        # Recreate fresh
        client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        os.chmod(str(CHROMA_PATH), 0o777)
        print("✅ Chroma collection cleared and recreated successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to reset Chroma: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DocSense AI - Unified Ingestion Pipeline")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--embed-only", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--reset-db", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not any([args.full, args.download_only, args.extract_only, args.embed_only]):
        args.full = True

    print("🚀 DocSense AI Ingestion Pipeline")
    print("=" * 70)

    try:
        # Reset database if requested (collection only)
        if args.reset_db:
            if not reset_chroma_db(args.force):
                print("❌ Database reset cancelled. Aborting.")
                sys.exit(1)

        # Step 1: Download
        if args.full or args.download_only:
            print("\n📥 Step 1: Downloading from Google Drive...")
            run_download()

        # Step 2: Extract
        if args.full or args.extract_only:
            print("\n📄 Step 2: Extracting text, tables & images...")
            run_extract()

        # Step 3 & 4: Chunk & Embed + Graph
        if args.full or args.embed_only:
            print("\n🔨 Step 3: Chunking and embedding into ChromaDB...")
            run_chunk_embed()
            print("\n🕸️ Step 4: Building Knowledge Graph in Neo4j...")
            build_graph(reset_db=args.reset_db)

        # Cleanup
        if (args.full or args.embed_only) and args.clean:
            print("\n🧹 Starting temporary files cleanup...")
            cleanup_temp_directories(force=True, keep_extracted=False)

        print("\n🎉 Pipeline completed successfully!")
        print(f" Vector store: {CHROMA_PATH.resolve()}")
        if args.reset_db:
            print(" → Database was fully reset and rebuilt.")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
