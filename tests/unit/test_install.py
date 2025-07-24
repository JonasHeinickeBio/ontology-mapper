#!/usr/bin/env python3
"""
Test exactly like the failing test
"""

import logging
import unittest
from unittest.mock import MagicMock, patch

from services.bioportal import BioPortalLookup
from services.ols import OLSLookup

# Configure logging for debugging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestParallelServiceCalls(unittest.TestCase):
    """Test parallel service calls exactly like failing test"""

    def setUp(self):
        """Set up test fixtures"""
        logger.debug("Setting up test fixtures")
        self.api_key = "test_api_key"
        self.bioportal = BioPortalLookup(self.api_key)
        self.ols = OLSLookup()

    @patch("utils.loading.LoadingBar")
    @patch("requests.get")
    def test_parallel_service_calls_integration(self, mock_requests_get, mock_loading):
        """Test parallel calls to both services"""
        logger.info("Testing parallel service calls integration")

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
                return mock_bp_response

        mock_requests_get.side_effect = mock_response

        logger.debug("Calling BioPortal search")
        bp_results = self.bioportal.search("diabetes", ontologies="MONDO")
        logger.debug(f"BioPortal results: {bp_results}")

        logger.debug("Calling OLS search")
        ols_results = self.ols.search("diabetes", ontologies="MONDO")
        logger.debug(f"OLS results: {ols_results}")

        # Debug output
        logger.debug(f"Requests mock called: {mock_requests_get.called}")
        logger.debug(f"Requests mock call count: {mock_requests_get.call_count}")
        logger.debug(f"BioPortal results count: {len(bp_results)}")
        logger.debug(f"OLS results count: {len(ols_results)}")

        # Show the issue
        print(f"Requests mock called: {mock_requests_get.called}")
        print(f"Requests mock call count: {mock_requests_get.call_count}")
        print(f"BioPortal results count: {len(bp_results)}")
        print(f"OLS results count: {len(ols_results)}")

        # Verify both services returned results
        self.assertGreater(len(bp_results), 0)
        self.assertGreater(len(ols_results), 0)


if __name__ == "__main__":
    unittest.main()
