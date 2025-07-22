"""
Unit tests for utils.helpers module.
"""

import logging
import unittest
from unittest.mock import Mock, patch

import pytest

from utils.helpers import clean_description, deduplicate_synonyms, determine_alignment_type


@pytest.mark.unit
class TestHelpersModule(unittest.TestCase):
    """Test cases for utils.helpers module."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)

    def test_clean_description_basic(self):
        """Test basic description cleaning."""
        result = clean_description("This is a test description")
        self.assertEqual(result, "Test description")

    def test_clean_description_with_prefixes(self):
        """Test description cleaning with common prefixes."""
        test_cases = [
            ("A test description", "Test description"),
            ("An example description", "Example description"),
            ("The main description", "Main description"),
            ("This is a test", "Test"),
            ("This is an example", "Example"),
            ("This is the main", "Main"),
            ("Definition: test definition", "Test definition"),
            ("Description: test description", "Test description"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = clean_description(input_text)
                self.assertEqual(result, expected)

    def test_clean_description_empty(self):
        """Test cleaning empty description."""
        result = clean_description("")
        self.assertEqual(result, "")

    def test_clean_description_none(self):
        """Test cleaning None description."""
        result = clean_description(None)
        self.assertEqual(result, "")

    def test_clean_description_whitespace(self):
        """Test cleaning description with extra whitespace."""
        result = clean_description("  This  is  a   test   description  ")
        self.assertEqual(result, "Test description")

    def test_clean_description_capitalization(self):
        """Test that first letter is capitalized."""
        result = clean_description("test description")
        self.assertEqual(result, "Test description")

    def test_clean_description_long_text(self):
        """Test cleaning very long description."""
        long_text = "This is a very long description that exceeds the normal length limit. " * 10
        result = clean_description(long_text)

        self.assertTrue(result.endswith("..."))
        self.assertEqual(len(result), 200)

    def test_clean_description_no_prefix_match(self):
        """Test description without matching prefix."""
        result = clean_description("Some unique description")
        self.assertEqual(result, "Some unique description")

    def test_deduplicate_synonyms_basic(self):
        """Test basic synonym deduplication."""
        synonyms = ["test", "example", "sample", "test", "TEST"]
        existing_labels = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        self.assertIn("test", result)
        self.assertIn("example", result)
        self.assertIn("sample", result)
        self.assertEqual(len(result), 3)  # No duplicates

    def test_deduplicate_synonyms_empty(self):
        """Test deduplication with empty list."""
        result = deduplicate_synonyms([], set())
        self.assertEqual(result, [])

    def test_deduplicate_synonyms_none(self):
        """Test deduplication with None input."""
        result = deduplicate_synonyms(None, set())
        self.assertEqual(result, [])

    def test_deduplicate_synonyms_with_existing_labels(self):
        """Test deduplication with existing labels."""
        synonyms = ["test", "example", "sample"]
        existing_labels = {"test", "example"}

        result = deduplicate_synonyms(synonyms, existing_labels)

        self.assertEqual(result, ["sample"])

    def test_deduplicate_synonyms_short_synonyms(self):
        """Test that very short synonyms are filtered out."""
        synonyms = ["test", "ab", "example", "x", "sample"]
        existing_labels = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        self.assertNotIn("ab", result)
        self.assertNotIn("x", result)
        self.assertIn("test", result)
        self.assertIn("example", result)
        self.assertIn("sample", result)

    def test_deduplicate_synonyms_whitespace(self):
        """Test deduplication with whitespace handling."""
        synonyms = ["  test  ", "example", "  ", "sample  "]
        existing_labels = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        self.assertIn("test", result)
        self.assertIn("example", result)
        self.assertIn("sample", result)

    def test_deduplicate_synonyms_sorting(self):
        """Test that synonyms are sorted by length."""
        synonyms = ["very long synonym", "test", "example", "short"]
        existing_labels = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should be sorted by length, then alphabetically
        self.assertEqual(result[0], "test")  # Shortest
        self.assertEqual(result[-1], "very long synonym")  # Longest

    def test_determine_alignment_type_exact(self):
        """Test exact alignment type determination."""
        alignment = {"label": "covid 19", "synonyms": ["covid", "coronavirus"]}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "exact")

    def test_determine_alignment_type_exact_synonym(self):
        """Test exact alignment via synonym match."""
        alignment = {"label": "SARS-CoV-2", "synonyms": ["covid 19", "coronavirus"]}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "exact")

    def test_determine_alignment_type_close(self):
        """Test close alignment type determination."""
        alignment = {"label": "covid 19 disease", "synonyms": []}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "close")

    def test_determine_alignment_type_broader(self):
        """Test broader alignment type determination."""
        alignment = {"label": "respiratory disease", "synonyms": []}
        concept_key = "symptom"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "broader")

    def test_determine_alignment_type_narrower(self):
        """Test narrower alignment type determination."""
        alignment = {"label": "cough symptom", "synonyms": []}
        concept_key = "disease"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "narrower")

    def test_determine_alignment_type_related(self):
        """Test related alignment type determination."""
        alignment = {"label": "treatment protocol", "synonyms": []}
        concept_key = "medication"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "related")

    def test_determine_alignment_type_case_insensitive(self):
        """Test that alignment type determination is case insensitive."""
        alignment = {"label": "covid 19", "synonyms": []}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "exact")

    def test_determine_alignment_type_underscore_handling(self):
        """Test that underscores are handled in concept keys."""
        alignment = {"label": "long covid", "synonyms": []}
        concept_key = "long_covid"

        result = determine_alignment_type(alignment, concept_key)

        self.assertEqual(result, "exact")

    def test_clean_description_only_prefix(self):
        """Test cleaning description that is only a prefix."""
        result = clean_description("A ")
        self.assertEqual(result, "A")

    def test_clean_description_definition_prefix(self):
        """Test cleaning description with definition prefix."""
        result = clean_description("Definition: This is a test definition")
        self.assertEqual(result, "This is a test definition")

    def test_deduplicate_synonyms_case_variations(self):
        """Test that case variations are properly handled."""
        synonyms = ["Test", "TEST", "test", "Example", "EXAMPLE"]
        existing_labels = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should keep only one version of each
        self.assertEqual(len(result), 2)
        self.assertIn("Test", result)
        self.assertIn("Example", result)

    def test_determine_alignment_type_broader_indicators(self):
        """Test broader alignment with various indicators."""
        test_cases = [
            ("respiratory disease", "symptom"),
            ("heart disorder", "sign"),
            ("metabolic condition", "symptom"),
            ("genetic syndrome", "sign"),
        ]

        for label, concept_key in test_cases:
            with self.subTest(label=label, concept_key=concept_key):
                alignment = {"label": label, "synonyms": []}
                result = determine_alignment_type(alignment, concept_key)
                self.assertEqual(result, "broader")

    def test_determine_alignment_type_narrower_indicators(self):
        """Test narrower alignment with various indicators."""
        test_cases = [
            ("cough symptom", "disease"),
            ("fever sign", "disorder"),
            ("pain manifestation", "disease"),
        ]

        for label, concept_key in test_cases:
            with self.subTest(label=label, concept_key=concept_key):
                alignment = {"label": label, "synonyms": []}
                result = determine_alignment_type(alignment, concept_key)
                self.assertEqual(result, "narrower")

    def test_clean_description_multiple_prefixes(self):
        """Test that only the first matching prefix is removed."""
        result = clean_description("The A test description")
        self.assertEqual(result, "A test description")  # Only "The " should be removed

    def test_deduplicate_synonyms_existing_labels_case_insensitive(self):
        """Test that existing labels comparison is case insensitive."""
        synonyms = ["Test", "Example", "SAMPLE"]
        existing_labels = {"test", "example"}

        result = deduplicate_synonyms(synonyms, existing_labels)

        self.assertEqual(result, ["SAMPLE"])


if __name__ == "__main__":
    unittest.main()
