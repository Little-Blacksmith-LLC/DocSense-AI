# DocSense AI
**Intelligent Knowledge Management & Assistant for Home Health Agencies**

A private, secure **Graph RAG** powered knowledge assistant that helps any employee or contractor quickly find, understand, and connect information across internal documents.

---

## 🎯 The Challenge
Home health and nursing agencies manage thousands of pages of critical documents:
- Policies and procedures
- Regulatory guidance (Medicare CoPs, HIPAA)
- Nurse credentialing and compliance materials
- Clinical protocols
- Technology and digital transformation initiatives

Employees often spend significant time searching for the right information or trying to understand dense technical and regulatory content.

## ✅ The Solution
**DocSense AI** automatically ingests documents from Google Drive, builds a rich **knowledge graph** of entities and relationships, and lets users ask natural language questions.

It combines **semantic search** (vector database) with **relational reasoning** (graph database) to deliver accurate, sourced answers while discovering important cross-document connections.

### Key Features
- Automatic ingestion from Google Drive (recursive folder support)
- Hybrid Graph RAG retrieval (vector + graph traversal)
- Built-in **access control** — users only see documents from folders they are authorized to access
- Natural language chat interface with source citations
- Self-referential — you can even ask the system about its own design documents
- Strong focus on home health topics: nurse credentialing, compliance, clinical operations, and technology initiatives

### Example Knowledge Base
You can explore the **public demo knowledge base** used in this project here:  
→ **[Home_Health_Knowledge_Base (Google Drive)](https://drive.google.com/drive/u/1/folders/1mv-iDrQdpMw8YBVJSwK3WcSR-CfIDmnk)**

This folder contains realistic sample documents across company overview, departments (including credentialing), policies, regulatory guidance, and technology initiatives.

### Future Integration
Designed to integrate with internal tools, starting with the **Nurse Credentialing Tool** (automated checklists, expiration tracking, compliance dashboards).

---

## 📁 Knowledge Base Structure
The system expects a well-organized Google Drive folder with the following structure (see full details in `docs/knowledge_base_structure.md`):
- `01_Company_Overview/`
- `02_Departments/` (with `Credentialing_and_Compliance/`)
- `03_Projects_and_Initiatives/`
- `04_Policies_and_Procedures/`
- `05_Regulatory_Guidance_and_Resources/`
- `06_Technology_and_Digital_Initiatives/` (including `DocSense_AI_Project/`)

---

## 🛠️ Tech Stack (Planned)
- **Backend**: Python + FastAPI
- **Ingestion**: Google Drive API + LangChain/LlamaIndex
- **Storage**: Vector Database (Chroma) + Neo4j (Graph Database)
- **LLM**: Local models via Ollama (privacy-first)
- **Frontend**: Streamlit or lightweight React chat interface (demo)
- **Authentication & Access Control**: Google OAuth + folder-level permissions

---

## 🧪 Testing

DocSense AI includes a dedicated `testing/` directory with comprehensive tests to ensure reliability, especially around **access control** and the ingestion pipeline.

### What the Tests Cover
- **Retrieval & Access Control**: Validates that users can only see authorized folders (HR vs Technology separation, nested folders, etc.)
- **Text Extraction**: Checks that PDFs are correctly converted to structured Markdown + JSON with preserved folder metadata
- **Vector Store Health**: Ensures ChromaDB is properly populated with correct metadata
- **Relevance Filtering**: Tests similarity threshold behavior to reduce noise from unrelated queries

### How to Run the Tests

1. **Run Main Test Script**:
   ```bash
   ./run_full_test_pipeline.sh
   ```
