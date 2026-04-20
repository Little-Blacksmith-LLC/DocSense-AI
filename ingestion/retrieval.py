#!/usr/bin/env python3
"""
DocSense AI - Retrieval with Folder-Based Access Control
Fully local using Ollama embeddings.
"""

from langchain_ollama import OllamaEmbeddings
import chromadb
from typing import List, Dict, Optional

class DocSenseRetriever:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        self.client = chromadb.PersistentClient(path="vector_store/chroma_db")
        self.collection = self.client.get_collection("docsense_knowledge_base")

    def retrieve(self, 
                 query: str, 
                 allowed_folders: Optional[List[str]] = None, 
                 n_results: int = 8):
        """
        Retrieve relevant chunks with access control.
        
        allowed_folders: List of folder prefixes the user can access.
                         Example: ["Departments/Human Resources", "Company Overview"]
                         If None → user can see everything.
        """
        print(f"🔍 Query: '{query}'")
        if allowed_folders:
            print(f"   Allowed folders: {allowed_folders}")

        # Get more results initially, then filter
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results * 3,   # oversample then filter
            include=["metadatas", "documents", "distances"]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        filtered = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            folder = meta.get("relative_folder", "")

            # Access control filter
            if allowed_folders is None or any(folder.startswith(allowed) for allowed in allowed_folders):
                filtered.append({
                    "content": doc,
                    "metadata": meta,
                    "score": 1 - dist,           # convert distance to similarity score
                    "document_name": meta.get("document_name"),
                    "folder": folder,
                    "chunk_type": meta.get("chunk_type", "text"),
                    "page": meta.get("page_number")
                })

        # Return top N after filtering
        filtered = sorted(filtered, key=lambda x: x["score"], reverse=True)[:n_results]

        print(f"   → Returned {len(filtered)} authorized results\n")
        return filtered

    def print_results(self, results: List[Dict]):
        for i, r in enumerate(results, 1):
            print(f"Result {i} | Score: {r['score']:.4f} | Type: {r['chunk_type']}")
            print(f"Document : {r['document_name']}")
            print(f"Folder   : {r['folder']}")
            if r.get('page'):
                print(f"Page     : {r['page']}")
            print(f"Content  : {r['content'][:500]}{'...' if len(r['content']) > 500 else ''}")
            print("-" * 90)


# Quick test when running directly
if __name__ == "__main__":
    retriever = DocSenseRetriever()

    print("=== DocSense AI - Access Control Test ===\n")

    # Test 1: HR / Credentialing user
    print("HR User (only sees Human Resources folders):")
    hr_results = retriever.retrieve(
        query="What are the nurse credentialing requirements?",
        allowed_folders=["Departments/Human Resources"],
        n_results=6
    )
    retriever.print_results(hr_results)

    print("\n" + "="*100 + "\n")

    # Test 2: Technology / Admin user
    print("Tech User (only sees Technology folders):")
    tech_results = retriever.retrieve(
        query="What is the high level architecture of DocSense AI?",
        allowed_folders=["Technology and Digital Initiatives"],
        n_results=5
    )
    retriever.print_results(tech_results)
