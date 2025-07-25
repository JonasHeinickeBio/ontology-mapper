"""
Integration tests for core generator functionality.
Tests the OntologyGenerator with realistic data.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

import pytest

from core.generator import OntologyGenerator
from core.parser import OntologyParser


@pytest.mark.integration
@pytest.mark.core
class TestCoreGeneratorIntegration(unittest.TestCase):
    """Integration tests for core generator functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = OntologyGenerator()

    def create_temp_ttl_file(self, content: str) -> str:
        """Create temporary TTL file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as f:
            f.write(content)
            return f.name

    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_generate_improved_ontology_integration(self):
        """Test complete ontology generation flow"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :COVID19 a owl:Class ;
            rdfs:label "COVID-19" ;
            rdfs:comment "A disease caused by SARS-CoV-2" .

        :Fatigue a owl:Class ;
            rdfs:label "Fatigue" ;
            rdfs:comment "A feeling of tiredness" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Create mock selections
            selections = {
                "covid": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/MONDO_0100096",
                        "label": "COVID-19",
                        "ontology": "MONDO",
                        "source": "bioportal",
                        "description": "A disease caused by SARS-CoV-2",
                    }
                ],
                "fatigue": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/HP_0012378",
                        "label": "Fatigue",
                        "ontology": "HP",
                        "source": "ols",
                        "description": "A feeling of tiredness",
                    }
                ],
            }

            # Generate improved ontology
            output_file = temp_file.replace(".ttl", "_improved.ttl")

            with patch("builtins.open", mock_open()) as mock_file:
                self.generator.generate_improved_ontology(parser, selections, output_file)

                # Verify generation was attempted
                self.assertTrue(mock_file.called)

        finally:
            self.cleanup_temp_file(temp_file)
            if os.path.exists(output_file):
                self.cleanup_temp_file(output_file)

    def test_generate_with_report_integration(self):
        """Test ontology generation with report generation"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :TestClass a owl:Class ;
            rdfs:label "Test Class" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Create mock selections
            selections = {
                "test": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "label": "Test Class",
                        "ontology": "TEST",
                        "source": "bioportal",
                        "description": "A test class",
                    }
                ]
            }

            # Generate with report
            output_file = temp_file.replace(".ttl", "_improved.ttl")
            report_file = temp_file.replace(".ttl", "_report.json")

            with patch("builtins.open", mock_open()) as mock_file:
                self.generator.generate_improved_ontology(
                    parser, selections, output_file, report_file
                )

                # Verify both files were attempted to be written
                self.assertTrue(mock_file.called)
                self.assertGreater(mock_file.call_count, 1)

        finally:
            self.cleanup_temp_file(temp_file)
            if os.path.exists(output_file):
                self.cleanup_temp_file(output_file)
            if os.path.exists(report_file):
                self.cleanup_temp_file(report_file)

    def test_generate_empty_selections_integration(self):
        """Test generation with empty selections"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :TestClass a owl:Class ;
            rdfs:label "Test Class" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Empty selections
            selections: dict[str, list] = {}

            # Generate with empty selections
            output_file = temp_file.replace(".ttl", "_improved.ttl")

            with patch("builtins.open", mock_open()) as mock_file:
                self.generator.generate_improved_ontology(parser, selections, output_file)

                # Should still attempt to write output
                self.assertTrue(mock_file.called)

        finally:
            self.cleanup_temp_file(temp_file)
            if os.path.exists(output_file):
                self.cleanup_temp_file(output_file)

    def test_generate_with_multiple_alignments_integration(self):
        """Test generation with multiple alignments per concept"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a owl:Class ;
            rdfs:label "Disease" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Multiple alignments for same concept
            selections = {
                "disease": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/MONDO_0000001",
                        "label": "Disease",
                        "ontology": "MONDO",
                        "source": "bioportal",
                        "description": "A disease from MONDO",
                    },
                    {
                        "uri": "http://purl.obolibrary.org/obo/DOID_4",
                        "label": "Disease",
                        "ontology": "DOID",
                        "source": "ols",
                        "description": "A disease from DOID",
                    },
                ]
            }

            # Generate with multiple alignments
            output_file = temp_file.replace(".ttl", "_improved.ttl")

            with patch("builtins.open", mock_open()) as mock_file:
                self.generator.generate_improved_ontology(parser, selections, output_file)

                # Should handle multiple alignments
                self.assertTrue(mock_file.called)

        finally:
            self.cleanup_temp_file(temp_file)
            if os.path.exists(output_file):
                self.cleanup_temp_file(output_file)

    def test_generate_with_missing_fields_integration(self):
        """Test generation with alignments missing optional fields"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :TestClass a owl:Class ;
            rdfs:label "Test Class" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Alignments with missing optional fields
            selections = {
                "test": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "label": "Test Class",
                        "ontology": "TEST",
                        "source": "bioportal",
                        # Missing description
                    }
                ]
            }

            # Generate with missing fields
            output_file = temp_file.replace(".ttl", "_improved.ttl")

            with patch("builtins.open", mock_open()) as mock_file:
                self.generator.generate_improved_ontology(parser, selections, output_file)

                # Should handle missing fields gracefully
                self.assertTrue(mock_file.called)

        finally:
            self.cleanup_temp_file(temp_file)
            if os.path.exists(output_file):
                self.cleanup_temp_file(output_file)

    def test_generator_initialization_integration(self):
        """Test generator initialization"""
        generator = OntologyGenerator()

        # Test that generator is properly initialized
        self.assertIsInstance(generator, OntologyGenerator)

        # Test that it can be created multiple times
        generator2 = OntologyGenerator()
        self.assertIsInstance(generator2, OntologyGenerator)

        # They should be separate instances
        self.assertIsNot(generator, generator2)

    def test_generate_with_file_errors_integration(self):
        """Test generation with file system errors"""
        # Create sample ontology
        ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :TestClass a owl:Class ;
            rdfs:label "Test Class" .
        """

        temp_file = self.create_temp_ttl_file(ttl_content)

        try:
            # Parse the ontology
            parser = OntologyParser(temp_file)
            self.assertTrue(parser.parse())

            # Create mock selections
            selections = {
                "test": [
                    {
                        "uri": "http://purl.obolibrary.org/obo/TEST_0001",
                        "label": "Test Class",
                        "ontology": "TEST",
                        "source": "bioportal",
                    }
                ]
            }

            # Generate with file error
            output_file = "/invalid/path/output.ttl"

            with patch("builtins.open", side_effect=OSError("File error")):
                try:
                    self.generator.generate_improved_ontology(parser, selections, output_file)
                    # Should handle file errors gracefully
                except OSError:
                    # Expected behavior - let the error propagate
                    pass

        finally:
            self.cleanup_temp_file(temp_file)


if __name__ == "__main__":
    unittest.main()
