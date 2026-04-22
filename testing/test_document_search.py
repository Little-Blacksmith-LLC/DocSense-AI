"""
DocSense AI - Document Search Tests (Use Case 2)
Comprehensive tests with quality scoring for formatted responses.
"""

import pytest
from ingestion.orchestrator import DocSenseOrchestrator

@pytest.fixture(scope="module")
def orchestrator():
    return DocSenseOrchestrator()


@pytest.mark.parametrize("query, role, expected_min_results, description", [
    ("How do you do nurse credentialing?", "Human Resources / Credentialing", 2, "HR credentialing search"),
    ("What is the high level architecture of DocSense AI?", "Technology and Digital Initiatives", 1, "DocSense architecture search"),
    ("What are the Medicare Conditions of Participation for home health agencies?", "Human Resources / Credentialing", 1, "Medicare CoPs search"),
])
def test_document_search_routing_and_results(orchestrator, query, role, expected_min_results, description):
    print(f"\n🧪 Testing: {description}")

    ROLE_TO_FOLDERS = {
        "All (Admin/Full Access)": None,
        "Human Resources / Credentialing": ["Departments/Human Resources", "Human Resources", "Credentialing"],
        "Technology and Digital Initiatives": ["Technology and Digital Initiatives", "06_Technology_and_Digital_Initiatives", "DocSense AI"],
    }
    allowed_folders = ROLE_TO_FOLDERS[role]

    result = orchestrator.query(user_query=query, allowed_folders=allowed_folders)

    assert result.get("use_case") == "search"
    results = result.get("results", [])
    assert len(results) >= expected_min_results

    print(f"✅ Search mode returned {len(results)} results")


def test_search_formatted_response_quality(orchestrator):
    """Tests quality of the nicely formatted search response."""
    print("\n🧪 Testing formatted search response quality + LLM scoring")

    test_cases = [
        ("How do you do nurse credentialing?", "Human Resources / Credentialing"),
        ("What is the high level architecture of DocSense AI?", "Technology and Digital Initiatives"),
        ("What are the Medicare Conditions of Participation for home health agencies?", "Human Resources / Credentialing"),
    ]

    evaluator = orchestrator.llm

    for query, role in test_cases:
        ROLE_TO_FOLDERS = {
            "All (Admin/Full Access)": None,
            "Human Resources / Credentialing": ["Departments/Human Resources", "Human Resources", "Credentialing"],
            "Technology and Digital Initiatives": ["Technology and Digital Initiatives", "06_Technology_and_Digital_Initiatives", "DocSense AI"],
        }
        allowed_folders = ROLE_TO_FOLDERS.get(role)

        print(f"\n{'='*90}")
        print(f"Query: {query}")
        print(f"Role: {role}")
        print(f"{'='*90}")

        result = orchestrator.query(query, allowed_folders)
        answer = result.get("answer", "")

        print("Response:\n", answer[:700] + "..." if len(answer) > 700 else answer)

        # LLM quality evaluation
        eval_prompt = f"""
Evaluate this search response for quality:
Question: {query}
Response: {answer}

Rate 1-5 on:
- Directness and usefulness
- Clarity and structure
- Relevance to the query
- Proper use of sources

Give a short assessment.
"""
        eval_result = evaluator.invoke(eval_prompt)
        print("\nLLM Quality Score:")
        print(eval_result.content)
        print("-" * 80)


def test_search_no_results_handling(orchestrator):
    print("\n🧪 Testing no-results handling")
    result = orchestrator.query("How do I build a rocket to Mars?", 
                                allowed_folders=["Departments/Human Resources", "Human Resources", "Credentialing"])
    assert result.get("use_case") == "search"
    answer = result.get("answer", "").lower()
    assert any(phrase in answer for phrase in ["couldn't find", "no relevant", "no documents"]), \
        f"Expected graceful no-results message. Got: {answer[:200]}"
    print("✅ No-results handled gracefully")


def test_search_vs_discovery_separation(orchestrator):
    print("\n🧪 Testing mode separation")
    search = orchestrator.query("How do you perform nurse credentialing step by step?", 
                                ["Departments/Human Resources", "Human Resources", "Credentialing"])
    discovery = orchestrator.query("What do I have access to right now?", 
                                   ["Departments/Human Resources", "Human Resources", "Credentialing"])
    assert search.get("use_case") == "search"
    assert discovery.get("use_case") == "knowledge-based discovery"
    print("✅ Mode separation is working correctly")
