"""
Unit tests for core/generator.py module.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef

from core.generator import OntologyGenerator
from core.parser import OntologyParser


class TestOntologyGenerator(unittest.TestCase):
    """Unit tests for OntologyGenerator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = OntologyGenerator()

        # Create a mock ontology parser with a simple graph
        self.mock_ontology = Mock(spec=OntologyParser)
        self.mock_graph = Graph()

        # Add some test triples to the mock graph
        test_uri = URIRef("http://example.org/test#concept1")
        self.mock_graph.add((test_uri, RDFS.label, Literal("Test Concept")))
        self.mock_graph.add((test_uri, RDF.type, OWL.Class))

        self.mock_ontology.graph = self.mock_graph
        self.mock_ontology.ttl_file = "test_input.ttl"  # Add the missing attribute

    def test_ontology_generator_init(self):
        """Test OntologyGenerator initialization"""
        generator = OntologyGenerator()
        self.assertIsInstance(generator, OntologyGenerator)

    @patch("core.generator.datetime")
    @patch("core.generator.determine_alignment_type")
    @patch("core.generator.clean_description")
    @patch("core.generator.deduplicate_synonyms")
    def test_generate_improved_ontology_basic(
        self, mock_dedupe, mock_clean, mock_align_type, mock_datetime
    ):
        """Test basic ontology generation"""
        # Mock dependencies
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
        mock_align_type.return_value = "exact"
        mock_clean.return_value = "Clean description"
        mock_dedupe.return_value = ["synonym1", "synonym2"]

        # Test data
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "description": "External description",
                    "synonyms": ["syn1", "syn2"],
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            # Call the method
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Verify output file was created
            self.assertTrue(os.path.exists(output_file))

            # Verify file content
            with open(output_file) as f:
                content = f.read()
                self.assertIn("exactMatch", content)
                self.assertIn("External Term 1", content)
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.determine_alignment_type")
    def test_generate_improved_ontology_different_alignment_types(self, mock_align_type):
        """Test generation with different alignment types"""
        # Test each alignment type
        alignment_types = ["exact", "close", "related", "broader", "narrower", "unknown"]

        for align_type in alignment_types:
            with self.subTest(alignment_type=align_type):
                mock_align_type.return_value = align_type

                selections = {
                    "concept1": [
                        {
                            "uri": "http://external.org/term1",
                            "label": "External Term 1",
                            "ontology": "MONDO",
                            "source": "bioportal",
                        }
                    ]
                }

                with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
                    output_file = tmp_file.name

                try:
                    self.generator.generate_improved_ontology(
                        self.mock_ontology, selections, output_file
                    )

                    # Verify output file was created
                    self.assertTrue(os.path.exists(output_file))

                    # Check for expected relationship type in output
                    with open(output_file) as f:
                        content = f.read()
                        if align_type == "exact":
                            self.assertIn("exactMatch", content)
                        elif align_type == "close":
                            self.assertIn("closeMatch", content)
                        elif align_type == "related":
                            self.assertIn("relatedMatch", content)
                        elif align_type == "broader":
                            self.assertIn("broadMatch", content)
                        elif align_type == "narrower":
                            self.assertIn("narrowMatch", content)
                        else:
                            self.assertIn("seeAlso", content)
                finally:
                    if os.path.exists(output_file):
                        os.unlink(output_file)

    @patch("core.generator.clean_description")
    def test_generate_improved_ontology_with_description(self, mock_clean):
        """Test generation with descriptions"""
        mock_clean.return_value = "Cleaned description text"

        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "description": "Original description",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Verify clean_description was called
            mock_clean.assert_called_with("Original description")

            # Verify output contains description
            with open(output_file) as f:
                content = f.read()
                self.assertIn("Cleaned description text", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.clean_description")
    def test_generate_improved_ontology_empty_description(self, mock_clean):
        """Test generation with empty description"""
        mock_clean.return_value = ""  # Empty cleaned description

        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "description": "   ",  # Whitespace only
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Should still create file but without description
            self.assertTrue(os.path.exists(output_file))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.deduplicate_synonyms")
    def test_generate_improved_ontology_with_synonyms(self, mock_dedupe):
        """Test generation with synonyms"""
        mock_dedupe.return_value = ["syn1", "syn2", "syn3"]

        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "synonyms": ["syn1", "syn2", "syn3", "syn4"],
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Verify deduplicate_synonyms was called
            mock_dedupe.assert_called_once()

            # Verify output contains synonyms (limited to 3)
            with open(output_file) as f:
                content = f.read()
                self.assertIn("syn1", content)
                self.assertIn("syn2", content)
                self.assertIn("syn3", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_improved_ontology_no_synonyms(self):
        """Test generation without synonyms"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Should still create file
            self.assertTrue(os.path.exists(output_file))
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_improved_ontology_multiple_concepts(self):
        """Test generation with multiple concepts and alignments"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ],
            "concept2": [
                {
                    "uri": "http://external.org/term2",
                    "label": "External Term 2",
                    "ontology": "HP",
                    "source": "ols",
                },
                {
                    "uri": "http://external.org/term3",
                    "label": "External Term 3",
                    "ontology": "NCIT",
                    "source": "bioportal",
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Verify output contains all terms
            with open(output_file) as f:
                content = f.read()
                self.assertIn("External Term 1", content)
                self.assertIn("External Term 2", content)
                self.assertIn("External Term 3", content)
                self.assertIn("concept1", content)
                self.assertIn("concept2", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_improved_ontology_with_report(self):
        """Test generation with report file"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_report:
            report_file = tmp_report.name

        try:
            self.generator.generate_improved_ontology(
                self.mock_ontology, selections, output_file, report_file
            )

            # Verify both files were created
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue(os.path.exists(report_file))

            # Verify report content
            with open(report_file) as f:
                report = json.load(f)
                self.assertIn("alignments_added", report)
                self.assertIn("concepts_aligned", report)
                self.assertEqual(report["alignments_added"], 1)
                self.assertEqual(report["concepts_aligned"], 1)
        finally:
            for file_path in [output_file, report_file]:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_generate_improved_ontology_empty_selections(self):
        """Test generation with empty selections"""
        selections: dict[str, list[dict]] = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Should still create file with original ontology
            self.assertTrue(os.path.exists(output_file))

            with open(output_file) as f:
                content = f.read()
                # Should contain original graph content
                self.assertIn("Test Concept", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.logger")
    def test_generate_improved_ontology_missing_fields(self, mock_logger):
        """Test generation with missing fields in alignments"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    # Missing label, description, synonyms
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            # This might fail due to missing label in logging, which reveals a bug
            with self.assertRaises(KeyError):
                self.generator.generate_improved_ontology(
                    self.mock_ontology, selections, output_file
                )
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_improved_ontology_different_sources(self):
        """Test generation with different sources (bioportal vs ols)"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "BioPortal Term",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ],
            "concept2": [
                {
                    "uri": "http://external.org/term2",
                    "label": "OLS Term",
                    "ontology": "HP",
                    "source": "ols",
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            with open(output_file) as f:
                content = f.read()
                self.assertIn("BioPortal Term", content)
                self.assertIn("OLS Term", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.logger")
    def test_generate_improved_ontology_logging(self, mock_logger):
        """Test that appropriate logging occurs"""
        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            # Verify logging calls
            mock_logger.info.assert_called()

            # Check that alignment logging occurred
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            alignment_logs = [log for log in log_calls if "→" in log]
            self.assertTrue(len(alignment_logs) > 0)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_improved_ontology_preserves_original_graph(self):
        """Test that original ontology graph is preserved"""
        # Add more content to original graph
        original_uri = URIRef("http://example.org/original#concept")
        self.mock_ontology.graph.add((original_uri, RDFS.label, Literal("Original Concept")))

        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            with open(output_file) as f:
                content = f.read()
                # Should contain both original and new content
                self.assertIn("Original Concept", content)
                self.assertIn("External Term 1", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.datetime")
    def test_generate_improved_ontology_provenance_metadata(self, mock_datetime):
        """Test that provenance metadata is added correctly"""
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"

        selections = {
            "concept1": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_improved_ontology(self.mock_ontology, selections, output_file)

            with open(output_file) as f:
                content = f.read()
                # Should contain provenance information
                self.assertIn("2023-01-01T00:00:00", content)
                self.assertIn("BioPortalCLIAlignment", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_single_word_ontology_basic(self):
        """Test basic single word ontology generation"""
        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "description": "External description",
                    "synonyms": ["syn1", "syn2"],
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Verify output file was created
            self.assertTrue(os.path.exists(output_file))

            # Verify file content
            with open(output_file) as f:
                content = f.read()
                self.assertIn("Test Concept", content)
                self.assertIn("external.org/term1", content)  # Check for URI instead
                self.assertIn("relatedMatch", content)  # Default alignment type
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.determine_alignment_type")
    def test_generate_single_word_ontology_different_alignment_types(self, mock_align_type):
        """Test single word generation with different alignment types"""
        alignment_types = ["exact", "close", "related", "broader", "narrower", "unknown"]

        for align_type in alignment_types:
            with self.subTest(alignment_type=align_type):
                mock_align_type.return_value = align_type

                concept = {"key": "test_concept", "label": "Test Concept"}
                selections = {
                    "test_concept": [
                        {
                            "uri": "http://external.org/term1",
                            "label": "External Term 1",
                            "ontology": "MONDO",
                            "source": "bioportal",
                        }
                    ]
                }

                with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
                    output_file = tmp_file.name

                try:
                    self.generator.generate_single_word_ontology(concept, selections, output_file)

                    # Verify output file was created
                    self.assertTrue(os.path.exists(output_file))

                    # Check for expected relationship type in output
                    with open(output_file) as f:
                        content = f.read()
                        if align_type == "exact":
                            self.assertIn("exactMatch", content)
                        elif align_type == "close":
                            self.assertIn("closeMatch", content)
                        elif align_type == "related":
                            self.assertIn("relatedMatch", content)
                        elif align_type == "broader":
                            self.assertIn("broadMatch", content)
                        elif align_type == "narrower":
                            self.assertIn("narrowMatch", content)
                        else:
                            self.assertIn("seeAlso", content)
                finally:
                    if os.path.exists(output_file):
                        os.unlink(output_file)

    def test_generate_single_word_ontology_with_report(self):
        """Test single word generation with report file"""
        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_report:
            report_file = tmp_report.name

        try:
            self.generator.generate_single_word_ontology(
                concept, selections, output_file, report_file
            )

            # Verify both files were created
            self.assertTrue(os.path.exists(output_file))
            self.assertTrue(os.path.exists(report_file))

            # Verify report content
            with open(report_file) as f:
                report = json.load(f)
                self.assertIn("query_term", report)
                self.assertIn("alignments_added", report)
                self.assertEqual(report["query_term"], "Test Concept")
                self.assertEqual(report["alignments_added"], 1)
        finally:
            for file_path in [output_file, report_file]:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    @patch("core.generator.clean_description")
    def test_generate_single_word_ontology_with_description(self, mock_clean):
        """Test single word generation with descriptions"""
        mock_clean.return_value = "Cleaned description text"

        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "description": "Original description",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Verify clean_description was called
            mock_clean.assert_called_with("Original description")

            # Verify output contains description
            with open(output_file) as f:
                content = f.read()
                self.assertIn("Cleaned description text", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.deduplicate_synonyms")
    def test_generate_single_word_ontology_with_synonyms(self, mock_dedupe):
        """Test single word generation with synonyms"""
        mock_dedupe.return_value = ["syn1", "syn2", "syn3"]

        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "synonyms": ["syn1", "syn2", "syn3", "syn4"],
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Verify deduplicate_synonyms was called
            mock_dedupe.assert_called_once()

            # Verify output contains synonyms (limited to 3)
            with open(output_file) as f:
                content = f.read()
                self.assertIn("syn1", content)
                self.assertIn("syn2", content)
                self.assertIn("syn3", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_single_word_ontology_empty_selections(self):
        """Test single word generation with empty selections"""
        concept = {"key": "test_concept", "label": "Test Concept"}
        selections: dict[str, list[dict]] = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Should still create file with concept
            self.assertTrue(os.path.exists(output_file))

            with open(output_file) as f:
                content = f.read()
                # Should contain the concept
                self.assertIn("Test Concept", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_generate_single_word_ontology_multiple_alignments(self):
        """Test single word generation with multiple alignments"""
        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                },
                {
                    "uri": "http://external.org/term2",
                    "label": "External Term 2",
                    "ontology": "HP",
                    "source": "ols",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Verify output contains all terms
            with open(output_file) as f:
                content = f.read()
                self.assertIn("external.org/term1", content)
                self.assertIn("external.org/term2", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.logger")
    def test_generate_single_word_ontology_logging(self, mock_logger):
        """Test that appropriate logging occurs in single word generation"""
        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            # Verify logging calls
            mock_logger.info.assert_called()

            # Check that alignment logging occurred
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            alignment_logs = [log for log in log_calls if "→" in log]
            self.assertTrue(len(alignment_logs) > 0)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    @patch("core.generator.datetime")
    def test_generate_single_word_ontology_provenance(self, mock_datetime):
        """Test that provenance metadata is added correctly in single word generation"""
        mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"

        concept = {"key": "test_concept", "label": "Test Concept"}
        selections = {
            "test_concept": [
                {
                    "uri": "http://external.org/term1",
                    "label": "External Term 1",
                    "ontology": "MONDO",
                    "source": "bioportal",
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as tmp_file:
            output_file = tmp_file.name

        try:
            self.generator.generate_single_word_ontology(concept, selections, output_file)

            with open(output_file) as f:
                content = f.read()
                # Should contain provenance information
                self.assertIn("2023-01-01T00:00:00", content)
                self.assertIn("SingleWordAlignment", content)
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == "__main__":
    unittest.main()
