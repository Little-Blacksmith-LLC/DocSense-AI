#!/usr/bin/env python3
"""
DocSense AI - Query Router
Decides between knowledge-based discovery and search.
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from langchain_ollama import ChatOllama

class QueryDecision(BaseModel):
    use_case: Literal["knowledge-based discovery", "search"] = Field(...)
    confidence: float
    reasoning: str

class QueryRouter:
    def __init__(self):
        self.llm = ChatOllama(model="llama3.2:3b", temperature=0.0)

    def route(self, query: str, allowed_folders: Optional[List[str]]) -> QueryDecision:
        prompt = f"""
You must classify the user question into exactly one of these two categories:

1. "knowledge-based discovery" → if the question is about:
   - what the user has access to
   - summarizing the knowledge base
   - what folders/documents are available
   - gaps or limitations within the authorized content
   - any broad inventory or overview of the KB

2. "search" → if the question is a specific how-to, fact lookup, or detailed request from documents.

Examples of knowledge-based discovery:
- What do I have access to right now?
- Summarize the knowledge base I can see
- What gaps exist in my credentialing materials?
- Give me a full overview of the knowledge base
- What folders and documents are available to me?

Question: "{query}"

Respond with **valid JSON only**, no extra text:
{{"use_case": "knowledge-based discovery" or "search", "confidence": number between 0 and 1, "reasoning": "one short sentence"}}
"""

        response = self.llm.invoke(prompt)
        
        try:
            import json
            content = response.content.strip()
            
            # Clean possible markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()

            data = json.loads(content)
            decision = QueryDecision(**data)
            
            # Force correct term if LLM still outputs old one
            if decision.use_case == "overview":
                decision.use_case = "knowledge-based discovery"
                
            return decision
            
        except Exception as e:
            print(f"Router parsing error: {e}. Falling back using keywords.")
            
            # Stronger keyword fallback
            lower = query.lower()
            if any(word in lower for word in ["access to", "have access", "summarize the knowledge", "overview of the knowledge", "gaps exist", "folders are available", "what is in the knowledge base"]):
                return QueryDecision(use_case="knowledge-based discovery", confidence=0.75, reasoning="Strong keyword match for discovery")
            else:
                return QueryDecision(use_case="search", confidence=0.6, reasoning="Fallback to search")
