#!/usr/bin/env python3
"""
DocSense AI - Folder Level Summarizer
Generates one high-level summary per folder during ingestion.
"""
import json
from pathlib import Path
from collections import defaultdict
from langchain_ollama import ChatOllama
from ingestion.config import (
    EXTRACTED_FOLDER, SUMMARY_MODEL, FOLDER_SUMMARY_PROMPT,
    CHROMA_PATH
)
import chromadb

def generate_folder_summary(folder_path: str, markdown_texts: list[str]) -> str:
    if not markdown_texts:
        return "Empty folder."
    
    llm = ChatOllama(model=SUMMARY_MODEL, temperature=0.0, max_tokens=400)
    
    combined = "\n\n---\n\n".join(markdown_texts[:8])  # limit context
    prompt = FOLDER_SUMMARY_PROMPT.format(folder_path=folder_path)
    
    response = llm.invoke(f"{prompt}\n\nContent from this folder:\n{combined}")
    return response.content.strip()

def store_folder_summary_in_chroma(folder_path: str, summary: str):
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection("docsense_knowledge_base")
    
    summary_id = f"folder_summary_{folder_path.replace('/', '_')}"
    
    collection.add(
        documents=[summary],
        metadatas=[{
            "chunk_id": summary_id,
            "document_name": "FOLDER_SUMMARY",
            "relative_folder": folder_path,
            "chunk_type": "folder_summary",
            "section": "Folder Overview"
        }],
        ids=[summary_id]
    )
    print(f"✅ Stored folder summary for: {folder_path}")

def main():
    print("📊 Generating folder-level summaries...")
    
    # Group markdown by folder
    folder_content = defaultdict(list)
    for json_file in EXTRACTED_FOLDER.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        folder = data.get("relative_folder", ".")
        markdown = data.get("full_markdown", "")[:8000]  # safety limit
        if markdown.strip():
            folder_content[folder].append(markdown)
    
    for folder, texts in folder_content.items():
        print(f"📁 Summarizing folder: {folder} ({len(texts)} documents)")
        summary = generate_folder_summary(folder, texts)
        store_folder_summary_in_chroma(folder, summary)
    
    print("🎉 All folder summaries generated and stored!")

if __name__ == "__main__":
    main()
