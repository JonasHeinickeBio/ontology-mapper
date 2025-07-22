"""
Unit tests for core/parser.py module.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from core.parser import OntologyParser


class TestOntologyParser(unittest.TestCase):
    """Unit tests for OntologyParser class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_ttl_content = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :COVID19 a owl:Class ;
            rdfs:label "COVID-19" ;
            rdfs:comment "A disease caused by SARS-CoV-2" .

        :Disease a rdfs:Class .
        :Symptom a rdfs:Class .

        :long_covid a :Disease ;
            rdfs:label "Long COVID" .

        :fatigue a :Symptom ;
            rdfs:label "Fatigue" .
        """

    def create_temp_ttl_file(self, content: str) -> str:
        """Create temporary TTL file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as f:
            f.write(content)
            return f.name

    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file"""
        if os.path.exists(file_path):
            os.unlink(file_path)

    def test_parser_initialization(self):
        """Test parser initialization"""
        parser = OntologyParser("test.ttl")

        self.assertEqual(parser.ttl_file, "test.ttl")
        self.assertIsNotNone(parser.graph)
        self.assertEqual(parser.classes, [])
        self.assertEqual(parser.instances, [])

    def test_parse_success(self):
        """Test successful parsing"""
        temp_file = self.create_temp_ttl_file(self.test_ttl_content)

        try:
            parser = OntologyParser(temp_file)
            result = parser.parse()

            self.assertTrue(result)
            self.assertGreater(len(parser.graph), 0)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_parse_file_not_found(self):
        """Test parsing with non-existent file"""
        parser = OntologyParser("nonexistent.ttl")
        result = parser.parse()

        self.assertFalse(result)

    def test_parse_invalid_ttl(self):
        """Test parsing with invalid TTL content"""
        invalid_content = "This is not valid TTL content"
        temp_file = self.create_temp_ttl_file(invalid_content)

        try:
            parser = OntologyParser(temp_file)
            result = parser.parse()

            self.assertFalse(result)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_parse_empty_file(self):
        """Test parsing with empty file"""
        temp_file = self.create_temp_ttl_file("")

        try:
            parser = OntologyParser(temp_file)
            result = parser.parse()

            # Empty file should parse successfully but with no triples
            self.assertTrue(result)
            self.assertEqual(len(parser.graph), 0)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_get_priority_concepts(self):
        """Test priority concepts extraction"""
        temp_file = self.create_temp_ttl_file(self.test_ttl_content)

        try:
            parser = OntologyParser(temp_file)
            parser.parse()

            concepts = parser.get_priority_concepts()

            self.assertIsInstance(concepts, list)
            # Should contain some concepts based on the test data

        finally:
            self.cleanup_temp_file(temp_file)

    def test_get_priority_concepts_empty(self):
        """Test priority concepts with empty parser"""
        parser = OntologyParser("test.ttl")

        concepts = parser.get_priority_concepts()

        self.assertIsInstance(concepts, list)
        self.assertEqual(len(concepts), 0)

    def test_classes_extraction(self):
        """Test class extraction from TTL"""
        complex_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .
        :Symptom a rdfs:Class .
        :Treatment a rdfs:Class .
        :Entity a rdfs:Class .
        """

        temp_file = self.create_temp_ttl_file(complex_ttl)

        try:
            parser = OntologyParser(temp_file)
            parser.parse()

            # Should extract classes (excluding Entity base class)
            expected_classes = ["Disease", "Symptom", "Treatment"]
            for class_name in expected_classes:
                self.assertIn(class_name, parser.classes)

            # Should not include Entity base class
            self.assertNotIn("Entity", parser.classes)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_instances_extraction(self):
        """Test instance extraction from TTL"""
        complex_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .
        :Symptom a rdfs:Class .

        :long_covid a :Disease ;
            rdfs:label "Long COVID" .

        :fatigue a :Symptom ;
            rdfs:label "Fatigue" .
        """

        temp_file = self.create_temp_ttl_file(complex_ttl)

        try:
            parser = OntologyParser(temp_file)
            parser.parse()

            # Should extract instances
            instance_names = [inst["name"] for inst in parser.instances]
            self.assertIn("long_covid", instance_names)
            self.assertIn("fatigue", instance_names)

            # Check instance structure
            for instance in parser.instances:
                self.assertIn("name", instance)
                self.assertIn("type", instance)
                self.assertIn("label", instance)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_priority_concepts_filtering(self):
        """Test priority concepts filtering logic"""
        complex_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .
        :Symptom a rdfs:Class .
        :Treatment a rdfs:Class .
        :OtherClass a rdfs:Class .

        :long_covid a :Disease ;
            rdfs:label "Long COVID" .

        :fatigue a :Symptom ;
            rdfs:label "Fatigue" .

        :other_instance a :OtherClass ;
            rdfs:label "Other Instance" .
        """

        temp_file = self.create_temp_ttl_file(complex_ttl)

        try:
            parser = OntologyParser(temp_file)
            parser.parse()

            concepts = parser.get_priority_concepts()

            # Should include priority instances
            instance_keys = [c["key"] for c in concepts if c["category"] == "instance"]
            self.assertIn("long_covid", instance_keys)
            self.assertIn("fatigue", instance_keys)

            # Should include priority classes
            class_keys = [c["key"] for c in concepts if c["category"] == "class"]
            self.assertIn("Disease", class_keys)
            self.assertIn("Symptom", class_keys)
            self.assertIn("Treatment", class_keys)

            # Should not include non-priority items
            self.assertNotIn("other_instance", instance_keys)
            self.assertNotIn("OtherClass", class_keys)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_parsing_with_logging(self):
        """Test parsing with logging functionality"""
        temp_file = self.create_temp_ttl_file(self.test_ttl_content)

        try:
            with patch("core.parser.logger") as mock_logger:
                mock_logger.info.return_value = None
                mock_logger.error.return_value = None

                parser = OntologyParser(temp_file)
                result = parser.parse()

                self.assertTrue(result)
                # Verify logging was called
                mock_logger.info.assert_called()

        finally:
            self.cleanup_temp_file(temp_file)

    def test_label_formatting(self):
        """Test label formatting in instances"""
        complex_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .

        :long_covid_syndrome a :Disease ;
            rdfs:label "Long COVID Syndrome" .
        """

        temp_file = self.create_temp_ttl_file(complex_ttl)

        try:
            parser = OntologyParser(temp_file)
            parser.parse()

            # Check that underscores are replaced with spaces in labels
            for instance in parser.instances:
                if instance["name"] == "long_covid_syndrome":
                    self.assertEqual(instance["label"], "long covid syndrome")

        finally:
            self.cleanup_temp_file(temp_file)

    def test_unicode_handling(self):
        """Test handling of unicode characters in TTL"""
        unicode_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .

        :café_syndrome a :Disease ;
            rdfs:label "Café Syndrome" .
        """

        temp_file = self.create_temp_ttl_file(unicode_ttl)

        try:
            parser = OntologyParser(temp_file)
            result = parser.parse()

            self.assertTrue(result)
            self.assertGreater(len(parser.instances), 0)

        finally:
            self.cleanup_temp_file(temp_file)

    def test_error_handling_with_partial_data(self):
        """Test error handling with partially valid data"""
        partial_ttl = """
        @prefix : <http://example.org/ontology#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        :Disease a rdfs:Class .

        # This line has an error
        :broken_instance a :NonExistentClass
        """

        temp_file = self.create_temp_ttl_file(partial_ttl)

        try:
            parser = OntologyParser(temp_file)
            # Should handle partial parsing gracefully
            result = parser.parse()

            # The result depends on rdflib's error handling
            # Just verify it doesn't crash
            self.assertIsInstance(result, bool)

        finally:
            self.cleanup_temp_file(temp_file)


if __name__ == "__main__":
    unittest.main()
