#!/usr/bin/env python3
"""
DocSense AI - Main Orchestrator
Routes queries and now includes a relevance threshold for search mode.
"""

from typing import List, Optional, Dict
from langchain_ollama import ChatOllama
from ingestion.hybrid_retriever import HybridRetriever
from ingestion.kb_overview import KBOverviewEngine
from ingestion.query_router import QueryRouter

class DocSenseOrchestrator:
    def __init__(self):
        self.router = QueryRouter()
        self.overview_engine = KBOverviewEngine()
        self.hybrid_retriever = HybridRetriever()
        self.llm = ChatOllama(model="llama3.1:8b", temperature=0.1)
        self.min_relevance_score = 0.45   # ← Tune this if needed (0.4–0.55 is typical)

    def query(self, user_query: str, allowed_folders: Optional[List[str]] = None) -> Dict:
        decision = self.router.route(user_query, allowed_folders)

        if decision.use_case == "knowledge-based discovery":
            answer = self.overview_engine.get_accessible_overview(user_query, allowed_folders)
            return {
                "answer": answer,
                "use_case": "knowledge-based discovery",
                "sources": []
            }
        else:
            # Use Case 2: Document Search
            raw_results = self.hybrid_retriever.retrieve(user_query, allowed_folders, n_results=10)
            
            # NEW: Filter by minimum relevance score
            relevant_results = [r for r in raw_results if r.get("score", 0) >= self.min_relevance_score]

            if not relevant_results:
                answer = "I couldn't find any relevant documents in your authorized folders for this query."
            else:
                answer = self._format_search_response(user_query, relevant_results)
            
            return {
                "answer": answer,
                "use_case": "search",
                "results": raw_results
            }

    def _format_search_response(self, query: str, results: List[Dict]) -> str:
        """Generate a clean, useful response with per-document summaries."""
        if not results:
            return "No relevant documents found."

        context = "Relevant documents:\n\n"
        for i, r in enumerate(results[:5], 1):
            doc_name = r.get("document_name", "Unnamed document")
            folder = r.get("folder", "Unknown folder")
            score = r.get("score", 0)
            preview = (r.get("content", "")[:500] + "...") if len(r.get("content", "")) > 500 else r.get("content", "")

            context += f"{i}. **{doc_name}** (Folder: {folder}, Relevance: {score:.3f})\n"
            context += f"   Preview: {preview}\n\n"

        system_prompt = """
You are DocSense AI, a helpful assistant for home health agencies.
Given a user query and relevant document excerpts, write a clear and professional response.
- Summarize the key information that answers the query.
- Mention the most relevant documents by name and briefly explain their usefulness.
- Use bullet points when helpful.
- Be concise but informative.
"""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User query: {query}\n\nRelevant documents:\n{context}"}
        ])

        return response.content.strip()
