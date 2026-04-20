#!/usr/bin/env python3
"""
DocSense AI - Central Configuration
Loads sensitive/local settings from .env (gitignored)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically (no export command needed)
load_dotenv()

# ========================= PATHS =========================
ROOT_FOLDER_ID = os.getenv("DOCSENSE_ROOT_FOLDER_ID")
if not ROOT_FOLDER_ID:
    raise ValueError(
        "DOCSENSE_ROOT_FOLDER_ID is not set. "
        "Please create a .env file in the project root with your Google Drive folder ID."
    )

DOWNLOAD_FOLDER = Path("downloaded_docs")
EXTRACTED_FOLDER = Path("extracted_texts")
IMAGES_BASE = Path("extracted_images")
CHROMA_PATH = Path("vector_store/chroma_db")

# ========================= CLEANUP & RETENTION =========================
KEEP_PDFS = False                    # Set True if you want to keep raw PDFs
KEEP_EXTRACTED_TEXT = True           # Recommended: keep Markdown/JSON for debugging
KEEP_IMAGES = False                  # Captions are already embedded

DEFAULT_CLEAN = False
DEFAULT_FORCE = False

# ========================= OLLAMA =========================
EMBEDDING_MODEL = "nomic-embed-text"
VISION_MODEL = "llama3.2-vision:11b"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120
