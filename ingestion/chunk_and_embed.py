#!/usr/bin/env python3
"""
DocSense AI - Chunking & Embedding Pipeline (Fully Local with Ollama)
No external dependencies beyond Ollama.
"""

import json
from pathlib import Path
import uuid

from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import chromadb
import ollama

EXTRACTED_FOLDER = Path("extracted_texts")
CHROMA_PATH = Path("vector_store/chroma_db")
CHROMA_PATH.mkdir(parents=True, exist_ok=True)

# ========================= CONFIG =========================
EMBEDDING_MODEL = "nomic-embed-text"      # Fully local embedding model
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120

USE_VISION_CAPTIONS = True
VISION_MODEL = "llama3.2-vision:11b"

print("🚀 Starting fully local Ollama embedding pipeline...")
print(f"   Embedding model : {EMBEDDING_MODEL}")
print(f"   Vision model    : {VISION_MODEL}")
print("=" * 85)

# Initialize local embeddings via Ollama
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = chroma_client.get_or_create_collection(
    name="docsense_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)

def generate_image_caption(image_path: str) -> str:
    try:
        print(f"   📸 Generating caption for: {Path(image_path).name}")
        response = ollama.chat(
            model=VISION_MODEL,
            messages=[{
                'role': 'user',
                'content': (
                    "Describe this image in 1-2 concise, factual sentences. "
                    "Focus on content relevant to home health, nurse credentialing, "
                    "compliance, clinical protocols, policies, or checklists."
                ),
                'images': [image_path]
            }]
        )
        caption = response['message']['content'].strip()
        print(f"   ✅ Caption: {caption[:100]}...")
        return caption
    except Exception as e:
        print(f"   ⚠️ Caption failed: {e}")
        return "Image from document (visual element)"


def process_extracted_file(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc_name = data.get("document_name", json_path.stem)
    relative_folder = data.get("relative_folder", ".")
    full_markdown = data.get("full_markdown", "")
    images = data.get("images", [])

    print(f"\n🔨 Processing: {doc_name} (folder: {relative_folder})")

    # Structure-aware chunking
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")],
        strip_headers=False,
    )
    header_chunks = header_splitter.split_text(full_markdown)

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_chunks = []
    for chunk_doc in header_chunks:
        sub_chunks = recursive_splitter.split_text(chunk_doc.page_content)
        for sub in sub_chunks:
            all_chunks.append({
                "text": sub,
                "metadata": {
                    "chunk_id": str(uuid.uuid4()),
                    "document_name": doc_name,
                    "relative_folder": relative_folder,
                    "chunk_type": "text",
                    "section": chunk_doc.metadata.get("Header 1", "General"),
                }
            })

    # Image chunks with captions
    for img in images:
        img_path_full = Path("extracted_images") / img.get("file_path", "")
        if img_path_full.exists():
            caption = generate_image_caption(str(img_path_full))
            image_text = f"{caption}\n\nContext: Appears on page {img.get('page_number')} of '{doc_name}' in folder '{relative_folder}'."

            all_chunks.append({
                "text": image_text,
                "metadata": {
                    "chunk_id": str(uuid.uuid4()),
                    "document_name": doc_name,
                    "relative_folder": relative_folder,
                    "chunk_type": "image",
                    "page_number": img.get("page_number"),
                    "image_path": str(img_path_full),
                }
            })

    if all_chunks:
        texts = [c["text"] for c in all_chunks]
        metadatas = [c["metadata"] for c in all_chunks]
        ids = [c["metadata"]["chunk_id"] for c in all_chunks]

        collection.add(documents=texts, metadatas=metadatas, ids=ids)
        print(f"   ✅ Stored {len(all_chunks)} chunks")
    else:
        print("   ⚠️ No chunks generated")


def main():
    json_files = list(EXTRACTED_FOLDER.glob("*.json"))
    print(f"Found {len(json_files)} documents to process.\n")

    for json_file in json_files:
        process_extracted_file(json_file)

    print("\n🎉 Fully local chunking & embedding completed!")
    print(f"   Vector store: {CHROMA_PATH}")


if __name__ == "__main__":
    main()
