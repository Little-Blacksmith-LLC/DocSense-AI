#!/usr/bin/env python3
"""
DocSense AI - Chunking & Embedding (defensive Chroma setup)
"""
import json
from pathlib import Path
import uuid
import os
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import chromadb
import ollama
from ingestion.config import EXTRACTED_FOLDER, CHROMA_PATH
from ingestion.folder_summarizer import main as run_folder_summarizer

# ========================= CONFIG =========================
EMBEDDING_MODEL = "nomic-embed-text"
VISION_MODEL = "llama3.2-vision:11b"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120

def get_chroma_collection():
    """Ultra-defensive Chroma setup"""
    print("🔧 Setting up ChromaDB client...")
   
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    os.chmod(str(CHROMA_PATH), 0o777)   # Ensure full write access
    
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection_name = "docsense_knowledge_base"
    
    try:
        client.delete_collection(collection_name)
        print(f"✅ Cleared existing collection: {collection_name}")
    except Exception:
        pass
    
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"✅ Chroma collection ready: {collection_name}")
    return collection

collection = None

def generate_image_caption(image_path: str) -> str:
    try:
        print(f" 📸 Generating caption for: {Path(image_path).name}")
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
        print(f" ✅ Caption: {caption[:100]}...")
        return caption
    except Exception as e:
        print(f" ⚠️ Caption failed: {e}")
        return "Image from document (visual element)"

def process_extracted_file(json_path: Path):
    global collection
    if collection is None:
        collection = get_chroma_collection()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
  
    doc_name = data.get("document_name", json_path.stem)
    relative_folder = data.get("relative_folder", ".")
    full_markdown = data.get("full_markdown", "")
    images = data.get("images", [])
    drive_link = data.get("drive_link")
    drive_file_id = data.get("drive_file_id")

    print(f"\n🔨 Processing: {doc_name} (folder: {relative_folder})")

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
                    "drive_link": drive_link,
                    "drive_file_id": drive_file_id
                }
            })

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
                    "drive_link": drive_link,
                    "drive_file_id": drive_file_id
                }
            })

    if all_chunks:
        texts = [c["text"] for c in all_chunks]
        metadatas = [c["metadata"] for c in all_chunks]
        ids = [c["metadata"]["chunk_id"] for c in all_chunks]
       
        collection.add(documents=texts, metadatas=metadatas, ids=ids)
        print(f" ✅ Stored {len(all_chunks)} chunks")
    else:
        print(" ⚠️ No chunks generated")

def main():
    json_files = list(EXTRACTED_FOLDER.glob("*.json"))
    print(f"Found {len(json_files)} documents to process.\n")
   
    for json_file in json_files:
        process_extracted_file(json_file)
   
    print("\n🎉 Fully local chunking & embedding completed!")
    print(f" Vector store: {CHROMA_PATH.resolve()}")
    
    run_folder_summarizer()

if __name__ == "__main__":
    main()
