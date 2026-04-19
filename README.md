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
- **Storage**: Vector Database + Neo4j (Graph Database)
- **LLM**: Local models via Ollama (privacy-first)
- **Frontend**: Streamlit or lightweight React chat interface (demo)
- **Authentication & Access Control**: Google OAuth + folder-level permissions

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

The code is publicly visible so others can learn from it. However, if you modify and run this software as a service, you must make your modified source code available under the same license.

For commercial use, custom licensing, or exceptions, please contact the project owner.

---

## 📋 Project Status

- ✅ Project planning and design documents completed
- ✅ Requirements Specification & High-Level Architecture written
- ✅ Public demo knowledge base created and shared
- 🔄 Setting up repository and initial code structure
- 🔄 Building Google Drive ingestion pipeline (next)

Design documents are located in the `docs/` folder.

---

## 🚀 Getting Started (Coming Soon)

Detailed setup and installation instructions will be added once the first working prototype is ready.

---

## 📬 Contact / Commercial Inquiries

This project is being developed to improve knowledge access and compliance in home health care.

Interested in collaboration, custom development, or licensing? Feel free to reach out.

---

**Built with ❤️ for better knowledge access in home health care.**
