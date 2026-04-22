#!/usr/bin/env python3
"""
DocSense AI - Central Configuration
Loads sensitive/local settings from .env (gitignored)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file automatically
load_dotenv()

# ========================= PATHS & DRIVE =========================
ROOT_FOLDER_ID = os.getenv("DOCSENSE_ROOT_FOLDER_ID")
if not ROOT_FOLDER_ID:
    raise ValueError(
        "DOCSENSE_ROOT_FOLDER_ID is not set in .env file. "
        "Please add it to your .env in the project root."
    )

DOWNLOAD_FOLDER = Path("downloaded_docs")
EXTRACTED_FOLDER = Path("extracted_texts")
IMAGES_BASE = Path("extracted_images")
CHROMA_PATH = Path("vector_store/chroma_db")
METADATA_FILE = Path("drive_metadata.json")

# ========================= Neo4j Configuration =========================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError(
        "NEO4J_PASSWORD is not set in .env file. "
        "Please add NEO4J_PASSWORD=your_actual_password to your .env"
    )
    
# ========================= FOLDER SUMMARIES =========================
SUMMARY_MODEL = "llama3.1:8b"          # or llama3.2:3b if you want it faster
MAX_SUMMARY_TOKENS = 400
FOLDER_SUMMARY_PROMPT = """
You are summarizing an entire folder in the DocSense AI knowledge base for a home health agency.
Write a concise 2-4 sentence overview of what this folder contains.
Focus on: topics covered, document types, regulatory/compliance focus, and any key themes.
Do not list individual files. Be professional and factual.
Folder path: {folder_path}
"""

# ========================= CLEANUP & RETENTION =========================
KEEP_PDFS = False
KEEP_EXTRACTED_TEXT = True
KEEP_IMAGES = False

# ========================= OLLAMA =========================
EMBEDDING_MODEL = "nomic-embed-text"
VISION_MODEL = "llama3.2-vision:11b"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120
