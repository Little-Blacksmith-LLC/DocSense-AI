# testing/test_retrieval.py
"""
DocSense AI - Retrieval Layer Tests

This is the core test file for the retrieval system.
It validates:
- Vector search with ChromaDB
- Folder-based Access Control (critical Phase 1 requirement)
- Relevance filtering using similarity threshold
- Prevention of unauthorized data leakage between departments
- Self-referential queries about the DocSense AI project itself
"""

import pytest
from ingestion.retrieval import DocSenseRetriever


def test_retriever_initialization(retriever):
    """
    Basic health check for the retrieval system.
    
    Ensures ChromaDB is connected and contains data after ingestion.
    """
    assert retriever is not None
    count = retriever.collection.count()
    print(f"✅ Chroma collection has {count:,} chunks")
    assert count > 1000, f"Only {count} chunks found — run full ingestion first"


@pytest.mark.parametrize("query, allowed_folders, expected_min_results, description, similarity_threshold", [
    ("nurse credentialing requirements", ["Departments/Human Resources"], 2,
     "HR credentialing query", 0.4),
    ("What is the high level architecture of DocSense AI?", 
     ["Technology and Digital Initiatives", "06_Technology_and_Digital_Initiatives"], 1,
     "DocSense architecture (self-referential)", 0.4),
    ("HIPAA compliance or Medicare CoPs", None, 3,
     "Unrestricted regulatory query", 0.4),
    ("nurse checklist forms", ["Departments/Human Resources/Credentialing and Compliance"], 2,
     "Nested HR folder access", 0.4),
    ("something completely unrelated xyz123 nonsense query purple elephant", None, 0,
     "Nonsense query — should return zero after threshold", 0.4),
])
def test_retrieve_with_access_control(retriever, query, allowed_folders, expected_min_results, description, similarity_threshold):
    """
    Core test for semantic retrieval + access control.
    
    Tests that:
    - Relevant results are returned
    - Access control filters folders correctly
    - Low-relevance results are filtered out using similarity threshold
    """
    print(f"\n🧪 Testing: {description}")
    results = retriever.retrieve(query, allowed_folders=allowed_folders, n_results=12)

    assert isinstance(results, list)

    # Enforce access control
    for r in results:
        folder = r.get("folder", "")
        if allowed_folders:
            assert any(folder.startswith(allowed) for allowed in allowed_folders), \
                   f"❌ Unauthorized folder leaked: {folder} (query: {query})"

    # Filter by similarity threshold
    high_quality = [r for r in results if r.get("score", 0) >= similarity_threshold]

    if expected_min_results > 0:
        assert len(high_quality) >= expected_min_results, \
               f"Expected ≥{expected_min_results} good results for '{query}' (got {len(high_quality)})"
        print(f"✅ {len(high_quality)} high-quality results (score ≥ {similarity_threshold})")
    else:
        assert len(high_quality) == 0, \
               f"Nonsense query returned {len(high_quality)} results above threshold"
        print("✅ Nonsense query correctly filtered to zero high-quality results")
        
        
def test_access_control_strict_filtering(retriever, real_hr_folders, similarity_threshold):
    """
    Strict security test: HR users must NOT see any Technology documents.
    
    This is a strong "catch" test to protect department-level separation.
    It verifies that access control is enforced even when the query is
    clearly related to Technology / DocSense AI content.
    """
    print("\n🧪 Testing: Strict HR access control (should block Tech content)")

    results = retriever.retrieve(
        query="DocSense AI high level architecture",
        allowed_folders=real_hr_folders,
        n_results=8
    )

    for r in results:
        folder_lower = r["folder"].lower()
        assert not any(term in folder_lower for term in ["technology", "digital", "architecture and technical"]), \
               f"❌ HR user saw Technology content: {r['folder']}"

    print(f"✅ Strict HR access control passed — {len(results)} results returned, all authorized")


def test_retrieve_nonsense_query_distribution(retriever, similarity_threshold):
    """
    Diagnostic test: Shows actual similarity scores for completely unrelated queries.
    
    Purpose:
    - Helps tune the SIMILARITY_THRESHOLD for nomic-embed-text on your specific dataset.
    - Verifies that low-quality matches are properly filtered out.
    - Acts as a safety net against excessive false positives.
    """
    print("\n🧪 Testing: Nonsense query score distribution (diagnostic)")

    nonsense_query = "purple flying elephant dancing on mars xyz123"

    results = retriever.retrieve(nonsense_query, allowed_folders=None, n_results=10)

    scores = [r.get("score", 0) for r in results]

    print(f"🔍 Nonsense query top scores: {[round(s, 4) for s in scores]}")
    print(f"   Max score: {max(scores):.4f} | Threshold used: {similarity_threshold}")

    high_quality_count = sum(1 for s in scores if s >= similarity_threshold)

    # We allow a small number of false positives (max 3) because vector search always returns something
    assert high_quality_count <= 3, \
        f"Too many false positives ({high_quality_count}) at threshold {similarity_threshold}. " \
        f"Consider raising the threshold."

    print(f"✅ Only {high_quality_count} false positives — good noise filtering")
    
    
def test_access_control_empty_folders(retriever):
    """Test that empty allowed_folders list returns no results."""
    results = retriever.retrieve(
        query="nurse credentialing",
        allowed_folders=[],   # explicitly empty
        n_results=5
    )
    assert len(results) == 0, "Empty allowed_folders should return zero results"
    print("✅ Empty allowed_folders correctly returns no results")


def test_access_control_none_vs_empty(retriever):
    """None should allow everything, empty list should allow nothing."""
    query = "credentialing requirements"
    
    results_none = retriever.retrieve(query, allowed_folders=None, n_results=5)
    results_empty = retriever.retrieve(query, allowed_folders=[], n_results=5)
    
    assert len(results_none) > 0
    assert len(results_empty) == 0
    print("✅ None vs empty allowed_folders behavior is correct")


def test_retrieval_with_different_n_results(retriever, real_hr_folders):
    """Test boundary values for n_results parameter."""
    query = "nurse credentialing requirements"
    
    for n in [1, 5, 20]:
        results = retriever.retrieve(query, allowed_folders=real_hr_folders, n_results=n)
        assert len(results) <= n
        assert all(r.get("score", 0) > 0 for r in results)
    print("✅ n_results parameter behaves correctly across different values")


def test_retrieval_score_ordering(retriever):
    """Results should be returned in descending score order."""
    results = retriever.retrieve("credentialing", allowed_folders=None, n_results=10)
    
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), "Results are not sorted by score descending"
    print("✅ Results are correctly sorted by similarity score (descending)")
