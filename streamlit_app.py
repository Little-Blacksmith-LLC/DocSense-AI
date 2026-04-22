#!/usr/bin/env python3
"""
DocSense AI - Streamlit Chat Interface (Updated with Orchestrator + Use Case 1)
"""
import streamlit as st
from langchain_ollama import ChatOllama

# New imports for Use Case 1 + routing
from ingestion.orchestrator import DocSenseOrchestrator

st.set_page_config(page_title="DocSense AI", page_icon="🩺", layout="wide")

# ========================= SESSION STATE =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = DocSenseOrchestrator()

# ========================= SIDEBAR =========================
st.sidebar.title("🩺 DocSense AI")
st.sidebar.markdown("**Private Knowledge Assistant** for Home Health Agencies")

# Model selector
available_models = ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b", "llama3.2:11b-vision"]
selected_model = st.sidebar.selectbox("LLM Model", available_models, index=0)

llm = ChatOllama(
    model=selected_model,
    temperature=0.1,
    max_tokens=2048,
    num_ctx=8192
)

# Role / Access Control
role = st.sidebar.selectbox(
    "Your Role (Access Control)",
    options=[
        "All (Admin/Full Access)",
        "Human Resources / Credentialing",
        "Technology and Digital Initiatives",
        "Clinical Operations",
        "Company Overview Only"
    ]
)

ROLE_TO_FOLDERS = {
    "All (Admin/Full Access)": None,
    "Human Resources / Credentialing": ["Departments/Human Resources", "02_Departments", "Human Resources", "Credentialing"],
    "Technology and Digital Initiatives": ["Technology and Digital Initiatives", "06_Technology_and_Digital_Initiatives", "DocSense AI"],
    "Clinical Operations": ["Clinical Operations", "Policies and Procedures", "Regulatory Guidance"],
    "Company Overview Only": ["Company Overview"]
}

allowed_folders = ROLE_TO_FOLDERS[role]

st.sidebar.success(f"Access: {'All documents' if allowed_folders is None else role}")
st.sidebar.markdown("---")
st.sidebar.info("Access control filters results based on folder paths.\n\nTry different roles to see the difference.")

# ========================= MAIN CHAT =========================
st.title("🩺 DocSense AI")
st.caption("Ask questions about credentialing, policies, regulations, clinical protocols, or the system itself.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources", expanded=False):
                for s in msg["sources"]:
                    st.markdown(f"• **{s.get('document_name', 'Document')}** — `{s.get('folder', '')}`")

if prompt := st.chat_input("Ask anything about nurse credentialing, Medicare CoPs, what I have access to, or DocSense architecture..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(f"Thinking with {selected_model}..."):
            try:
                # Use the new orchestrator
                result = st.session_state.orchestrator.query(
                    user_query=prompt,
                    allowed_folders=allowed_folders
                )

                answer = result.get("answer", "Sorry, I couldn't process that request.")
                use_case = result.get("use_case", "search")
                sources = result.get("results", []) if use_case == "search" else []

                # Show use case indicator (helpful during development)
                if use_case == "overview":
                    st.info("📋 **Overview Mode** — Showing what you have access to")
                else:
                    st.caption("🔍 Search Mode")

                st.markdown(answer)

                # Show sources for search mode
                if sources and use_case == "search":
                    with st.expander("📚 Sources & Citations", expanded=True):
                        for i, s in enumerate(sources, 1):
                            link = s.get("drive_link")
                            if link:
                                st.markdown(
                                    f"**{i}. [{s.get('document_name', 'Document')}]({link})**\n"
                                    f"Folder: `{s.get('folder', '')}`\n"
                                    f"Relevance: `{s.get('score', 0):.3f}`"
                                )
                            else:
                                st.markdown(
                                    f"**{i}. {s.get('document_name', 'Document')}**\n"
                                    f"Folder: `{s.get('folder', '')}`"
                                )

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Tip: Make sure the selected model is pulled with `ollama pull <model>`")

st.caption("Local-only • Access-controlled • Built for Home Health Agencies")
