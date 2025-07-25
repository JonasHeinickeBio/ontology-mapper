"""
Test configuration and fixtures
"""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_ttl_content():
    """Sample TTL content for testing"""
    return """
@prefix : <http://example.org/ontology#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

:Disease a owl:Class ;
    rdfs:label "Disease" ;
    rdfs:comment "A disease or disorder" .

:long_covid a :Disease ;
    rdfs:label "Long COVID" ;
    rdfs:comment "Long-term effects of COVID-19" .

:fatigue a owl:Class ;
    rdfs:label "Fatigue" ;
    rdfs:comment "Extreme tiredness" .
"""


@pytest.fixture
def sample_concepts_file(temp_dir):
    """Create a sample concepts file for batch testing"""
    concepts_file = temp_dir / "concepts.txt"
    concepts_file.write_text("breast cancer\ndiabetes mellitus\nhypertension\n")
    return concepts_file


@pytest.fixture
def mock_bioportal_response():
    """Mock BioPortal API response"""
    return {
        "collection": [
            {
                "@id": "http://purl.obolibrary.org/obo/MONDO_0007254",
                "prefLabel": "breast cancer",
                "definition": ["A cancer that forms in tissues of the breast."],
                "synonym": ["mammary cancer", "breast neoplasm"],
                "links": {"ontology": "http://data.bioontology.org/ontologies/MONDO"},
            }
        ]
    }


@pytest.fixture
def mock_ols_response():
    """Mock OLS API response"""
    return {
        "response": {
            "docs": [
                {
                    "iri": "http://purl.obolibrary.org/obo/MONDO_0007254",
                    "label": "breast cancer",
                    "description": ["A cancer that forms in tissues of the breast."],
                    "synonym": ["mammary cancer", "breast neoplasm"],
                    "ontology_name": "MONDO",
                }
            ]
        }
    }


@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    original_env = os.environ.copy()
    os.environ["BIOPORTAL_API_KEY"] = "test_api_key"
    yield
    os.environ.clear()
    os.environ.update(original_env)
