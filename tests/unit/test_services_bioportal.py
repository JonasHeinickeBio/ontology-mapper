"""
Unit tests for services/bioportal.py module.
"""

import os
import unittest
from unittest.mock import Mock, patch

import requests

from services.bioportal import BioPortalLookup


class TestBioPortalLookup(unittest.TestCase):
    """Unit tests for BioPortalLookup class"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.bioportal = BioPortalLookup(self.api_key)

    def test_bioportal_lookup_init_with_api_key(self):
        """Test BioPortalLookup initialization with API key"""
        bp = BioPortalLookup("custom_key")
        self.assertEqual(bp.api_key, "custom_key")
        self.assertEqual(bp.base_url, "https://data.bioontology.org/search")

    def test_bioportal_lookup_init_without_api_key(self):
        """Test BioPortalLookup initialization without API key"""
        with patch.dict("os.environ", {}, clear=True):
            bp = BioPortalLookup()
            self.assertIsNone(bp.api_key)

    @patch.dict("os.environ", {"BIOPORTAL_API_KEY": "env_key"})
    def test_bioportal_lookup_init_from_env(self):
        """Test BioPortalLookup initialization from environment variable"""
        bp = BioPortalLookup()
        self.assertEqual(bp.api_key, "env_key")

    def test_search_demo_mode_no_api_key(self):
        """Test search in demo mode when no API key is provided"""
        with patch.dict(os.environ, {}, clear=True):
            bp = BioPortalLookup(None)
            results = bp.search("test query")

            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["source"], "bioportal_demo")
            self.assertIn("Demo: test query", results[0]["label"])

    def test_search_demo_mode_invalid_api_key(self):
        """Test search in demo mode with invalid API key"""
        bp = BioPortalLookup("your_api_key_here")
        results = bp.search("covid")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "bioportal_demo")

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_with_valid_api_key(self, mock_get, mock_loading_bar):
        """Test search with valid API key"""
        # Mock loading bar
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "COVID-19",
                    "@id": "http://purl.obolibrary.org/obo/MONDO_0100096",
                    "definition": ["A disease caused by SARS-CoV-2"],
                    "synonym": ["SARS-CoV-2 infection"],
                    "links": {"ontology": "http://data.bioontology.org/ontologies/MONDO"},
                }
            ]
        }
        mock_get.return_value = mock_response

        results = self.bioportal.search("covid")

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("params", call_args.kwargs)
        params = call_args.kwargs["params"]
        self.assertEqual(params["q"], "covid")
        self.assertEqual(params["apikey"], self.api_key)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["label"], "COVID-19")
        self.assertEqual(results[0]["source"], "bioportal")

        # Verify loading bar usage
        mock_bar.start.assert_called_once()
        mock_bar.stop.assert_called_once()

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_with_ontologies_filter(self, mock_get, mock_loading_bar):
        """Test search with ontologies filter"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"collection": []}
        mock_get.return_value = mock_response

        self.bioportal.search("term", ontologies="HP,MONDO", max_results=10)

        # Verify API call parameters
        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        self.assertEqual(params["ontologies"], "HP,MONDO")
        self.assertEqual(params["pagesize"], 10)

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_api_error_handling(self, mock_get, mock_loading_bar):
        """Test search handles API errors gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock API error
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        results = self.bioportal.search("test")

        # Should return empty list on error
        self.assertEqual(results, [])

        # Should manage loading bar (start and stop at least once)
        mock_bar.start.assert_called_once()
        self.assertTrue(mock_bar.stop.called)

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_timeout_handling(self, mock_get, mock_loading_bar):
        """Test search handles timeouts gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock timeout
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        results = self.bioportal.search("test")

        # Should return empty list on timeout
        self.assertEqual(results, [])

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_http_error_handling(self, mock_get, mock_loading_bar):
        """Test search handles HTTP errors gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        results = self.bioportal.search("test")

        # Should return empty list on HTTP error
        self.assertEqual(results, [])

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_malformed_response(self, mock_get, mock_loading_bar):
        """Test search handles malformed JSON response"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock malformed response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        results = self.bioportal.search("test")

        # Should return empty list on JSON error
        self.assertEqual(results, [])

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_missing_collection_key(self, mock_get, mock_loading_bar):
        """Test search handles response missing collection key"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response without collection key
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"no_collection": "here"}
        mock_get.return_value = mock_response

        results = self.bioportal.search("test")

        # Should return empty list when collection is missing
        self.assertEqual(results, [])

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_result_extraction(self, mock_get, mock_loading_bar):
        """Test search result extraction and processing"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with detailed result
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Hypertension",
                    "@id": "http://purl.obolibrary.org/obo/HP_0000822",
                    "definition": ["High blood pressure"],
                    "synonym": ["High blood pressure", "HTN"],
                    "links": {"ontology": "http://data.bioontology.org/ontologies/HP"},
                }
            ]
        }
        mock_get.return_value = mock_response

        results = self.bioportal.search("hypertension")

        # Verify result structure
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["uri"], "http://purl.obolibrary.org/obo/HP_0000822")
        self.assertEqual(result["label"], "Hypertension")
        self.assertEqual(result["ontology"], "HP")
        self.assertEqual(result["description"], "High blood pressure")
        self.assertEqual(result["synonyms"], ["High blood pressure", "HTN"])
        self.assertEqual(result["source"], "bioportal")

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_empty_fields_handling(self, mock_get, mock_loading_bar):
        """Test search handles empty or missing fields gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with minimal data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Test Term",
                    "@id": "http://example.org/test",
                    # Missing definition, synonym, and links
                }
            ]
        }
        mock_get.return_value = mock_response

        results = self.bioportal.search("test")

        # Should handle missing fields gracefully
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["label"], "Test Term")
        self.assertEqual(result["description"], "")
        self.assertEqual(result["synonyms"], [])
        self.assertEqual(result["ontology"], "")

    def test_logger_usage(self):
        """Test logger is used correctly"""
        # Test that logger exists in the module
        from services.bioportal import logger

        self.assertIsNotNone(logger)

    def test_base_url_configuration(self):
        """Test base URL is configured correctly"""
        bp = BioPortalLookup()
        self.assertEqual(bp.base_url, "https://data.bioontology.org/search")

    @patch("services.bioportal.LoadingBar")
    @patch("requests.get")
    def test_search_default_parameters(self, mock_get, mock_loading_bar):
        """Test search uses correct default parameters"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"collection": []}
        mock_get.return_value = mock_response

        self.bioportal.search("test")

        # Verify default parameters
        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        self.assertEqual(params["q"], "test")
        self.assertEqual(params["pagesize"], 5)  # default max_results
        self.assertEqual(params["format"], "json")

    def test_module_docstring(self):
        """Test module has appropriate docstring"""
        import services.bioportal as bp_module

        docstring = bp_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("BioPortal API client", docstring)

    def test_class_docstring(self):
        """Test BioPortalLookup class has appropriate docstring"""
        docstring = BioPortalLookup.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("BioPortal API", docstring)


if __name__ == "__main__":
    unittest.main()
