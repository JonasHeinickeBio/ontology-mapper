"""
Unit tests for services.ols module.
"""

import json
import logging
import unittest
from unittest.mock import Mock, patch

import pytest
import requests

from services.ols import OLSLookup


@pytest.mark.unit
@pytest.mark.api
class TestOLSLookup(unittest.TestCase):
    """Test cases for OLSLookup class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)
        self.lookup = OLSLookup()

    def test_init(self):
        """Test OLSLookup initialization."""
        self.assertEqual(self.lookup.base_url, "https://www.ebi.ac.uk/ols/api/search")

    def test_search_success(self):
        """Test successful search."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "COVID-19",
                            "iri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                            "description": ["A disease caused by SARS-CoV-2"],
                            "synonym": ["SARS-CoV-2 infection"],
                            "ontology_name": "mondo",
                            "id": "MONDO:0100096",
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response

            result = self.lookup.search("COVID-19")

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["label"], "COVID-19")
            self.assertEqual(result[0]["uri"], "http://purl.obolibrary.org/obo/MONDO_0100096")
            self.assertEqual(result[0]["ontology"], "MONDO")
            self.assertEqual(result[0]["source"], "ols")

    def test_search_with_ontology_filter(self):
        """Test search with ontology filter."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test", ontologies="mondo,hp")

            # Verify ontology parameter was passed
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertIn("ontology", call_args[1]["params"])
            self.assertEqual(call_args[1]["params"]["ontology"], "mondo,hp")

    def test_search_with_max_results(self):
        """Test search with max results parameter."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test", max_results=10)

            # Verify rows parameter was passed
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args[1]["params"]["rows"], 10)

    def test_search_http_error(self):
        """Test search with HTTP error."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "Server error"
            )
            mock_get.return_value = mock_response

            with patch("services.ols.logger") as mock_logger:
                result = self.lookup.search("test")

            self.assertEqual(result, [])
            mock_logger.error.assert_called()
            mock_loading_bar_instance.stop.assert_called()  # Just check it was called

    def test_search_connection_error(self):
        """Test search with connection error."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            with patch("services.ols.logger") as mock_logger:
                result = self.lookup.search("test")

            self.assertEqual(result, [])
            mock_logger.error.assert_called()
            mock_loading_bar_instance.stop.assert_called()  # Just check it was called

    def test_search_json_decode_error(self):
        """Test search with JSON decode error."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
            mock_get.return_value = mock_response

            with patch("services.ols.logger") as mock_logger:
                result = self.lookup.search("test")

            self.assertEqual(result, [])
            mock_logger.error.assert_called()
            mock_loading_bar_instance.stop.assert_called()  # Just check it was called

    def test_search_empty_response(self):
        """Test search with empty response."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            result = self.lookup.search("nonexistent")

            self.assertEqual(result, [])
            mock_loading_bar_instance.start.assert_called_once()
            mock_loading_bar_instance.stop.assert_called_once()

    def test_search_url_construction(self):
        """Test that search URL and parameters are constructed correctly."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test query")

            # Verify URL construction
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertEqual(call_args[0][0], self.lookup.base_url)

            # Verify parameters
            params = call_args[1]["params"]
            self.assertEqual(params["q"], "test query")
            self.assertEqual(params["format"], "json")

    def test_search_default_parameters(self):
        """Test that default parameters are set correctly."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test")

            # Verify default parameters
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            self.assertEqual(params["rows"], 5)
            self.assertEqual(params["format"], "json")

    def test_search_timeout_parameter(self):
        """Test that timeout parameter is set correctly."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test")

            # Verify timeout parameter
            call_args = mock_get.call_args
            self.assertEqual(call_args[1]["timeout"], 30)

    def test_search_response_parsing(self):
        """Test that response is parsed correctly."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "Test Term",
                            "iri": "http://purl.obolibrary.org/obo/TEST_123",
                            "description": ["Test description"],
                            "synonym": ["test synonym"],
                            "ontology_name": "test_ontology",
                            "id": "TEST:123",
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response

            result = self.lookup.search("test")

            self.assertEqual(len(result), 1)
            term = result[0]
            self.assertEqual(term["label"], "Test Term")
            self.assertEqual(term["uri"], "http://purl.obolibrary.org/obo/TEST_123")
            self.assertEqual(term["ontology"], "TEST_ONTOLOGY")
            self.assertEqual(term["source"], "ols")
            self.assertEqual(term["description"], "Test description")
            self.assertEqual(term["synonyms"], ["test synonym"])

    def test_search_missing_fields(self):
        """Test handling of missing fields in response."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "Test Term",
                            "iri": "http://purl.obolibrary.org/obo/TEST_123",
                            "ontology_name": "test_ontology",
                            # Missing description and synonym
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response

            result = self.lookup.search("test")

            self.assertEqual(len(result), 1)
            term = result[0]
            self.assertEqual(term["label"], "Test Term")
            self.assertEqual(term["description"], "")
            self.assertEqual(term["synonyms"], [])

    def test_search_with_loading_bar_usage(self):
        """Test that loading bar is used correctly."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": {"docs": []}}
            mock_get.return_value = mock_response

            self.lookup.search("test")

            # Verify loading bar was used
            mock_loading_bar.assert_called_once()
            mock_loading_bar_instance.start.assert_called_once()
            mock_loading_bar_instance.stop.assert_called_once()

    def test_search_ontology_name_upper_case(self):
        """Test that ontology name is converted to uppercase."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": {
                    "docs": [
                        {
                            "label": "Test Term",
                            "iri": "http://purl.obolibrary.org/obo/TEST_123",
                            "ontology_name": "lowercase_ontology",
                        }
                    ]
                }
            }
            mock_get.return_value = mock_response

            result = self.lookup.search("test")

            self.assertEqual(result[0]["ontology"], "LOWERCASE_ONTOLOGY")

    def test_search_malformed_response(self):
        """Test handling of malformed response structure."""
        with (
            patch("services.ols.requests.get") as mock_get,
            patch("services.ols.LoadingBar") as mock_loading_bar,
        ):
            mock_loading_bar_instance = Mock()
            mock_loading_bar.return_value = mock_loading_bar_instance

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"invalid": "structure"}
            mock_get.return_value = mock_response

            result = self.lookup.search("test")

            self.assertEqual(result, [])  # Should return empty list for malformed response


if __name__ == "__main__":
    unittest.main()
