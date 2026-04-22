#!/usr/bin/env python3
"""
DocSense AI - Graph Builder (Enhanced for Use Case 1)
- Builds Folder hierarchy with summaries from Chroma
- Links Document nodes
- Optional light entity extraction
- Safe clear on full reset
"""

import json
from pathlib import Path
import chromadb

from langchain_neo4j import Neo4jGraph
from langchain_ollama import ChatOllama
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document

from ingestion.config import (
    EXTRACTED_FOLDER,
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
    CHROMA_PATH,
)

# ====================== CONFIG ======================
CLEAR_GRAPH_ON_RESET = True          # Set False in production if you want to keep history
ENABLE_ENTITY_EXTRACTION = True      # Light entity extraction (can be slow)
ENTITY_MODEL = "llama3.2:3b"

# Initialize Neo4j
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    refresh_schema=True
)

llm = ChatOllama(model=ENTITY_MODEL, temperature=0.0)

if ENABLE_ENTITY_EXTRACTION:
    graph_transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["Policy", "Regulation", "CredentialRequirement", "Checklist", "Department", "Document", "Section", "Folder"],
        allowed_relationships=["CONTAINS", "REFERENCES", "REQUIRES", "RELATED_TO", "BELONGS_TO_DEPARTMENT", "APPLIES_TO"],
        node_properties=True,
        relationship_properties=True,
    )

# ====================== Safe Chroma Access ======================
chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

def get_chroma_collection_safe():
    """Safe way to get or create the collection"""
    collection_name = "docsense_knowledge_base"
    try:
        return chroma_client.get_collection(name=collection_name)
    except chromadb.errors.NotFoundError:
        print(f"⚠️ Chroma collection '{collection_name}' not found. Creating it...")
        return chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"⚠️ Unexpected Chroma error: {e}")
        raise

def get_folder_summary_from_chroma(folder_path: str) -> str:
    """Query Chroma for the folder_summary chunk - fixed where clause"""
    try:
        collection = get_chroma_collection_safe()
        
        # Fixed: Use $and operator for multiple where conditions
        results = collection.get(
            where={
                "$and": [
                    {"relative_folder": folder_path},
                    {"chunk_type": "folder_summary"}
                ]
            },
            include=["documents"]
        )
        
        if results and results.get("documents"):
            summary = str(results["documents"][0])
            print(f"  ✅ Loaded summary for: {folder_path}")
            return summary[:1500]
    except Exception as e:
        print(f"  ⚠️ Could not load summary for {folder_path}: {e}")
    
    return "No summary available yet."

# ====================== Graph Building Functions ======================
def clear_existing_graph():
    """Clear the entire graph - called only when --reset-db is used"""
    print("🧹 Clearing existing graph nodes...")
    graph.query("MATCH (n) DETACH DELETE n")
    print("✅ Graph cleared.")

def create_folder_hierarchy():
    """Create hierarchical Folder nodes and attach summaries + REAL document counts."""
    print("📁 Building Folder hierarchy and loading summaries...")

    folders = {}
    for json_file in EXTRACTED_FOLDER.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        folder_path = data.get("relative_folder", ".")
        if folder_path not in folders:
            folders[folder_path] = {
                "path": folder_path,
                "name": Path(folder_path).name or "Root",
                "depth": len(Path(folder_path).parts),
                "documents_count": 0   # will be updated below
            }

    # First create/update Folder nodes with summaries
    for folder in folders.values():
        summary = get_folder_summary_from_chroma(folder["path"])
        cypher = """
        MERGE (f:Folder {path: $path})
        SET f.name = $name,
            f.depth = $depth,
            f.summary = $summary
        """
        params = {**folder, "summary": summary}
        graph.query(cypher, params)

    # Now count actual documents and update counts
    print("📊 Updating real document counts...")
    count_cypher = """
    MATCH (f:Folder)
    SET f.documents_count = size([(f)-[:CONTAINS]->(d:Document) | d])
    """
    graph.query(count_cypher)

    print(f"✅ Created/Updated {len(folders)} Folder nodes with correct document counts.")

def link_documents_to_folders():
    """Create Document nodes and link them to Folders"""
    print("📄 Linking documents to folders...")

    for json_file in EXTRACTED_FOLDER.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        doc_name = data.get("document_name")
        folder_path = data.get("relative_folder", ".")
        drive_link = data.get("drive_link")

        cypher = """
        MATCH (f:Folder {path: $folder_path})
        MERGE (d:Document {name: $doc_name})
        SET d.drive_link = $drive_link,
            d.source = $source
        MERGE (f)-[:CONTAINS]->(d)
        """
        params = {
            "doc_name": doc_name,
            "folder_path": folder_path,
            "drive_link": drive_link,
            "source": str(json_file)
        }
        graph.query(cypher, params)

    print("✅ All documents linked to their folders.")

def run_light_entity_extraction():
    """Optional: Run LLM-based entity & relationship extraction"""
    if not ENABLE_ENTITY_EXTRACTION:
        print("⏭️ Entity extraction disabled.")
        return

    print("🤖 Running light entity/relationship extraction (this may take a few minutes)...")
    documents = []
    for json_file in EXTRACTED_FOLDER.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("full_markdown", "")[:10000]
        if text.strip():
            documents.append(Document(
                page_content=text,
                metadata={
                    "document_name": data.get("document_name"),
                    "relative_folder": data.get("relative_folder")
                }
            ))

    if documents:
        graph_docs = graph_transformer.convert_to_graph_documents(documents)
        graph.add_graph_documents(
            graph_docs,
            baseEntityLabel=True,
            include_source=True
        )
        print(f"✅ Added entities & relationships from {len(graph_docs)} documents.")
    else:
        print("⚠️ No documents found for entity extraction.")

def build_graph(reset_db: bool = False):
    """Main entry point"""
    print("🕸️ Starting enhanced GraphRAG build (optimized for Use Case 1)...")

    if reset_db and CLEAR_GRAPH_ON_RESET:
        clear_existing_graph()

    create_folder_hierarchy()
    link_documents_to_folders()
    run_light_entity_extraction()

    print("\n🎉 Knowledge Graph successfully built!")
    print(" → Folder hierarchy + summaries + document links ready for Use Case 1")
    print(" → Neo4j Browser: http://localhost:7474")
    print(" → Test query: MATCH (f:Folder) RETURN f.path, f.summary, f.documents_count LIMIT 15")

if __name__ == "__main__":
    build_graph(reset_db=False)
