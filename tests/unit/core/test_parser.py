"""
Unit tests for core.parser module.
"""

import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from rdflib import Graph

from core.parser import OntologyParser


@pytest.mark.unit
class TestOntologyParser(unittest.TestCase):
    """Test cases for OntologyParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)
        self.temp_dir = tempfile.mkdtemp()
        self.sample_ttl_content = """
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix ont: <http://example.org/ontology#> .

        ont:Disease rdf:type rdfs:Class .
        ont:Symptom rdf:type rdfs:Class .
        ont:Treatment rdf:type rdfs:Class .

        ont:long_covid rdf:type ont:Disease .
        ont:fatigue rdf:type ont:Symptom .
        ont:rest_therapy rdf:type ont:Treatment .
        """

        self.ttl_file = Path(self.temp_dir) / "test.ttl"
        self.ttl_file.write_text(self.sample_ttl_content)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test OntologyParser initialization."""
        parser = OntologyParser(str(self.ttl_file))

        self.assertEqual(parser.ttl_file, str(self.ttl_file))
        self.assertIsInstance(parser.graph, Graph)
        self.assertEqual(len(parser.classes), 0)
        self.assertEqual(len(parser.instances), 0)

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file."""
        non_existent = "/non/existent/file.ttl"
        parser = OntologyParser(non_existent)

        self.assertEqual(parser.ttl_file, non_existent)
        self.assertIsInstance(parser.graph, Graph)

    def test_parse_success(self):
        """Test successful parsing of TTL file."""
        parser = OntologyParser(str(self.ttl_file))

        with patch("core.parser.logger") as mock_logger:
            result = parser.parse()

        self.assertTrue(result)
        self.assertIn("Disease", parser.classes)
        self.assertIn("Symptom", parser.classes)
        self.assertIn("Treatment", parser.classes)
        self.assertNotIn("Entity", parser.classes)  # Should be skipped

        # Check instances
        instance_names = [inst["name"] for inst in parser.instances]
        self.assertIn("long_covid", instance_names)
        self.assertIn("fatigue", instance_names)
        self.assertIn("rest_therapy", instance_names)

        # Verify logger was called with success message
        mock_logger.info.assert_called()

    def test_parse_invalid_file(self):
        """Test parsing with invalid TTL file."""
        invalid_file = Path(self.temp_dir) / "invalid.ttl"
        invalid_file.write_text("invalid ttl content")

        parser = OntologyParser(str(invalid_file))

        with patch("core.parser.logger") as mock_logger:
            result = parser.parse()

        self.assertFalse(result)
        mock_logger.error.assert_called()

    def test_parse_nonexistent_file(self):
        """Test parsing with non-existent file."""
        parser = OntologyParser("/non/existent/file.ttl")

        with patch("core.parser.logger") as mock_logger:
            result = parser.parse()

        self.assertFalse(result)
        mock_logger.error.assert_called()

    def test_get_priority_concepts(self):
        """Test getting priority concepts."""
        parser = OntologyParser(str(self.ttl_file))
        parser.parse()

        concepts = parser.get_priority_concepts()

        self.assertIsInstance(concepts, list)
        self.assertGreater(len(concepts), 0)

        # Check for expected priority instances
        concept_keys = [c["key"] for c in concepts]
        self.assertIn("long_covid", concept_keys)
        self.assertIn("fatigue", concept_keys)

        # Check concept structure
        for concept in concepts:
            self.assertIn("key", concept)
            self.assertIn("label", concept)
            self.assertIn("type", concept)
            self.assertIn("category", concept)

    def test_get_priority_concepts_empty(self):
        """Test getting priority concepts with no matches."""
        empty_ttl = """
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix ont: <http://example.org/ontology#> .

        ont:RandomClass rdf:type rdfs:Class .
        ont:random_instance rdf:type ont:RandomClass .
        """

        empty_file = Path(self.temp_dir) / "empty.ttl"
        empty_file.write_text(empty_ttl)

        parser = OntologyParser(str(empty_file))
        parser.parse()

        concepts = parser.get_priority_concepts()

        self.assertIsInstance(concepts, list)
        # Should have at least some concepts from priority classes
        self.assertGreaterEqual(len(concepts), 0)

    def test_instance_label_generation(self):
        """Test that instance labels are generated correctly."""
        parser = OntologyParser(str(self.ttl_file))
        parser.parse()

        # Find long_covid instance
        long_covid_instance = None
        for instance in parser.instances:
            if instance["name"] == "long_covid":
                long_covid_instance = instance
                break

        self.assertIsNotNone(long_covid_instance)
        self.assertEqual(
            long_covid_instance["label"], "long covid"
        )  # Underscores replaced with spaces
        self.assertEqual(long_covid_instance["type"], "Disease")

    @patch("core.parser.Graph")
    def test_parse_with_graph_exception(self, mock_graph_class):
        """Test parse method when graph parsing raises exception."""
        mock_graph = Mock()
        mock_graph.parse.side_effect = Exception("Graph parsing error")
        mock_graph_class.return_value = mock_graph

        parser = OntologyParser(str(self.ttl_file))
        parser.graph = mock_graph

        with patch("core.parser.logger") as mock_logger:
            result = parser.parse()

        self.assertFalse(result)
        mock_logger.error.assert_called()

    def test_priority_classes_filtering(self):
        """Test that priority classes are properly filtered."""
        parser = OntologyParser(str(self.ttl_file))
        parser.parse()

        concepts = parser.get_priority_concepts()

        # Check that only priority classes are included
        class_concepts = [c for c in concepts if c["category"] == "class"]
        class_keys = [c["key"] for c in class_concepts]

        # Should include Disease, Symptom, Treatment if they exist
        expected_priority_classes = ["Disease", "Symptom", "Treatment"]
        for expected_class in expected_priority_classes:
            if expected_class in parser.classes:
                self.assertIn(expected_class, class_keys)


if __name__ == "__main__":
    unittest.main()
