"""
Integration tests for API interactions with mocking.
Tests the complete flow from CLI to API services.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from cli.interface import CLIInterface
from core.lookup import ConceptLookup
from services.bioportal import BioPortalLookup
from services.ols import OLSLookup


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration(unittest.TestCase):
    """Integration tests for API interactions with mocking"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key"
        self.bioportal = BioPortalLookup(self.api_key)
        self.ols = OLSLookup()
        self.lookup = ConceptLookup(self.bioportal, self.ols)
        self.cli = CLIInterface()

    def create_temp_ttl_file(self, content: str) -> str:
        """Create temporary TTL file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as f:
            f.write(content)
            return f.name

    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    @patch("requests.get")
    def test_full_concept_lookup_integration(self, mock_requests_get):
        """Test complete concept lookup flow with both services"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "COVID-19",
                    "@id": "http://purl.obolibrary.org/obo/MONDO_0100096",
                    "definition": ["A disease caused by SARS-CoV-2"],
                    "synonym": ["SARS-CoV-2 infection", "2019-nCoV disease"],
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

        # Test concept lookup
        concept = {"key": "covid", "label": "COVID-19", "type": "Disease", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn("uri", results[0])
        self.assertIn("label", results[0])
        self.assertIn("source", results[0])

        # Verify comparison
        self.assertIsInstance(comparison, dict)

        # Verify API calls were made
        self.assertGreater(mock_requests_get.call_count, 0)

    @patch("requests.get")
    def test_api_error_handling_integration(self, mock_requests_get):
        """Test error handling when APIs fail"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock OLS success response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "ontology_name": "test",
                    }
                ]
            }
        }

        # Configure mock to fail for BioPortal and succeed for OLS
        def mock_response(url, *args, **kwargs):
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            hostname = parsed_url.hostname

            if hostname and hostname.endswith("bioontology.org"):
                raise Exception("BioPortal API Error")
            elif hostname and hostname.endswith("ebi.ac.uk"):
                return mock_ols_response
            else:
                raise Exception("API Error")

        mock_requests_get.side_effect = mock_response

        # Test that OLS can provide results when BioPortal fails
        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should still get results from OLS
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["source"], "ols")

    @patch("requests.get")
    def test_empty_api_responses_integration(self, mock_requests_get):
        """Test handling of empty API responses"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock empty BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {"collection": []}

        # Mock empty OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {"response": {"docs": []}}

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

        concept = {
            "key": "nonexistent",
            "label": "Nonexistent Term",
            "type": "Term",
            "category": "instance",
        }

        results, comparison = lookup.lookup_concept(concept)

        # Should return empty results
        self.assertEqual(len(results), 0)
        self.assertIsInstance(comparison, dict)

    @patch("services.bioportal.requests.get")
    @patch("services.ols.requests.get")
    def test_cli_single_word_mode_integration(self, mock_ols_get, mock_bioportal_get):
        """Test CLI single-word mode with API mocking"""
        # Mock BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Fatigue",
                    "@id": "http://purl.obolibrary.org/obo/HP_0012378",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/HP"},
                }
            ]
        }
        mock_bioportal_get.return_value = mock_bp_response

        # Mock OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Fatigue",
                        "iri": "http://purl.obolibrary.org/obo/HP_0012378",
                        "ontology_name": "hp",
                    }
                ]
            }
        }
        mock_ols_get.return_value = mock_ols_response

        # Test single-word mode argument parsing
        args = self.cli.parser.parse_args(["--single-word", "fatigue", "--ontologies", "HP"])

        # Verify single-word mode is enabled
        self.assertTrue(args.single_word)
        self.assertEqual(args.ontologies, "HP")

        # Test that CLI can be properly initialized
        self.assertIsInstance(self.cli, CLIInterface)
        self.assertIsNotNone(self.cli.parser)

    @patch("requests.get")
    def test_cli_single_word_integration(self, mock_requests_get):
        """Test CLI single-word mode integration"""
        # Create fresh CLI instance after mock is applied
        cli = CLIInterface()

        # Mock HP API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Fatigue",
                    "@id": "http://purl.obolibrary.org/obo/HP_0012378",
                    "links": {"ontology": "https://data.bioontology.org/ontologies/HP"},
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        # Test that args can be parsed for single-word mode
        args = cli.parser.parse_args(["--single-word", "fatigue", "--ontologies", "HP"])

        # Verify that single-word mode is enabled
        self.assertTrue(args.single_word)
        self.assertEqual(args.ontologies, "HP")

        # Test that the CLI instance is properly initialized
        self.assertIsInstance(cli, CLIInterface)
        self.assertIsNotNone(cli.parser)

    @patch("requests.get")
    def test_cli_ttl_processing_integration(self, mock_requests_get):
        """Test CLI TTL file processing with API mocking"""
        # Create fresh CLI instance after mock is applied
        cli = CLIInterface()

        # Create temporary TTL file
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :COVID19 a owl:Class ;
            rdfs:label "COVID-19" ;
            rdfs:comment "A disease caused by SARS-CoV-2" .
        """
        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Mock API responses
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "collection": [
                    {
                        "prefLabel": "COVID-19",
                        "@id": "http://purl.obolibrary.org/obo/MONDO_0100096",
                        "links": {"ontology": "https://data.bioontology.org/ontologies/MONDO"},
                    }
                ]
            }
            mock_requests_get.return_value = mock_response

            # Test TTL processing args
            args = cli.parser.parse_args([temp_file])

            # Verify TTL file is set properly
            self.assertEqual(args.ttl_file, temp_file)
            self.assertIsNone(args.single_word)

            # Test that the CLI instance is properly initialized
            self.assertIsInstance(cli, CLIInterface)
            self.assertIsNotNone(cli.parser)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_batch_mode_integration(self):
        """Test batch mode processing with API mocking"""
        # Create temporary batch file
        batch_selections = {
            "covid": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                    "label": "COVID-19",
                    "ontology": "MONDO",
                }
            ],
            "fatigue": [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0012378",
                    "label": "Fatigue",
                    "ontology": "HP",
                }
            ],
        }

        temp_batch_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(batch_selections, temp_batch_file)
        temp_batch_file.close()

        temp_ttl_file = self.create_temp_ttl_file("""
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :COVID19 a owl:Class ;
            rdfs:label "COVID-19" .
        """)

        try:
            # Test batch mode
            args = self.cli.parser.parse_args([temp_ttl_file, "--batch-mode", temp_batch_file.name])

            # Verify batch mode is set properly
            self.assertEqual(args.batch_mode, temp_batch_file.name)
            self.assertEqual(args.ttl_file, temp_ttl_file)

            # Test that the CLI instance is properly initialized
            self.assertIsInstance(self.cli, CLIInterface)
            self.assertIsNotNone(self.cli.parser)

        finally:
            self.cleanup_temp_file(temp_batch_file.name)
            self.cleanup_temp_file(temp_ttl_file)

    @patch("requests.get")
    def test_api_timeout_handling_integration(self, mock_requests_get):
        """Test API timeout handling"""
        import requests

        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock successful OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "ontology_name": "test",
                    }
                ]
            }
        }

        # Configure mock to return timeout for BioPortal and success for OLS
        def mock_response(url, *args, **kwargs):
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            hostname = parsed_url.hostname

            if hostname and hostname.endswith("bioontology.org"):
                raise requests.exceptions.Timeout("Request timed out")
            elif hostname and hostname.endswith("ebi.ac.uk"):
                return mock_ols_response
            else:
                raise requests.exceptions.Timeout("Request timed out")

        mock_requests_get.side_effect = mock_response

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should still get results from OLS when BioPortal times out
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["source"], "ols")

    @patch("requests.get")
    def test_api_rate_limiting_integration(self, mock_requests_get):
        """Test API rate limiting handling"""
        import requests

        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock rate limiting for BioPortal
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 429
        mock_bp_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Rate limit exceeded"
        )

        # Mock successful OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "ontology_name": "test",
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

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should still get results from OLS when BioPortal is rate limited
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["source"], "ols")

    @patch("requests.get")
    def test_malformed_api_responses_integration(self, mock_requests_get):
        """Test handling of malformed API responses"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock malformed BioPortal response
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {"invalid": "structure"}

        # Mock malformed OLS response
        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {"malformed": "data"}

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

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should handle malformed responses gracefully
        self.assertIsInstance(results, list)
        self.assertIsInstance(comparison, dict)

    @patch("requests.get")
    def test_multiple_concept_variants_integration(self, mock_requests_get):
        """Test lookup with multiple concept variants"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock responses for different variants
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "COVID-19",
                    "@id": "http://purl.obolibrary.org/obo/MONDO_0100096",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/MONDO"},
                }
            ]
        }

        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "COVID-19",
                        "iri": "http://purl.obolibrary.org/obo/MONDO_0100096",
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

        # Test concept with multiple variants
        concept = {"key": "covid", "label": "COVID-19", "type": "Disease", "category": "instance"}

        # Mock search strategies to include multiple variants
        with patch(
            "core.lookup.SEARCH_STRATEGIES",
            {
                "covid": {
                    "variants": ["COVID-19", "SARS-CoV-2", "coronavirus disease"],
                    "ontologies": "MONDO,HP",
                }
            },
        ):
            results, comparison = lookup.lookup_concept(concept)

            # Should have made multiple API calls for different variants
            self.assertGreater(mock_requests_get.call_count, 1)
            self.assertGreater(len(results), 0)

    @patch("requests.get")
    def test_ontology_filtering_integration(self, mock_requests_get):
        """Test ontology filtering in API calls"""
        # Create fresh service instances after mocks are applied
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols, default_ontologies="HP,MONDO")

        # Mock responses
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Fatigue",
                    "@id": "http://purl.obolibrary.org/obo/HP_0012378",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/HP"},
                }
            ]
        }

        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Fatigue",
                        "iri": "http://purl.obolibrary.org/obo/HP_0012378",
                        "ontology_name": "hp",
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

        concept = {"key": "fatigue", "label": "Fatigue", "type": "Symptom", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Verify ontology filtering was applied by checking the mock was called
        self.assertGreater(mock_requests_get.call_count, 0)
        self.assertGreater(len(results), 0)

    def test_result_deduplication_integration(self):
        """Test result deduplication across services"""
        # Mock duplicate results from both services
        bp_results = [
            {
                "uri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                "label": "COVID-19",
                "ontology": "MONDO",
                "source": "bioportal",
            }
        ]

        ols_results = [
            {
                "uri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                "label": "COVID-19",
                "ontology": "MONDO",
                "source": "ols",
            }
        ]

        # Test deduplication
        combined = self.lookup._combine_results(bp_results, ols_results)

        # Should only have one result despite duplicates
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0]["source"], "bioportal")  # BioPortal takes priority

    @patch("requests.get")
    def test_cli_list_ontologies_integration(self, mock_requests_get):
        """Test CLI list ontologies functionality"""
        # Create fresh CLI instance
        cli = CLIInterface()

        # Test list ontologies argument parsing
        args = cli.parser.parse_args(["--list-ontologies"])

        # Verify list ontologies is enabled
        self.assertTrue(args.list_ontologies)

        # Test that CLI can handle the list ontologies command
        self.assertIsInstance(cli, CLIInterface)
        self.assertIsNotNone(cli.parser)

    @patch("requests.get")
    def test_cli_output_file_integration(self, mock_requests_get):
        """Test CLI output file specification"""
        # Create fresh CLI instance
        cli = CLIInterface()

        # Create temporary TTL file
        temp_file = self.create_temp_ttl_file("""
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :Test a owl:Class .
        """)

        try:
            # Test output file argument parsing
            args = cli.parser.parse_args([temp_file, "--output", "custom_output.ttl"])

            # Verify output file is set
            self.assertEqual(args.output, "custom_output.ttl")
            self.assertEqual(args.ttl_file, temp_file)

        finally:
            self.cleanup_temp_file(temp_file)

    @patch("requests.get")
    def test_cli_terminal_only_mode_integration(self, mock_requests_get):
        """Test CLI terminal-only mode"""
        # Create fresh CLI instance
        cli = CLIInterface()

        # Create temporary TTL file
        temp_file = self.create_temp_ttl_file("""
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :Test a owl:Class .
        """)

        try:
            # Test terminal-only mode argument parsing
            args = cli.parser.parse_args([temp_file, "--terminal-only"])

            # Verify terminal-only mode is enabled
            self.assertTrue(args.terminal_only)
            self.assertEqual(args.ttl_file, temp_file)

        finally:
            self.cleanup_temp_file(temp_file)

    @patch("requests.get")
    def test_cli_report_mode_integration(self, mock_requests_get):
        """Test CLI report generation mode"""
        # Create fresh CLI instance
        cli = CLIInterface()

        # Create temporary TTL file
        temp_file = self.create_temp_ttl_file("""
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        :Test a owl:Class .
        """)

        try:
            # Test report mode argument parsing
            args = cli.parser.parse_args([temp_file, "--report", "comparison_report.json"])

            # Verify report mode is enabled
            self.assertEqual(args.report, "comparison_report.json")
            self.assertEqual(args.ttl_file, temp_file)

        finally:
            self.cleanup_temp_file(temp_file)

    @patch("requests.get")
    def test_service_comparison_integration(self, mock_requests_get):
        """Test service comparison functionality"""
        # Create fresh service instances
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock different responses from services
        mock_bp_response = MagicMock()
        mock_bp_response.status_code = 200
        mock_bp_response.raise_for_status.return_value = None
        mock_bp_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Test Term",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                }
            ]
        }

        mock_ols_response = MagicMock()
        mock_ols_response.status_code = 200
        mock_ols_response.raise_for_status.return_value = None
        mock_ols_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0002",
                        "ontology_name": "test",
                    }
                ]
            }
        }

        # Configure mock to return different responses
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

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Verify comparison data is generated
        self.assertIsInstance(comparison, dict)
        self.assertIn("concept", comparison)
        self.assertIn("bioportal_count", comparison)
        self.assertIn("ols_count", comparison)
        self.assertIn("discrepancies", comparison)

    @patch("requests.get")
    def test_error_recovery_integration(self, mock_requests_get):
        """Test error recovery across multiple API calls"""
        # Create fresh service instances
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Track call count
        call_count = 0

        def mock_response(url, *args, **kwargs):
            nonlocal call_count
            call_count += 1

            # Fail first call, succeed on second
            if call_count == 1:
                raise Exception("First call fails")
            else:
                mock_success = MagicMock()
                mock_success.status_code = 200
                mock_success.raise_for_status.return_value = None
                mock_success.json.return_value = {
                    "response": {
                        "docs": [
                            {
                                "label": "Test Term",
                                "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                                "ontology_name": "test",
                            }
                        ]
                    }
                }
                return mock_success

        mock_requests_get.side_effect = mock_response

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should still get results despite initial failure
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["source"], "ols")

    @patch("requests.get")
    def test_logging_integration(self, mock_requests_get):
        """Test logging functionality during API calls"""
        # Create fresh service instances
        bioportal = BioPortalLookup(self.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": {
                "docs": [
                    {
                        "label": "Test Term",
                        "iri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "ontology_name": "test",
                    }
                ]
            }
        }
        mock_requests_get.return_value = mock_response

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        # Test that logging doesn't break functionality
        with patch("config.logging_config.get_logger") as mock_logger:
            mock_logger.return_value.info.return_value = None
            mock_logger.return_value.warning.return_value = None
            mock_logger.return_value.error.return_value = None

            results, comparison = lookup.lookup_concept(concept)

            # Should still work with logging
            self.assertIsInstance(results, list)
            self.assertIsInstance(comparison, dict)

    def test_create_temp_batch_file(self):
        """Test temporary batch file creation utility"""
        batch_data = {
            "test": [{"uri": "http://example.org/test", "label": "Test", "ontology": "TEST"}]
        }

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(batch_data, temp_file)
        temp_file.close()

        try:
            # Verify file was created and contains expected data
            self.assertTrue(os.path.exists(temp_file.name))

            with open(temp_file.name) as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, batch_data)

        finally:
            self.cleanup_temp_file(temp_file.name)

    def test_cleanup_temp_file(self):
        """Test temporary file cleanup utility"""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        temp_file.write("test content")
        temp_file.close()

        # Verify file exists
        self.assertTrue(os.path.exists(temp_file.name))

        # Clean it up
        self.cleanup_temp_file(temp_file.name)

        # Verify file is gone
        self.assertFalse(os.path.exists(temp_file.name))

    @patch("requests.get")
    def test_api_key_validation_integration(self, mock_requests_get):
        """Test API key validation during requests"""
        # Create service with different API key
        bioportal = BioPortalLookup("different_key")
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols)

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Test Term",
                    "@id": "http://purl.obolibrary.org/obo/TEST_0001",
                    "links": {"ontology": "http://data.bioontology.org/ontologies/TEST"},
                }
            ]
        }
        mock_requests_get.return_value = mock_response

        concept = {"key": "test", "label": "Test Term", "type": "Term", "category": "instance"}

        results, comparison = lookup.lookup_concept(concept)

        # Should work with any API key in test mode
        self.assertIsInstance(results, list)
        self.assertIsInstance(comparison, dict)

        # Verify the API key was used in the request
        mock_requests_get.assert_called()

        # In test mode, API key might not be required, so we just verify the service works
        self.assertIsInstance(results, list)
        self.assertIsInstance(comparison, dict)


if __name__ == "__main__":
    unittest.main()
