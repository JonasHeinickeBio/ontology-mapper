"""
Integration tests for API service interactions with comprehensive mocking.
Tests BioPortal and OLS service integration scenarios.
"""

import logging
import unittest
from unittest.mock import MagicMock, patch

import pytest
import requests

from services.bioportal import BioPortalLookup
from services.comparator import ResultComparator
from services.ols import OLSLookup

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.api
class TestServiceAPIIntegration(unittest.TestCase):
    """Integration tests for service API interactions"""

    def setUp(self):
        """Set up test fixtures"""
        logger.debug("Setting up test fixtures")
        self.api_key = "test_api_key"
        # Don't create service instances here - they need to be created after mocks are applied

    def _create_service_instances(self):
        """Create service instances after mocks are applied"""
        return BioPortalLookup(self.api_key), OLSLookup()

    @patch("utils.loading.LoadingBar")
    @patch("requests.get")
    def test_parallel_service_calls_integration(self, mock_requests_get, mock_loading):
        """Test parallel calls to both services"""
        logger.info("Testing parallel service calls integration")

        # Create service instances after mocks are applied
        bioportal = BioPortalLookup("test_api_key")
        ols = OLSLookup()

        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
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

        # Mock OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
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

        # Configure mock to return different responses based on URL
        def mock_response(url, *args, **kwargs):
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            hostname = parsed_url.hostname

            if hostname and hostname.endswith("bioontology.org"):
                return mock_bp_response
            elif hostname and hostname.endswith("ebi.ac.uk"):
                return mock_ols_response
            else:
                # Default response
                return mock_bp_response

        mock_requests_get.side_effect = mock_response

        logger.debug("Calling BioPortal search")
        bp_results = bioportal.search("diabetes", ontologies="MONDO")
        logger.debug(f"BioPortal results: {bp_results}")

        logger.debug("Calling OLS search")
        ols_results = ols.search("diabetes", ontologies="MONDO")
        logger.debug(f"OLS results: {ols_results}")

        # Debug output
        logger.debug(f"Requests mock called: {mock_requests_get.called}")
        logger.debug(f"Requests mock call count: {mock_requests_get.call_count}")
        logger.debug(f"BioPortal results count: {len(bp_results)}")
        logger.debug(f"OLS results count: {len(ols_results)}")

        # Verify both services returned results
        if len(bp_results) == 0:
            logger.error("BioPortal returned no results")
        if len(ols_results) == 0:
            logger.error("OLS returned no results")

        self.assertGreater(len(bp_results), 0)
        self.assertGreater(len(ols_results), 0)  # Verify API calls were made
        self.assertEqual(mock_requests_get.call_count, 2)  # Both services called

        # Verify result structure
        self.assertIn("uri", bp_results[0])
        self.assertIn("label", bp_results[0])
        self.assertIn("source", bp_results[0])
        self.assertEqual(bp_results[0]["source"], "bioportal")

        self.assertIn("uri", ols_results[0])
        self.assertIn("label", ols_results[0])
        self.assertIn("source", ols_results[0])
        self.assertEqual(ols_results[0]["source"], "ols")

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    @patch("services.ols.requests.get")
    def test_service_result_comparison_integration(
        self, mock_ols_get, mock_bioportal_get, mock_loading
    ):
        """Test comparison of results from both services"""
        logger.info("Testing service result comparison integration")

        # Create service instances after mocks are applied
        bioportal, ols = self._create_service_instances()

        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Hypertension",
                    "@id": "http://purl.obolibrary.org/obo/HP_0000822",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/HP"},
                }
            ]
        }
        mock_bioportal_get.return_value = mock_bp_response

        # Mock OLS response with different result
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "High blood pressure",
                        "iri": "http://purl.obolibrary.org/obo/HP_0000822",
                        "ontology_name": "hp",
                    }
                ]
            }
        }
        mock_ols_get.return_value = mock_ols_response

        logger.debug("Calling BioPortal search for comparison")
        bp_results = bioportal.search("hypertension")
        logger.debug(f"BioPortal results: {bp_results}")

        logger.debug("Calling OLS search for comparison")
        ols_results = ols.search("hypertension")
        logger.debug(f"OLS results: {ols_results}")

        # Test result comparison
        comparison = ResultComparator.compare_results(bp_results, ols_results, "hypertension")
        logger.debug(f"Comparison result: {comparison}")

        # Verify comparison structure
        self.assertIn("bioportal_count", comparison)
        self.assertIn("ols_count", comparison)
        self.assertIn("common_terms", comparison)
        self.assertIn("bioportal_only", comparison)
        self.assertIn("ols_only", comparison)

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_bioportal_demo_mode_integration(self, mock_bioportal_get, mock_loading):
        """Test BioPortal demo mode when no API key is provided"""
        logger.info("Testing BioPortal demo mode integration")
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Test with demo API key
        demo_lookup = BioPortalLookup(api_key="your_api_key_here")

        logger.debug("Calling BioPortal search in demo mode")
        results = demo_lookup.search("test")
        logger.debug(f"Demo mode results: {results}")

        # Verify demo results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "bioportal_demo")
        self.assertIn("Demo:", results[0]["label"])

        # Verify no actual API call was made
        mock_bioportal_get.assert_not_called()

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    def test_bioportal_api_key_validation_integration(self, mock_bioportal_get, mock_loading):
        """Test BioPortal API key validation"""
        logger.info("Testing BioPortal API key validation integration")
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock unauthorized response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Unauthorized")
        mock_bioportal_get.return_value = mock_response

        # Test with invalid API key
        invalid_lookup = BioPortalLookup(api_key="invalid_key")

        logger.debug("Calling BioPortal search with invalid API key")
        results = invalid_lookup.search("test")
        logger.debug(f"Results with invalid API key: {results}")

        # Should return empty results on authentication failure
        self.assertEqual(len(results), 0)
        mock_bioportal_get.assert_called_once()

    @patch("utils.loading.LoadingBar")
    @patch("services.ols.requests.get")
    def test_ols_ontology_conversion_integration(self, mock_ols_get, mock_loading):
        """Test OLS ontology name conversion from BioPortal format"""
        logger.info("Testing OLS ontology conversion integration")

        # Create service instances after mocks are applied
        bioportal, ols = self._create_service_instances()

        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock OLS response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "ontology_name": "mondo",
                    }
                ]
            }
        }
        mock_ols_get.return_value = mock_response

        logger.debug("Calling OLS search with BioPortal ontology name")
        ols.search("test", ontologies="MONDO")

        # Verify conversion happened
        mock_ols_get.assert_called_once()
        call_args = mock_ols_get.call_args
        params = call_args[1]["params"]
        logger.debug(f"OLS request params: {params}")

        # Should have converted MONDO to mondo for OLS
        if "ontology" in params:
            self.assertIn("mondo", params["ontology"])

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    @patch("services.ols.requests.get")
    def test_concurrent_api_failures_integration(
        self, mock_ols_get, mock_bioportal_get, mock_loading
    ):
        """Test handling when both APIs fail simultaneously"""
        logger.info("Testing concurrent API failures integration")

        # Create service instances after mocks are applied
        bioportal, ols = self._create_service_instances()

        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock failures for both services
        mock_bioportal_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        mock_ols_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        logger.debug("Calling BioPortal search with connection failure")
        bp_results = bioportal.search("test")
        logger.debug(f"BioPortal results on failure: {bp_results}")

        logger.debug("Calling OLS search with connection failure")
        ols_results = ols.search("test")
        logger.debug(f"OLS results on failure: {ols_results}")

        # Both should return empty results
        self.assertEqual(len(bp_results), 0)
        self.assertEqual(len(ols_results), 0)

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    @patch("services.ols.requests.get")
    def test_service_availability_check_integration(
        self, mock_ols_get, mock_bioportal_get, mock_loading
    ):
        """Test service availability checking"""
        logger.info("Testing service availability check integration")

        # Create service instances after mocks are applied
        bioportal, ols = self._create_service_instances()

        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock service unavailable responses
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 503
        mock_bp_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Service Unavailable"
        )
        mock_bioportal_get.return_value = mock_bp_response

        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 503
        mock_ols_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Service Unavailable"
        )
        mock_ols_get.return_value = mock_ols_response

        logger.debug("Calling BioPortal search with service unavailable")
        bp_results = bioportal.search("test")
        logger.debug(f"BioPortal results on service unavailable: {bp_results}")

        logger.debug("Calling OLS search with service unavailable")
        ols_results = ols.search("test")
        logger.debug(f"OLS results on service unavailable: {ols_results}")

        # Should return empty results when services are unavailable
        self.assertEqual(len(bp_results), 0)
        self.assertEqual(len(ols_results), 0)

    @patch("utils.loading.LoadingBar")
    @patch("services.bioportal.requests.get")
    @patch("services.ols.requests.get")
    def test_mixed_success_failure_integration(
        self, mock_ols_get, mock_bioportal_get, mock_loading
    ):
        """Test mixed success and failure scenarios"""
        logger.info("Testing mixed success and failure integration")

        # Create service instances after mocks are applied
        bioportal, ols = self._create_service_instances()

        # Mock loading bars
        """Test scenarios where one service succeeds and another fails"""
        logger.info("Testing mixed success/failure integration")
        # Mock loading bars
        mock_loading.return_value.start.return_value = None
        mock_loading.return_value.stop.return_value = None

        # Mock BioPortal success
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Success Term",
                    "@id": "http://purl.obolibrary.org/obo/SUCCESS_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/SUCCESS"},
                }
            ]
        }
        mock_bioportal_get.return_value = mock_bp_response

        # Mock OLS failure
        mock_ols_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        logger.debug("Calling BioPortal search (should succeed)")
        bp_results = bioportal.search("test")
        logger.debug(f"BioPortal results: {bp_results}")

        logger.debug("Calling OLS search (should fail)")
        ols_results = ols.search("test")
        logger.debug(f"OLS results: {ols_results}")

        # BioPortal should succeed
        self.assertEqual(len(bp_results), 1)
        self.assertEqual(bp_results[0]["label"], "Success Term")

        # OLS should fail gracefully
        self.assertEqual(len(ols_results), 0)


if __name__ == "__main__":
    logger.info("Starting integration tests for service API interactions")
    unittest.main()
