# testing/test_edge_cases.py
"""
Tests for unusual or boundary conditions.
"""

def test_retrieval_with_very_short_query(retriever):
    results = retriever.retrieve("a", allowed_folders=None, n_results=5)
    assert len(results) <= 5
    print("✅ Short query handled gracefully")


def test_retrieval_with_special_characters(retriever):
    results = retriever.retrieve("HIPAA & Medicare CoPs?!", allowed_folders=None, n_results=5)
    assert isinstance(results, list)
    print("✅ Special characters in query handled")
