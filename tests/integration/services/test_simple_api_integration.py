"""
Simple integration test for API service interactions.
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from services.bioportal import BioPortalLookup
from services.ols import OLSLookup


@pytest.mark.integration
@pytest.mark.api
class TestSimpleAPIIntegration(unittest.TestCase):
    """Simple integration tests for API services"""

    def setUp(self):
        """Set up test fixtures"""
        self.bioportal = BioPortalLookup("test_api_key")
        self.ols = OLSLookup()

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_bioportal_search_integration(self, mock_bioportal_get, mock_loading):
        """Test BioPortal search integration"""
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock BioPortal response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Diabetes mellitus",
                    "@id": "http://purl.obolibrary.org/obo/MONDO_0005015",
                    "definition": ["A metabolic disorder"],
                    "links": {"ontology": "http://data.bioontology.org/ontologies/MONDO"},
                }
            ]
        }
        mock_bioportal_get.return_value = mock_response

        # Test search
        results = self.bioportal.search("diabetes", ontologies="MONDO")

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "bioportal")
        self.assertEqual(results[0]["label"], "Diabetes mellitus")
        self.assertIn("uri", results[0])

    @patch("utils.loading.LoadingBar")
    @patch("services.ols.requests.get")
    def test_ols_search_integration(self, mock_ols_get, mock_loading):
        """Test OLS search integration"""
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock OLS response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Diabetes mellitus",
                        "iri": "http://purl.obolibrary.org/obo/MONDO_0005015",
                        "description": ["A metabolic disorder"],
                        "ontology_name": "mondo",
                    }
                ]
            }
        }
        mock_ols_get.return_value = mock_response

        # Test search
        results = self.ols.search("diabetes", ontologies="MONDO")

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "ols")
        self.assertEqual(results[0]["label"], "Diabetes mellitus")
        self.assertIn("uri", results[0])

    @patch("utils.loading.LoadingBar")
    def test_both_services_integration(self, mock_loading):
        """Test both services together"""
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Test BioPortal first
        with patch("services.bioportal.requests.get") as mock_bioportal_get:
            # Mock BioPortal response
            mock_bp_response = Mock()
            mock_bp_response.status_code = 200
            mock_bp_response.json.return_value = {
                "collection": [
                    {
                        "prefLabel": "Diabetes mellitus",
                        "@id": "http://purl.obolibrary.org/obo/MONDO_0005015",
                        "definition": ["A metabolic disorder"],
                        "links": {"ontology": "http://data.bioontology.org/ontologies/MONDO"},
                    }
                ]
            }
            mock_bioportal_get.return_value = mock_bp_response
            bp_results = self.bioportal.search("diabetes", ontologies="MONDO")

        # Test OLS second
        with patch("services.ols.requests.get") as mock_ols_get:
            # Mock OLS response
            mock_ols_response = Mock()
            mock_ols_response.status_code = 200
            mock_ols_response.json.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "Diabetes mellitus",
                            "iri": "http://purl.obolibrary.org/obo/MONDO_0005015",
                            "description": ["A metabolic disorder"],
                            "ontology_name": "mondo",
                        }
                    ]
                }
            }
            mock_ols_get.return_value = mock_ols_response
            ols_results = self.ols.search("diabetes")

        # Verify both returned results
        self.assertEqual(len(bp_results), 1)
        self.assertEqual(len(ols_results), 1)
        self.assertEqual(bp_results[0]["source"], "bioportal")
        self.assertEqual(ols_results[0]["source"], "ols")


if __name__ == "__main__":
    unittest.main()
