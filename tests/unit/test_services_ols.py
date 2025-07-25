"""
Unit tests for services/ols.py module.
"""

import unittest
from unittest.mock import Mock, patch

import requests

from services.ols import OLSLookup


class TestOLSLookup(unittest.TestCase):
    """Unit tests for OLSLookup class"""

    def setUp(self):
        """Set up test fixtures"""
        self.ols = OLSLookup()

    def test_ols_lookup_init(self):
        """Test OLSLookup initialization"""
        ols = OLSLookup()
        self.assertEqual(ols.base_url, "https://www.ebi.ac.uk/ols/api/search")

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_basic(self, mock_get, mock_loading_bar):
        """Test basic search functionality"""
        # Mock loading bar
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "iri": "http://purl.obolibrary.org/obo/HP_0000822",
                        "label": "Hypertension",
                        "ontology_name": "hp",
                        "description": ["High blood pressure"],
                        "synonym": ["High BP", "HTN"],
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        results = self.ols.search("hypertension")

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("params", call_args.kwargs)
        params = call_args.kwargs["params"]
        self.assertEqual(params["q"], "hypertension")
        self.assertEqual(params["rows"], 5)  # default max_results
        self.assertEqual(params["format"], "json")

        # Verify results
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["uri"], "http://purl.obolibrary.org/obo/HP_0000822")
        self.assertEqual(result["label"], "Hypertension")
        self.assertEqual(result["ontology"], "HP")
        self.assertEqual(result["description"], "High blood pressure")
        self.assertEqual(result["synonyms"], ["High BP", "HTN"])
        self.assertEqual(result["source"], "ols")

        # Verify loading bar usage
        mock_bar.start.assert_called_once()
        mock_bar.stop.assert_called_once()

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_with_ontologies_filter(self, mock_get, mock_loading_bar):
        """Test search with ontologies filter"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"docs": []}}
        mock_get.return_value = mock_response

        self.ols.search("term", ontologies="hp,mondo", max_results=10)

        # Verify API call parameters
        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        self.assertEqual(params["rows"], 10)
        # Note: ontology parameter handling depends on _convert_ontologies

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_api_error_handling(self, mock_get, mock_loading_bar):
        """Test search handles API errors gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock API error
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        results = self.ols.search("test")

        # Should return empty list on error
        self.assertEqual(results, [])

        # Should manage loading bar (start and stop at least once)
        mock_bar.start.assert_called_once()
        self.assertTrue(mock_bar.stop.called)

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_timeout_handling(self, mock_get, mock_loading_bar):
        """Test search handles timeouts gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock timeout
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        results = self.ols.search("test")

        # Should return empty list on timeout
        self.assertEqual(results, [])

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_http_error_handling(self, mock_get, mock_loading_bar):
        """Test search handles HTTP errors gracefully"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        results = self.ols.search("test")

        # Should return empty list on HTTP error
        self.assertEqual(results, [])

    @patch("services.ols.LoadingBar")
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

        results = self.ols.search("test")

        # Should return empty list on JSON error
        self.assertEqual(results, [])

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_missing_response_structure(self, mock_get, mock_loading_bar):
        """Test search handles response missing expected structure"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response without expected structure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"unexpected": "structure"}
        mock_get.return_value = mock_response

        results = self.ols.search("test")

        # Should return empty list when structure is unexpected
        self.assertEqual(results, [])

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_empty_docs(self, mock_get, mock_loading_bar):
        """Test search handles empty docs list"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with empty docs
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"docs": []}}
        mock_get.return_value = mock_response

        results = self.ols.search("test")

        # Should return empty list
        self.assertEqual(results, [])

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_minimal_doc_data(self, mock_get, mock_loading_bar):
        """Test search handles docs with minimal data"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with minimal doc data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "iri": "http://example.org/test",
                        "label": "Test Term",
                        # Missing ontology_name, description, synonym
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        results = self.ols.search("test")

        # Should handle missing fields gracefully
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["uri"], "http://example.org/test")
        self.assertEqual(result["label"], "Test Term")
        self.assertEqual(result["ontology"], "")  # Should default to empty string
        self.assertEqual(result["description"], "")
        self.assertEqual(result["synonyms"], [])

    def test_convert_ontologies_method(self):
        """Test _convert_ontologies method exists and handles input"""
        # Test the method exists
        self.assertTrue(hasattr(self.ols, "_convert_ontologies"))

        # Test with valid input (implementation may vary)
        result = self.ols._convert_ontologies("HP,MONDO")
        self.assertIsInstance(result, str)

    @patch("services.ols.BIOPORTAL_TO_OLS_MAPPING", {"HP": "hp", "MONDO": "mondo"})
    def test_convert_ontologies_mapping(self):
        """Test ontology name conversion"""
        # Test conversion of known mappings
        result = self.ols._convert_ontologies("HP,MONDO")
        # Result should contain converted names
        self.assertIsInstance(result, str)

    def test_convert_ontologies_empty_input(self):
        """Test _convert_ontologies with empty input"""
        result = self.ols._convert_ontologies("")
        # Should handle empty input gracefully
        self.assertIsInstance(result, str)

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_timeout_parameter(self, mock_get, mock_loading_bar):
        """Test search uses correct timeout parameter"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"docs": []}}
        mock_get.return_value = mock_response

        self.ols.search("test")

        # Verify timeout is set
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs["timeout"], 30)

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_result_extraction_detailed(self, mock_get, mock_loading_bar):
        """Test detailed result extraction and processing"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with detailed result
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "iri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                        "label": "COVID-19",
                        "ontology_name": "mondo",
                        "description": ["A disease caused by SARS-CoV-2"],
                        "synonym": ["SARS-CoV-2 infection", "2019-nCoV"],
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        results = self.ols.search("covid")

        # Verify result structure
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["uri"], "http://purl.obolibrary.org/obo/MONDO_0100096")
        self.assertEqual(result["label"], "COVID-19")
        self.assertEqual(result["ontology"], "MONDO")
        self.assertEqual(result["description"], "A disease caused by SARS-CoV-2")
        self.assertEqual(result["synonyms"], ["SARS-CoV-2 infection", "2019-nCoV"])
        self.assertEqual(result["source"], "ols")

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_multiple_results(self, mock_get, mock_loading_bar):
        """Test search handles multiple results"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        # Mock response with multiple results
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "iri": "http://example.org/test1",
                        "label": "Test 1",
                        "ontology_name": "test",
                    },
                    {
                        "iri": "http://example.org/test2",
                        "label": "Test 2",
                        "ontology_name": "test",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        results = self.ols.search("test")

        # Should return multiple results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["label"], "Test 1")
        self.assertEqual(results[1]["label"], "Test 2")

    def test_logger_usage(self):
        """Test logger is used correctly"""
        # Test that logger exists in the module
        from services.ols import logger

        self.assertIsNotNone(logger)

    def test_base_url_configuration(self):
        """Test base URL is configured correctly"""
        ols = OLSLookup()
        self.assertEqual(ols.base_url, "https://www.ebi.ac.uk/ols/api/search")

    def test_module_docstring(self):
        """Test module has appropriate docstring"""
        import services.ols as ols_module

        docstring = ols_module.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("OLS API client", docstring)

    def test_class_docstring(self):
        """Test OLSLookup class has appropriate docstring"""
        docstring = OLSLookup.__doc__
        self.assertIsNotNone(docstring)
        if docstring:
            self.assertIn("OLS", docstring)

    @patch("services.ols.LoadingBar")
    @patch("requests.get")
    def test_search_default_parameters(self, mock_get, mock_loading_bar):
        """Test search uses correct default parameters"""
        mock_bar = Mock()
        mock_loading_bar.return_value = mock_bar

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": {"docs": []}}
        mock_get.return_value = mock_response

        self.ols.search("test")

        # Verify default parameters
        call_args = mock_get.call_args
        params = call_args.kwargs["params"]
        self.assertEqual(params["q"], "test")
        self.assertEqual(params["rows"], 5)  # default max_results
        self.assertEqual(params["format"], "json")


if __name__ == "__main__":
    unittest.main()
