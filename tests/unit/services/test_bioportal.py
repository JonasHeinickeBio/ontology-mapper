"""
Unit tests for services.bioportal module.
"""

import json
import logging
import os
import unittest
from unittest.mock import Mock, patch

import pytest
import requests

from services.bioportal import BioPortalLookup
from utils.loading import LoadingBar


@pytest.mark.unit
@pytest.mark.api
class TestBioPortalLookup(unittest.TestCase):
    """Test cases for BioPortalLookup class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)
        self.api_key = "test_api_key"
        self.lookup = BioPortalLookup(self.api_key)

    def test_init_with_api_key(self):
        """Test BioPortalLookup initialization with API key."""
        self.assertEqual(self.lookup.api_key, self.api_key)

    def test_init_without_api_key(self):
        """Test BioPortalLookup initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            lookup = BioPortalLookup()
            self.assertIsNone(lookup.api_key)

    def test_init_with_none_api_key(self):
        """Test BioPortalLookup initialization with None API key."""
        with patch.dict(os.environ, {}, clear=True):
            lookup = BioPortalLookup(api_key=None)
            self.assertIsNone(lookup.api_key)

    def test_search_success(self):
        """Test successful search."""
        # Mock successful response with collection
        mock_response_data = {
            "collection": [
                {
                    "prefLabel": "Test Term",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                }
            ]
        }

        with patch("services.bioportal.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            result = self.lookup.search("test")

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(
                result[0]["label"], "Test Term"
            )  # The service returns "label", not "prefLabel"
            self.assertEqual(result[0]["uri"], "http://purl.obolibrary.org/obo/TEST_0001")
            self.assertEqual(result[0]["source"], "bioportal")

    @patch("services.bioportal.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_search_http_error(self, mock_get, mock_loading_bar):
        """Test search with HTTP error."""
        mock_loading_bar_instance = Mock()
        mock_loading_bar.return_value = mock_loading_bar_instance

        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Unauthorized")
        mock_get.return_value = mock_response

        with patch("services.bioportal.logger") as mock_logger:
            result = self.lookup.search("test")

        self.assertEqual(result, [])
        mock_logger.error.assert_called()
        mock_loading_bar_instance.stop.assert_called()

    @patch("services.bioportal.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_search_connection_error(self, mock_get, mock_loading_bar):
        """Test search with connection error."""
        mock_loading_bar_instance = Mock()
        mock_loading_bar.return_value = mock_loading_bar_instance

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with patch("services.bioportal.logger") as mock_logger:
            result = self.lookup.search("test")

        self.assertEqual(result, [])
        mock_logger.error.assert_called()
        mock_loading_bar_instance.stop.assert_called()

    @patch("services.bioportal.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_search_json_decode_error(self, mock_get, mock_loading_bar):
        """Test search with JSON decode error."""
        mock_loading_bar_instance = Mock()
        mock_loading_bar.return_value = mock_loading_bar_instance

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        with patch("services.bioportal.logger") as mock_logger:
            result = self.lookup.search("test")

        self.assertEqual(result, [])
        mock_logger.error.assert_called()
        mock_loading_bar_instance.stop.assert_called()

    @patch("services.bioportal.requests.get")
    def test_search_malformed_response(self, mock_get):
        """Test search with malformed response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_get.return_value = mock_response

        result = self.lookup.search("test")

        self.assertEqual(result, [])  # Should return empty list for malformed response

    @patch("services.bioportal.requests.get")
    def test_search_empty_response(self, mock_get):
        """Test search with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"collection": []}
        mock_get.return_value = mock_response

        result = self.lookup.search("test")

        self.assertEqual(result, [])

    @patch("services.bioportal.requests.get")
    def test_search_no_collection_in_response(self, mock_get):
        """Test search with no collection in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = self.lookup.search("test")

        self.assertEqual(result, [])  # Should return empty list when no collection

    @patch("services.bioportal.requests.get")
    def test_search_none_response(self, mock_get):
        """Test search with None response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        with patch("services.bioportal.logger") as mock_logger:
            result = self.lookup.search("test")

        self.assertEqual(result, [])
        mock_logger.error.assert_called()

    @patch("services.bioportal.requests.get")
    def test_search_request_exception(self, mock_get):
        """Test search with request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Request failed")

        with patch("services.bioportal.logger") as mock_logger:
            result = self.lookup.search("test")

        self.assertEqual(result, [])
        mock_logger.error.assert_called()

    @patch("services.bioportal.requests.get")
    def test_search_processing_error(self, mock_get):
        """Test search with processing error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"collection": [{}]}  # Empty concept
        mock_get.return_value = mock_response

        # This should not raise an exception
        result = self.lookup.search("test")
        self.assertIsInstance(result, list)

    @patch("services.bioportal.requests.get")
    def test_search_multiple_results(self, mock_get):
        """Test search with multiple results."""
        mock_response_data = {
            "collection": [
                {
                    "prefLabel": "Test Term 1",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                },
                {
                    "prefLabel": "Test Term 2",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0002",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                },
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        result = self.lookup.search("test")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["label"], "Test Term 1")  # The service returns "label"
        self.assertEqual(result[1]["label"], "Test Term 2")  # The service returns "label"

    @patch("services.bioportal.requests.get")
    def test_search_with_ontology_filter(self, mock_get):
        """Test search with ontology filter."""
        mock_response_data = {
            "collection": [
                {
                    "prefLabel": "Test Term",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                }
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        result = self.lookup.search("test", ontologies="TEST")  # Pass string, not list

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        mock_get.assert_called_once()
        # Check that the ontologies parameter was passed
        call_args = mock_get.call_args
        self.assertIn("ontologies", call_args[1]["params"])


if __name__ == "__main__":
    unittest.main()
