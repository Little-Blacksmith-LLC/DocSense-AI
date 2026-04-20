# testing/conftest.py
"""
Shared fixtures and constants for DocSense AI tests.

This file contains reusable test fixtures (like the retriever) and 
common test data (folder paths, thresholds) so we don't repeat them 
across test files.
"""

import pytest
from ingestion.retrieval import DocSenseRetriever

# ========================= CONSTANTS =========================
SIMILARITY_THRESHOLD = 0.40
"""
Recommended similarity threshold for nomic-embed-text on our regulatory 
and credentialing documents. Tuned based on real nonsense query scores.
Lower = more results (risk of noise). Higher = stricter relevance.
"""

@pytest.fixture(scope="session")
def retriever():
    """
    Returns a DocSenseRetriever instance shared across all tests in the session.
    
    Scope="session" means it's created once per test run for better performance.
    """
    print("🔧 Setting up shared DocSenseRetriever for tests...")
    return DocSenseRetriever()


@pytest.fixture
def real_tech_folders():
    """Realistic folder paths for Technology users (used in access control tests)."""
    return [
        "Technology and Digital Initiatives",
        "06_Technology_and_Digital_Initiatives"
    ]


@pytest.fixture
def real_hr_folders():
    """Realistic folder paths for Human Resources / Credentialing users."""
    return [
        "Departments/Human Resources",
        "02_Departments"
    ]
    
    
@pytest.fixture
def similarity_threshold():
    """Central similarity threshold used for relevance filtering."""
    return SIMILARITY_THRESHOLD
