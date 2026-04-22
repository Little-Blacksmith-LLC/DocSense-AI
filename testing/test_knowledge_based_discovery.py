"""
DocSense AI - Knowledge-Based Discovery Tests
Focused tests for knowledge-based discovery mode (formerly Use Case 1).
Tests routing, response quality, and honest handling of access + gaps questions.

Usage:

# Run with visible output
pytest testing/test_knowledge_based_discovery.py -v -s

# Or just the routing tests
pytest testing/test_knowledge_based_discovery.py::test_knowledge_based_discovery_routing -v
"""

import pytest
from ingestion.orchestrator import DocSenseOrchestrator

@pytest.fixture(scope="module")
def orchestrator():
    """Shared orchestrator for knowledge-based discovery tests"""
    return DocSenseOrchestrator()


@pytest.mark.parametrize("query, role, description", [
    ("What do I have access to right now?", 
     "Human Resources / Credentialing", 
     "HR role - basic access discovery"),

    ("Summarize the knowledge base I can see", 
     "Human Resources / Credentialing", 
     "HR role - summarize accessible content"),

    ("What gaps exist in my credentialing materials?", 
     "Human Resources / Credentialing", 
     "HR role - gaps within authorized scope"),

    ("Give me a full overview of the knowledge base", 
     "All (Admin/Full Access)", 
     "Admin - full knowledge base discovery"),

    ("What folders and documents are available to me?", 
     "Technology and Digital Initiatives", 
     "Tech role - access discovery"),
])
def test_knowledge_based_discovery_routing(orchestrator, query, role, description):
    """
    Test that the router correctly routes to knowledge-based discovery mode.
    """
    print(f"\n🧪 Testing: {description}")

    ROLE_TO_FOLDERS = {
        "All (Admin/Full Access)": None,
        "Human Resources / Credentialing": ["Departments/Human Resources", "02_Departments", "Human Resources", "Credentialing"],
        "Technology and Digital Initiatives": ["Technology and Digital Initiatives", "06_Technology_and_Digital_Initiatives", "DocSense AI"],
    }
    allowed_folders = ROLE_TO_FOLDERS[role]

    result = orchestrator.query(user_query=query, allowed_folders=allowed_folders)

    assert result.get("use_case") == "knowledge-based discovery", \
        f"Expected 'knowledge-based discovery', got '{result.get('use_case')}' for query: {query}"

    print(f"✅ Correctly routed to knowledge-based discovery mode")


def test_knowledge_based_discovery_response_quality(orchestrator):
    """
    Visual inspection test for knowledge-based discovery responses.
    Prints the actual response + a simple LLM evaluation so you can review quality.
    """
    print("\n🧪 Running visual knowledge-based discovery response quality test")

    test_cases = [
        ("What do I have access to right now?", "Human Resources / Credentialing"),
        ("Summarize the knowledge base I can see", "Human Resources / Credentialing"),
        ("What gaps exist in my credentialing materials?", "Human Resources / Credentialing"),
        ("Give me a full overview of the knowledge base", "All (Admin/Full Access)"),
    ]

    evaluator_llm = orchestrator.overview_engine.llm

    for query, role in test_cases:
        ROLE_TO_FOLDERS = {
            "All (Admin/Full Access)": None,
            "Human Resources / Credentialing": ["Departments/Human Resources", "Human Resources", "Credentialing"],
        }
        allowed_folders = ROLE_TO_FOLDERS.get(role)

        print(f"\n{'='*90}")
        print(f"Question: {query}")
        print(f"Role: {role}")
        print(f"{'='*90}")

        result = orchestrator.query(query, allowed_folders)
        
        print("\nResponse:")
        print(result.get("answer", "No answer returned"))
        print("\nMode detected:", result.get("use_case"))

        # Simple LLM self-evaluation of the response
        eval_prompt = f"""
Evaluate this response for a knowledge-based discovery question.
Question: {query}
Response: {result.get('answer', '')}

Rate 1-5 on:
- Directness: Does it answer the exact question asked?
- Relevance: Does it stay focused on authorized content?
- Honesty: Does it properly acknowledge limitations (especially for gaps)?

Give a short 1-2 sentence assessment.
"""

        eval_response = evaluator_llm.invoke(eval_prompt)
        print("\nLLM Evaluation:")
        print(eval_response.content)
        print("-" * 80)


def test_gaps_question_handling(orchestrator):
    """
    Specifically test how 'gaps' questions are handled in knowledge-based discovery mode.
    The system should acknowledge its limitations rather than hallucinate external gaps.
    """
    print("\n🧪 Testing gaps question handling in knowledge-based discovery mode")

    query = "What gaps exist in my credentialing materials?"
    allowed_folders = ["Departments/Human Resources", "Human Resources", "Credentialing"]

    result = orchestrator.query(query, allowed_folders)

    assert result.get("use_case") == "knowledge-based discovery", \
        "Gaps question should be routed to knowledge-based discovery mode"

    answer = result.get("answer", "").lower()

    # More flexible check for honest limitation language
    limitation_phrases = [
        "cannot", 
        "limited", 
        "only analyze", 
        "only have access", 
        "within the knowledge base", 
        "based on the documents", 
        "do not have enough information", 
        "i cannot identify specific gaps"
    ]

    assert any(phrase in answer for phrase in limitation_phrases), \
        f"Response should honestly acknowledge limitations. Got: {answer[:400]}..."

    print("✅ Gaps question correctly handled in knowledge-based discovery mode")
    print("Response preview:", result.get("answer", "")[:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""))
    
