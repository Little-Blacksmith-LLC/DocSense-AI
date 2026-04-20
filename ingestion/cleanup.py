#!/usr/bin/env python3
"""
DocSense AI - Cleanup Utility
Safely removes temporary directories and optionally resets the vector database.

Usage:

# 1. Clean temporary folders only (recommended after a run)
python -m ingestion.cleanup --clean

# 2. Clean temp folders + force delete extracted_texts too
python -m ingestion.cleanup --clean --remove-extracted --force

# 3. Reset only the database
python -m ingestion.cleanup --reset-db --force

# 4. Full cleanup: temp files + database reset
python -m ingestion.cleanup --clean --reset-db --force

# 5. Keep extracted texts while cleaning everything else
python -m ingestion.cleanup --clean --keep-extracted
"""

import argparse
import shutil
import sys
from pathlib import Path

from .config import (
    DOWNLOAD_FOLDER,
    EXTRACTED_FOLDER,
    IMAGES_BASE,
    CHROMA_PATH,
    KEEP_EXTRACTED_TEXT
)

def get_size(path: Path) -> int:
    """Return size in bytes of a directory or file."""
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())


def cleanup_temp_directories(force: bool = False, keep_extracted: bool = False):
    """
    Clean up temporary directories after successful ingestion.
    
    By default, we delete downloaded_docs, extracted_images, AND extracted_texts
    because all necessary data is now stored in the Chroma vector database.
    
    Args:
        force: Skip confirmation prompt (used in automated pipeline).
        keep_extracted: If True, preserve extracted_texts/ (useful for debugging).
                        Default is False = delete everything except the vector store.
    """
    to_delete = []

    # Always clean these two
    if DOWNLOAD_FOLDER.exists():
        to_delete.append(DOWNLOAD_FOLDER)
    if IMAGES_BASE.exists():
        to_delete.append(IMAGES_BASE)

    # Delete extracted_texts unless explicitly told to keep it
    if not keep_extracted and EXTRACTED_FOLDER.exists():
        to_delete.append(EXTRACTED_FOLDER)

    if not to_delete:
        print("✅ No temporary directories to clean.")
        return

    # Show cleanup summary
    total_size_mb = sum(get_size(p) for p in to_delete) / (1024 * 1024)
    print("🧹 Temporary files cleanup summary:")
    for p in to_delete:
        size_mb = get_size(p) / (1024 * 1024)
        print(f"   - {p.name} ({size_mb:.1f} MB)")
    print(f"   Total to free: ~{total_size_mb:.2f} MB\n")

    if not force:
        confirm = input("Proceed with deletion? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cleanup cancelled.")
            return

    for p in to_delete:
        try:
            shutil.rmtree(p)
            print(f"✅ Deleted: {p}")
        except Exception as e:
            print(f"⚠️ Failed to delete {p}: {e}")

    print("🧹 Temporary files cleanup completed.")
    

def reset_database(force: bool = False):
    """Completely reset the Chroma vector database."""
    if not CHROMA_PATH.exists():
        print("ℹ️  Vector database does not exist. Nothing to reset.")
        return

    print(f"⚠️  WARNING: This will permanently delete the vector database at:")
    print(f"   {CHROMA_PATH.resolve()}")
    print("   All embedded chunks will be lost.\n")

    if not force:
        confirm = input("Type 'RESET' to confirm database reset: ").strip()
        if confirm != "RESET":
            print("Database reset cancelled.")
            return

    try:
        shutil.rmtree(CHROMA_PATH)
        print("✅ Vector database deleted.")
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        print("✅ New empty database directory created.")
    except Exception as e:
        print(f"❌ Failed to reset database: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="DocSense AI - Cleanup Utility"
    )
    parser.add_argument("--clean", action="store_true", 
                        help="Clean temporary directories (downloaded_docs, extracted_images)")
    parser.add_argument("--reset-db", action="store_true", 
                        help="Reset the Chroma vector database")
    parser.add_argument("--force", action="store_true", 
                        help="Skip confirmation prompts")
    parser.add_argument("--keep-extracted", action="store_true",
                        help="Keep extracted_texts folder (Markdown + JSON)")
    parser.add_argument("--remove-extracted", action="store_true",
                        help="Also remove extracted_texts folder")

    args = parser.parse_args()

    # Default behavior if no flags provided
    if not args.clean and not args.reset_db:
        print("No action specified. Use --clean and/or --reset-db.")
        parser.print_help()
        sys.exit(1)

    print("🧹 DocSense AI Cleanup Utility")
    print("=" * 60)

    try:
        if args.clean:
            keep_extracted = None
            if args.keep_extracted:
                keep_extracted = True
            elif args.remove_extracted:
                keep_extracted = False

            cleanup_temp_directories(args.force, keep_extracted)

        if args.reset_db:
            reset_database(args.force)

        print("🎉 Cleanup finished.")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
