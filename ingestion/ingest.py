#!/usr/bin/env python3
"""
DocSense AI - Unified Ingestion Orchestrator
Supports --clean (temp files) and --reset-db (Chroma database)

Usage:

# 1. Normal run: clean temp files, keep existing database (fastest for small changes)
python -m ingestion.ingest --full --clean

# 2. Full clean re-ingestion (recommended when changing chunk size, extraction logic, etc.)
python -m ingestion.ingest --full --clean --reset-db

# 3. Force mode (no confirmation prompts)
python -m ingestion.ingest --full --clean --reset-db --force

# 4. Just reset the database without re-running everything
python -m ingestion.ingest --embed-only --reset-db --force

# 5. Test with dry run
python -m ingestion.ingest --full --clean --reset-db --dry-run
"""

import argparse
import shutil
import sys
from pathlib import Path
from ingestion.cleanup import cleanup_temp_directories
from .config import (
    DOWNLOAD_FOLDER, EXTRACTED_FOLDER, IMAGES_BASE, CHROMA_PATH,
    KEEP_PDFS, KEEP_EXTRACTED_TEXT, KEEP_IMAGES,
    DEFAULT_CLEAN, DEFAULT_FORCE
)

# Import main functions
from .drive_explorer import main as run_download
from .text_extractor import main as run_extract
from .chunk_and_embed import main as run_chunk_embed


def get_size(path: Path) -> int:
    """Return size in bytes of directory or file."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def cleanup_directories(clean_pdfs: bool, clean_images: bool, force: bool = False):
    """Clean only temporary folders (does NOT touch Chroma DB)."""
    to_delete = []
    if clean_pdfs and DOWNLOAD_FOLDER.exists():
        to_delete.append(DOWNLOAD_FOLDER)
    if clean_images and IMAGES_BASE.exists():
        to_delete.append(IMAGES_BASE)
    if not KEEP_EXTRACTED_TEXT and EXTRACTED_FOLDER.exists():
        to_delete.append(EXTRACTED_FOLDER)

    if not to_delete:
        print("✅ No temporary files to clean up.")
        return

    total_size_gb = sum(get_size(p) for p in to_delete) / (1024**3)

    print(f"\n🧹 Temporary files cleanup summary:")
    for p in to_delete:
        print(f"   - {p} ({get_size(p)/(1024*1024):.1f} MB)")
    print(f"   Total to free: ~{total_size_gb:.2f} GB")

    if not force:
        confirm = input("\nProceed with deletion? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cleanup cancelled.")
            return

    for p in to_delete:
        try:
            shutil.rmtree(p)
            print(f"✅ Deleted: {p}")
        except Exception as e:
            print(f"⚠️ Failed to delete {p}: {e}")

    print("🧹 Temporary files cleanup completed.\n")


def reset_chroma_db(force: bool = False):
    """Delete the entire Chroma database directory."""
    if not CHROMA_PATH.exists():
        print("ℹ️  Chroma DB directory does not exist yet.")
        return True

    print(f"\n⚠️  WARNING: This will completely delete the vector database at:")
    print(f"   {CHROMA_PATH.resolve()}")
    print("   All previously embedded chunks will be lost.")

    if not force:
        confirm = input("\nType 'RESET' to confirm database reset: ").strip()
        if confirm != "RESET":
            print("Database reset cancelled.")
            return False

    try:
        shutil.rmtree(CHROMA_PATH)
        print("✅ Chroma database directory deleted.")
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        print("✅ New empty Chroma database directory created.")
        return True
    except Exception as e:
        print(f"❌ Failed to reset Chroma DB: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="DocSense AI - Unified Ingestion Pipeline"
    )
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    parser.add_argument("--download-only", action="store_true", help="Only download")
    parser.add_argument("--extract-only", action="store_true", help="Only extract")
    parser.add_argument("--embed-only", action="store_true", help="Only chunk & embed")
    parser.add_argument("--clean", action="store_true", help="Clean temporary folders after embedding")
    parser.add_argument("--reset-db", action="store_true", help="Reset (delete) Chroma database before embedding")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without executing")

    args = parser.parse_args()

    if not any([args.full, args.download_only, args.extract_only, args.embed_only]):
        args.full = True

    print("🚀 DocSense AI Ingestion Pipeline")
    print("=" * 70)

    if args.dry_run:
        print("🔍 DRY-RUN MODE — No changes will be made.")
        return

    try:
        # Reset database if requested (before any embedding)
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

        # Step 3: Chunk & Embed
        if args.full or args.embed_only:
            print("\n🔨 Step 3: Chunking and embedding into ChromaDB...")
            run_chunk_embed()

        # Cleanup temporary files — only after successful embedding
        if (args.full or args.embed_only) and (args.clean or DEFAULT_CLEAN):
            print("\n🧹 Starting temporary files cleanup...")

            # Default: delete ALL temporary folders (including extracted_texts)
            # Only keep extracted_texts if you explicitly want to debug chunking
            cleanup_temp_directories(
                force=True,           # Skip confirmation in automated pipeline
                keep_extracted=False  # ← This controls whether extracted_texts is kept
            )

        # Final success message
        print("\n🎉 Pipeline completed successfully!")
        print(f"   Vector store: {CHROMA_PATH.resolve()}")

        if args.reset_db:
            print("   → Database was fully reset and rebuilt.")
        if args.clean or DEFAULT_CLEAN:
            print("   → Temporary files were cleaned.")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
