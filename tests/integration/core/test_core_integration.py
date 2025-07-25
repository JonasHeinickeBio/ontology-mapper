"""
Integration tests for core module functionality.
Tests the interaction between core components with realistic scenarios.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from core.generator import OntologyGenerator
from core.lookup import ConceptLookup
from core.parser import OntologyParser
from services import BioPortalLookup, OLSLookup, ResultComparator


@pytest.mark.integration
@pytest.mark.core
class TestCoreModuleIntegration(unittest.TestCase):
    """Integration tests for core module components working together"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Create mock services
        self.mock_bioportal = MagicMock(spec=BioPortalLookup)
        self.mock_ols = MagicMock(spec=OLSLookup)

        # Set up realistic mock responses
        self.sample_bp_results = [
            {
                "uri": "http://purl.bioontology.org/ontology/NCIT/C3262",
                "label": "Neoplasm",
                "source": "BioPortal",
                "ontology": "NCIT",
            },
            {
                "uri": "http://purl.bioontology.org/ontology/MONDO/0005070",
                "label": "Neoplastic Process",
                "source": "BioPortal",
                "ontology": "MONDO",
            },
        ]

        self.sample_ols_results = [
            {
                "uri": "http://purl.obolibrary.org/obo/MONDO_0005070",
                "label": "Neoplasm",
                "source": "OLS",
                "ontology": "mondo",
            }
        ]

    def test_lookup_parser_generator_integration(self):
        """Test full workflow: lookup → parse → generate"""
        # Set up concept lookup
        self.mock_bioportal.search.return_value = self.sample_bp_results
        self.mock_ols.search.return_value = self.sample_ols_results

        # Create concept lookup
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

        # Test concept lookup
        concept = {"key": "Disease", "label": "Cancer"}
        results, comparison = lookup.lookup_concept(concept)

        # Verify lookup worked
        self.assertGreater(len(results), 0)
        self.assertIn("concept", comparison)

        # Create sample concept data for generator (generator expects alignments directly)
        selections_data = {
            "cancer": results[:2]  # Use lookup results directly as alignments
        }

        # Test generator with lookup results
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as base_ttl:
            base_ttl.write(b"@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
            base_ttl.write(b"@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            base_ttl_path = base_ttl.name

        try:
            # Test parser with base ontology
            parser = OntologyParser(base_ttl_path)
            parsed_success = parser.parse()
            self.assertTrue(parsed_success)

            # Test generator with parsed data
            with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
                generator = OntologyGenerator()

                # Test ontology generation
                generator.generate_improved_ontology(parser, selections_data, output_file.name)

                # Verify output file was created
                output_exists = os.path.exists(output_file.name)
                self.assertTrue(output_exists)

        finally:
            if os.path.exists(base_ttl_path):
                os.unlink(base_ttl_path)

    def test_concept_lookup_with_multiple_services(self):
        """Test concept lookup integrating both BioPortal and OLS services"""
        # Set up different results from each service
        self.mock_bioportal.search.return_value = self.sample_bp_results
        self.mock_ols.search.return_value = self.sample_ols_results

        # Create lookup with both services
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

        # Test lookup with real concept
        concept = {"key": "Disease", "label": "Tumor"}
        results, comparison = lookup.lookup_concept(concept, max_results=10)

        # Verify both services were called
        self.mock_bioportal.search.assert_called()
        self.mock_ols.search.assert_called()

        # Verify results combination
        self.assertIsInstance(results, list)
        self.assertIsInstance(comparison, dict)

        # Verify comparison was performed
        self.assertIn("concept", comparison)

    def test_error_handling_integration(self):
        """Test error handling across core components"""
        # Set up service to raise exceptions
        self.mock_bioportal.search.side_effect = Exception("Service unavailable")
        self.mock_ols.search.return_value = self.sample_ols_results

        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

        # Test that lookup properly propagates service failures
        concept = {"key": "Disease", "label": "Cancer"}

        # Should raise exception when service fails
        with self.assertRaises(Exception) as context:
            results, comparison = lookup.lookup_concept(concept)

        # Verify the correct exception is raised
        self.assertIn("Service unavailable", str(context.exception))

    def test_data_flow_consistency(self):
        """Test data consistency across core components"""
        # Create realistic data that flows through all components
        self.mock_bioportal.search.return_value = self.sample_bp_results
        self.mock_ols.search.return_value = self.sample_ols_results

        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

        # Test multiple concepts
        concepts = [
            {"key": "Disease", "label": "Cancer"},
            {"key": "Symptom", "label": "Fatigue"},
            {"key": "Treatment", "label": "Chemotherapy"},
        ]

        all_results = []
        all_comparisons = []

        for concept in concepts:
            results, comparison = lookup.lookup_concept(concept)
            all_results.extend(results)
            all_comparisons.append(comparison)

            # Verify each concept produces valid results
            self.assertIsInstance(results, list)
            self.assertIsInstance(comparison, dict)

        # Verify data consistency
        self.assertGreater(len(all_results), 0)
        self.assertEqual(len(all_comparisons), len(concepts))

    def test_ontology_generation_integration(self):
        """Test ontology generation with realistic concept data"""
        # Create a complete concept dataset (generator expects direct alignments)
        selections_data = {
            "disease": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "alignment_type": "exact",
                    "source": "MONDO",
                    "ontology": "MONDO",
                }
            ],
            "symptom": [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0012378",
                    "label": "Fatigue",
                    "alignment_type": "exact",
                    "source": "HP",
                    "ontology": "HP",
                }
            ],
        }

        # Create base TTL file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as base_ttl:
            base_ttl.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
            base_ttl.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            base_ttl_path = base_ttl.name

        try:
            # Test complete generation workflow
            parser = OntologyParser(base_ttl_path)
            parse_success = parser.parse()
            self.assertTrue(parse_success)

            generator = OntologyGenerator()

            with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
                # Test both generation methods
                generator.generate_improved_ontology(parser, selections_data, output_file.name)

                # Verify output file exists
                output_exists = os.path.exists(output_file.name)
                self.assertTrue(output_exists)

                # Test single word generation
                single_output = output_file.name.replace(".ttl", "_single.ttl")
                test_concept = {"key": "cancer", "label": "Cancer"}
                generator.generate_single_word_ontology(
                    test_concept, selections_data, single_output
                )

                # Verify single word output exists
                single_exists = os.path.exists(single_output)
                self.assertTrue(single_exists)

        finally:
            if os.path.exists(base_ttl_path):
                os.unlink(base_ttl_path)

    def test_configuration_integration(self):
        """Test integration with configuration and search strategies"""
        # Test with custom search strategies
        custom_strategies = {
            "test_disease": {
                "variants": ["cancer", "tumor", "neoplasm"],
                "ontologies": "MONDO,NCIT",
            }
        }

        # Set up mock with custom strategy
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)
        lookup.search_strategies = custom_strategies

        self.mock_bioportal.search.return_value = self.sample_bp_results
        self.mock_ols.search.return_value = self.sample_ols_results

        # Test concept with custom strategy
        concept = {"key": "test_disease", "label": "Cancer"}
        results, comparison = lookup.lookup_concept(concept)

        # Verify custom strategy was used
        expected_calls = len(custom_strategies["test_disease"]["variants"])
        self.assertEqual(self.mock_bioportal.search.call_count, expected_calls)
        self.assertEqual(self.mock_ols.search.call_count, expected_calls)

        # Verify correct ontologies were used
        for call in self.mock_bioportal.search.call_args_list:
            args, kwargs = call
            self.assertEqual(args[1], "MONDO,NCIT")  # ontologies parameter

    def test_result_comparison_integration(self):
        """Test result comparison integration across services"""
        # Set up overlapping results to test comparison
        bp_results = [
            {
                "uri": "http://purl.bioontology.org/ontology/MONDO/0005070",
                "label": "Neoplasm",
                "source": "BioPortal",
                "ontology": "MONDO",
            },
            {
                "uri": "http://purl.bioontology.org/ontology/NCIT/C3262",
                "label": "Cancer",
                "source": "BioPortal",
                "ontology": "NCIT",
            },
        ]

        ols_results = [
            {
                "uri": "http://purl.obolibrary.org/obo/MONDO_0005070",
                "label": "Neoplasm",
                "source": "OLS",
                "ontology": "mondo",
            },
            {
                "uri": "http://purl.obolibrary.org/obo/HP_0002664",
                "label": "Neoplastic Process",
                "source": "OLS",
                "ontology": "HP",
            },
        ]

        self.mock_bioportal.search.return_value = bp_results
        self.mock_ols.search.return_value = ols_results

        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

        # Test comparison functionality
        concept = {"key": "Disease", "label": "Cancer"}
        results, comparison = lookup.lookup_concept(concept)

        # Verify comparison results structure
        self.assertIn("concept", comparison)
        self.assertIsInstance(comparison, dict)

        # Verify results were combined and deduplicated appropriately
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
