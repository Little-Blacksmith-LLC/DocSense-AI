#!/usr/bin/env python3
"""
DocSense AI - Hybrid Retriever (Vector + GraphRAG)
Improved version with better error handling and dynamic relationship discovery.
"""

from typing import List, Dict, Optional
import chromadb
from langchain_ollama import OllamaEmbeddings
from langchain_neo4j import Neo4jGraph   # Updated import

from ingestion.config import CHROMA_PATH

class HybridRetriever:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        
        # Vector DB
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_collection("docsense_knowledge_base")
        
        # Graph DB - update password if changed
        self.graph = Neo4jGraph(
            url="bolt://localhost:7687",
            username="neo4j",
            password="password123"   # ← CHANGE TO YOUR ACTUAL NEO4J PASSWORD
        )

    def retrieve(self, 
                 query: str, 
                 allowed_folders: Optional[List[str]] = None, 
                 n_results: int = 8) -> List[Dict]:
        """
        Hybrid retrieval: Vector search first, then optional graph expansion.
        """
        print(f"🔍 Hybrid query: '{query}' | Allowed folders: {allowed_folders}")

        # Step 1: Vector search with access control
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=n_results * 3,
            include=["metadatas", "documents", "distances"]
        )

        documents = vector_results["documents"][0]
        metadatas = vector_results["metadatas"][0]
        distances = vector_results["distances"][0]

        filtered = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            folder = meta.get("relative_folder", "")
            if allowed_folders is None or any(folder.startswith(allowed) for allowed in allowed_folders or []):
                filtered.append({
                    "content": doc,
                    "metadata": meta,
                    "score": 1 - dist,
                    "document_name": meta.get("document_name"),
                    "folder": folder,
                    "drive_link": meta.get("drive_link"),
                    "chunk_type": meta.get("chunk_type", "text"),
                })

        filtered = sorted(filtered, key=lambda x: x["score"], reverse=True)[:n_results]

        # Step 2: Graph expansion (more forgiving)
        if filtered:
            try:
                doc_names = [r["document_name"] for r in filtered]
                
                # More flexible Cypher - discover actual relationships
                cypher = """
                MATCH (d:Document)-[r*1..2]-(related)
                WHERE d.document_name IN $doc_names
                RETURN DISTINCT related, type(r[0]) as relationship_type, d.document_name as source_doc
                LIMIT 30
                """
                graph_results = self.graph.query(cypher, {"doc_names": doc_names})
                
                print(f"🕸️ Graph expansion found {len(graph_results)} related nodes")
                if graph_results:
                    print(f"   Example relationships: {[r.get('relationship_type') for r in graph_results[:5]]}")
            except Exception as e:
                print(f"⚠️ Graph expansion skipped: {e}")

        return filtered

    def print_results(self, results: List[Dict]):
        for i, r in enumerate(results, 1):
            print(f"Result {i} | Score: {r['score']:.4f} | {r.get('document_name')}")
            print(f"Folder: {r.get('folder')}")
            if r.get('drive_link'):
                print(f"Drive Link: {r['drive_link']}")
            print(f"Content preview: {r['content'][:250]}...")
            print("-" * 90)
