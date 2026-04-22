#!/usr/bin/env python3
"""
DocSense AI - Knowledge-Based Discovery Engine
Strict, direct, and honest responses. No hallucinated gaps.
"""

from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain_neo4j import Neo4jGraph
from ingestion.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

class KBOverviewEngine:
    def __init__(self):
        self.graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD
        )
        self.llm = ChatOllama(model="llama3.1:8b", temperature=0.0)

    def get_accessible_overview(self, query: str, allowed_folders: Optional[List[str]] = None) -> str:
        folders = self._get_accessible_folders(allowed_folders)
        
        if not folders:
            return "You currently have access to no documents."

        context = "Accessible content:\n"
        for f in folders:
            context += f"• {f['path']} — {f['documents_count']} documents\n"
            if f.get('summary') and f['summary'] != "No summary available yet.":
                context += f"  {f['summary']}\n"

        system_prompt = """
You are DocSense AI, a precise assistant for home health agencies.

Answer the user's question DIRECTLY using ONLY the authorized context.

Special rule for "gaps" or "missing" questions:
- If the user asks about gaps, ONLY say what is clearly missing from the provided context.
- If you cannot confidently identify real gaps, respond exactly with this sentence: 
  "I can only analyze the documents currently in the knowledge base. I do not have enough information to identify specific gaps."
- NEVER invent or list missing policies, forms, checklists, or procedures that are not explicitly absent from all documents.
- Do not say "there appears to be a gap" unless you are certain.

For all other questions:
- Be concise and factual.
- List folders with document counts when relevant.
- Never add unsolicited advice or sections.
"""

        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"}
        ])

        return response.content.strip()

    def _get_accessible_folders(self, allowed_folders: Optional[List[str]]) -> List[dict]:
        if allowed_folders is None:
            where_clause = ""
            params = {}
        else:
            where_clause = "WHERE ANY(allowed IN $allowed_folders WHERE f.path STARTS WITH allowed OR f.path = allowed)"
            params = {"allowed_folders": allowed_folders}

        cypher = f"""
        MATCH (f:Folder)
        {where_clause}
        RETURN 
            f.path AS path, 
            size([(f)-[:CONTAINS]->(d) | d]) AS documents_count,
            f.summary AS summary
        ORDER BY f.depth
        """

        results = self.graph.query(cypher, params)
        return [dict(record) for record in results]
