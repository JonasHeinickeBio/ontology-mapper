"""
End-to-end integration tests for the ontology mapper system.
Tests complete workflows from concept lookup to ontology generation.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

import pytest

from core.generator import OntologyGenerator
from core.lookup import ConceptLookup
from core.parser import OntologyParser
from services import BioPortalLookup, OLSLookup


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

        # Sample realistic data
        self.sample_concepts = [
            {"key": "long_covid", "label": "Long COVID"},
            {"key": "fatigue", "label": "Chronic Fatigue"},
            {"key": "immune_dysfunction", "label": "Immune System Disorder"},
        ]

        self.sample_search_results = {
            "long_covid": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0100233",
                    "label": "Post-acute COVID-19 syndrome",
                    "source": "MONDO",
                    "ontology": "mondo",
                }
            ],
            "fatigue": [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0012378",
                    "label": "Fatigue",
                    "source": "HP",
                    "ontology": "hp",
                }
            ],
            "immune_dysfunction": [
                {
                    "uri": "http://purl.obolibrary.org/obo/GO_0002376",
                    "label": "Immune system process",
                    "source": "GO",
                    "ontology": "go",
                }
            ],
        }

    def test_complete_workflow_with_mocked_services(self):
        """Test complete workflow from concept lookup to ontology generation"""
        # Create mock services
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        # Set up mock responses
        def mock_bp_search(term, ontologies, max_results=5):
            for concept_key, results in self.sample_search_results.items():
                if concept_key.replace("_", " ").lower() in term.lower():
                    return results
            return []

        def mock_ols_search(term, ontologies, max_results=5):
            # Return slightly different results to test combination
            for concept_key, results in self.sample_search_results.items():
                if concept_key.replace("_", " ").lower() in term.lower():
                    modified_results = results.copy()
                    for result in modified_results:
                        result["source"] = "OLS"
                    return modified_results
            return []

        mock_bioportal.search.side_effect = mock_bp_search
        mock_ols.search.side_effect = mock_ols_search

        # Test concept lookup phase
        lookup = ConceptLookup(mock_bioportal, mock_ols)

        all_results = {}
        all_comparisons = {}

        for concept in self.sample_concepts:
            results, comparison = lookup.lookup_concept(concept, max_results=10)
            all_results[concept["key"]] = results
            all_comparisons[concept["key"]] = comparison

            # Verify results were found
            self.assertGreater(len(results), 0, f"No results found for {concept['label']}")

        # Create selections from lookup results
        selections = {}
        for concept_key, results in all_results.items():
            if results:
                selections[concept_key] = results[:2]  # Select top 2 results directly

        # Test ontology generation phase
        base_ttl_path = None
        output_path = None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as base_ttl:
            base_ttl.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
            base_ttl.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            base_ttl_path = base_ttl.name

        try:
            # Parse base ontology
            parser = OntologyParser(base_ttl_path)
            parse_success = parser.parse()
            self.assertTrue(parse_success)

            # Generate improved ontology
            generator = OntologyGenerator()

            with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
                output_path = output_file.name

            # Generate ontology
            generator.generate_improved_ontology(parser, selections, output_path)

            # Verify output was created
            self.assertTrue(os.path.exists(output_path))

            # Verify output has content (not empty)
            with open(output_path) as f:
                content = f.read()
                self.assertGreater(len(content), 0)
                # Should contain some RDF/TTL content
                self.assertIn("@prefix", content)

        finally:
            # Cleanup
            for path in [base_ttl_path, output_path]:
                if path and os.path.exists(path):
                    os.unlink(path)

    def test_error_resilience_workflow(self):
        """Test that the workflow handles errors gracefully"""
        # Create services with some failures
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        # Make BioPortal fail for some searches
        def failing_bp_search(term, ontologies, max_results=5):
            if "immune" in term.lower():
                raise Exception("Service temporarily unavailable")
            return self.sample_search_results.get("fatigue", [])

        # Make OLS work normally
        def working_ols_search(term, ontologies, max_results=5):
            for concept_key, results in self.sample_search_results.items():
                if concept_key.replace("_", " ").lower() in term.lower():
                    return results
            return []

        mock_bioportal.search.side_effect = failing_bp_search
        mock_ols.search.side_effect = working_ols_search

        # Test that lookup propagates service failures
        lookup = ConceptLookup(mock_bioportal, mock_ols)

        successful_results = {}
        expected_failures = 0
        for concept in self.sample_concepts:
            try:
                results, comparison = lookup.lookup_concept(concept)
                if results:  # Only store if we got results
                    successful_results[concept["key"]] = results
            except Exception:
                # Expected for concepts that trigger failures
                expected_failures += 1

        # Should have some failures (as designed) and some successes
        self.assertGreater(expected_failures, 0)
        self.assertGreater(len(successful_results), 0)

    def test_data_persistence_and_loading(self):
        """Test saving and loading results between workflow stages"""
        # Create mock services with realistic data
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        mock_bioportal.search.return_value = self.sample_search_results["fatigue"]
        mock_ols.search.return_value = []

        lookup = ConceptLookup(mock_bioportal, mock_ols)

        # Test concept lookup and saving
        concept = {"key": "fatigue", "label": "Chronic Fatigue"}
        results, comparison = lookup.lookup_concept(concept)

        # Save results to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as results_file:
            results_data = {
                "concept": concept,
                "results": results,
                "comparison": comparison,
                "timestamp": "2024-01-01T00:00:00Z",
            }
            json.dump(results_data, results_file)
            results_path = results_file.name

        try:
            # Load and verify saved results
            with open(results_path) as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data["concept"], concept)
            self.assertEqual(loaded_data["results"], results)
            self.assertIn("timestamp", loaded_data)

            # Use loaded results for ontology generation (generator expects direct lists)
            selections = {
                concept["key"]: loaded_data["results"][:1]  # Use loaded results directly
            }

            # Test generation with loaded data
            base_ttl_path = None
            output_path = None

            with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as base_ttl:
                base_ttl.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
                base_ttl_path = base_ttl.name

            parser = OntologyParser(base_ttl_path)
            parser.parse()

            generator = OntologyGenerator()

            with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
                output_path = output_file.name

            # Should work with loaded data
            generator.generate_improved_ontology(parser, selections, output_path)
            self.assertTrue(os.path.exists(output_path))

        finally:
            # Cleanup (basic cleanup, temp files will be handled by OS)
            if os.path.exists(results_path):
                os.unlink(results_path)

    def test_configuration_variations(self):
        """Test workflow with different configuration options"""
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        mock_bioportal.search.return_value = self.sample_search_results["fatigue"]
        mock_ols.search.return_value = []

        # Test with different default ontologies
        for default_ontologies in ["MONDO,HP", "NCIT,GO", None]:
            lookup = ConceptLookup(mock_bioportal, mock_ols, default_ontologies)

            concept = {"key": "test_concept", "label": "Test Concept"}
            results, comparison = lookup.lookup_concept(concept)

            # Verify lookup worked regardless of configuration
            self.assertIsInstance(results, list)
            self.assertIsInstance(comparison, dict)

            # Verify service was called
            self.assertTrue(mock_bioportal.search.called)

    def test_multiple_concept_workflow(self):
        """Test workflow with multiple concepts processed together"""
        mock_bioportal = MagicMock(spec=BioPortalLookup)
        mock_ols = MagicMock(spec=OLSLookup)

        # Set up different results for different concepts
        def concept_specific_search(term, ontologies, max_results=5):
            term_lower = term.lower()
            if "covid" in term_lower:
                return self.sample_search_results["long_covid"]
            elif "fatigue" in term_lower:
                return self.sample_search_results["fatigue"]
            elif "immune" in term_lower:
                return self.sample_search_results["immune_dysfunction"]
            return []

        mock_bioportal.search.side_effect = concept_specific_search
        mock_ols.search.side_effect = concept_specific_search

        lookup = ConceptLookup(mock_bioportal, mock_ols)

        # Process all concepts
        all_selections = {}
        for concept in self.sample_concepts:
            results, comparison = lookup.lookup_concept(concept)

            if results:
                all_selections[concept["key"]] = results[:1]  # Use results directly

        # Verify we got results for multiple concepts
        self.assertGreaterEqual(len(all_selections), 2)

        # Test generating ontology with multiple concepts
        base_ttl_path = None
        output_path = None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as base_ttl:
            base_ttl.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
            base_ttl_path = base_ttl.name

        try:
            parser = OntologyParser(base_ttl_path)
            parser.parse()

            generator = OntologyGenerator()

            with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as output_file:
                output_path = output_file.name

            # Generate with multiple concepts
            generator.generate_improved_ontology(parser, all_selections, output_path)

            # Verify output contains references to multiple concepts
            with open(output_path) as f:
                content = f.read()
                concept_count = sum(
                    1 for concept in self.sample_concepts if concept["key"] in content
                )
                self.assertGreater(concept_count, 0)

        finally:
            for path in [base_ttl_path, output_path]:
                if path and os.path.exists(path):
                    os.unlink(path)


if __name__ == "__main__":
    unittest.main()
