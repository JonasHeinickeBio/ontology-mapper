"""
Unit tests for utils/helpers.py module.
"""

import unittest
from unittest.mock import patch

from utils.helpers import clean_description, deduplicate_synonyms, determine_alignment_type


class TestUtilsHelpers(unittest.TestCase):
    """Unit tests for utility helper functions"""

    def test_clean_description_basic(self):
        """Test basic description cleaning"""
        description = "A disease caused by virus"
        result = clean_description(description)
        self.assertEqual(result, "Disease caused by virus")

    def test_clean_description_empty(self):
        """Test empty description handling"""
        self.assertEqual(clean_description(""), "")

    def test_clean_description_whitespace_only(self):
        """Test whitespace-only input"""
        self.assertEqual(clean_description("   "), "")
        self.assertEqual(clean_description("\t\n  "), "")

    def test_clean_description_whitespace(self):
        """Test whitespace normalization"""
        description = "  Multiple   spaces    in   text  "
        result = clean_description(description)
        self.assertEqual(result, "Multiple spaces in text")

    def test_clean_description_prefixes(self):
        """Test prefix removal"""
        test_cases = [
            ("A medical condition", "Medical condition"),
            ("An important disease", "Important disease"),
            ("The primary symptom", "Primary symptom"),
            ("This is a test", "Test"),
            ("Definition: A disease", "A disease"),  # Only removes "Definition: "
            ("Description: Symptom", "Symptom"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = clean_description(input_text)
                self.assertEqual(result, expected)

    def test_clean_description_capitalization(self):
        """Test capitalization handling"""
        description = "a disease without capital"
        result = clean_description(description)
        self.assertEqual(result, "A disease without capital")  # First letter capitalized

    def test_clean_description_length_limit(self):
        """Test length limiting"""
        long_description = "A " + "very " * 50 + "long description"
        result = clean_description(long_description)
        self.assertTrue(len(result) <= 200)
        self.assertTrue(result.endswith("..."))

    def test_deduplicate_synonyms_basic(self):
        """Test basic synonym deduplication"""
        synonyms = ["COVID-19", "covid-19", "SARS-CoV-2", "COVID-19"]
        existing_labels = {"coronavirus"}

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should remove duplicates and normalize
        self.assertIn("COVID-19", result)
        self.assertIn("SARS-CoV-2", result)
        self.assertEqual(len(result), 2)

    def test_deduplicate_synonyms_empty(self):
        """Test empty synonym list"""
        result = deduplicate_synonyms([], set())
        self.assertEqual(result, [])

    def test_deduplicate_synonyms_whitespace_handling(self):
        """Test handling of synonyms with whitespace"""
        synonyms = ["  COVID-19  ", "", "   ", "\t\n", "SARS-CoV-2"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should strip whitespace and exclude empty entries
        self.assertIn("COVID-19", result)
        self.assertIn("SARS-CoV-2", result)
        self.assertEqual(len(result), 2)

    def test_deduplicate_synonyms_case_variations(self):
        """Test handling of case variations"""
        synonyms = ["Covid-19", "COVID-19", "covid-19", "CoViD-19"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should keep only one variation
        self.assertEqual(len(result), 1)

    def test_deduplicate_synonyms_case_variations_complex(self):
        """Test complex case variation handling"""
        # This should trigger the case variation check on line 67
        synonyms = ["Term1", "TERM1", "different_term", "DIFFERENT_TERM"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should keep only unique normalized forms
        self.assertEqual(len(result), 2)  # One for term1, one for different_term

    def test_deduplicate_synonyms_potential_unreachable_case(self):
        """Test potential edge case that might trigger line 67"""
        # Try to create a scenario where the case variation check might be relevant
        # This is testing if the logic works as intended, even if line 67 is unreachable
        synonyms = ["Test", "test", "TEST", "TeSt"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should only keep one variation
        self.assertEqual(len(result), 1)

    def test_deduplicate_synonyms_sorting_behavior(self):
        """Test sorting by length then alphabetically"""
        synonyms = ["very_long_synonym", "abc", "medium_length", "xyz"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should be sorted by length first, then alphabetically
        lengths = [len(s) for s in result]
        self.assertEqual(lengths, sorted(lengths))

        # Within same length, should be alphabetically sorted
        same_length_groups: dict[int, list[str]] = {}
        for s in result:
            length = len(s)
            if length not in same_length_groups:
                same_length_groups[length] = []
            same_length_groups[length].append(s)

        for group in same_length_groups.values():
            self.assertEqual(group, sorted(group, key=str.lower))

    def test_deduplicate_synonyms_short_terms(self):
        """Test filtering of short terms"""
        synonyms = ["COVID-19", "A", "AB", "ABC"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should only keep terms >= 3 characters
        self.assertIn("COVID-19", result)
        self.assertIn("ABC", result)
        self.assertNotIn("A", result)
        self.assertNotIn("AB", result)

    def test_deduplicate_synonyms_existing_labels(self):
        """Test filtering against existing labels"""
        synonyms = ["COVID-19", "SARS-CoV-2", "coronavirus"]
        existing_labels = {"coronavirus", "covid-19"}

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should exclude existing labels
        self.assertIn("SARS-CoV-2", result)
        self.assertNotIn("coronavirus", result)

    def test_determine_alignment_type_exact(self):
        """Test exact alignment detection"""
        alignment = {"label": "covid 19", "synonyms": ["SARS-CoV-2"]}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "exact")

    def test_determine_alignment_type_synonym_match(self):
        """Test exact match in synonyms"""
        alignment = {"label": "Disease", "synonyms": ["covid 19", "coronavirus"]}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "exact")

    def test_determine_alignment_type_close(self):
        """Test close match detection"""
        alignment = {"label": "covid 19 disease", "synonyms": []}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "close")

    def test_determine_alignment_type_broader(self):
        """Test broader match detection"""
        alignment = {"label": "Infectious Disease", "synonyms": []}
        concept_key = "symptom"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "broader")

    def test_determine_alignment_type_narrower(self):
        """Test narrower match detection"""
        alignment = {"label": "Fever symptom", "synonyms": []}
        concept_key = "disease"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "narrower")

    def test_determine_alignment_type_default(self):
        """Test default related match"""
        alignment = {"label": "Unrelated Term", "synonyms": []}
        concept_key = "covid_19"

        result = determine_alignment_type(alignment, concept_key)
        self.assertEqual(result, "related")

    def test_integration_all_functions(self):
        """Test integration of all helper functions"""
        # Test clean_description
        description = "A disease characterized by high body temperature"
        cleaned = clean_description(description)
        self.assertEqual(cleaned, "Disease characterized by high body temperature")

        # Test deduplicate_synonyms
        synonyms = ["fever", "Fever", "pyrexia", "high temperature"]
        existing = {"temperature"}
        deduped = deduplicate_synonyms(synonyms, existing)
        self.assertIn("fever", deduped)
        self.assertIn("pyrexia", deduped)

        # Test determine_alignment_type
        alignment = {"label": "fever", "synonyms": ["pyrexia"]}
        alignment_type = determine_alignment_type(alignment, "fever")
        self.assertEqual(alignment_type, "exact")

    def test_clean_description_edge_cases(self):
        """Test clean_description edge cases"""
        # Test single character after prefix removal
        self.assertEqual(clean_description("A x"), "X")

        # Test exact prefix match - results in just the capitalized remaining text
        self.assertEqual(
            clean_description("A "), "A"
        )  # Just "A" after stripping prefix leaves empty, so returns "A"
        self.assertEqual(clean_description("The "), "The")  # Same behavior

        # Test prefix case sensitivity
        self.assertEqual(clean_description("a disease"), "A disease")  # lowercase 'a' not removed

    def test_clean_description_multiple_prefixes(self):
        """Test that only first matching prefix is removed"""
        description = "A definition: This is a disease"
        result = clean_description(description)
        self.assertEqual(result, "Definition: This is a disease")

    def test_deduplicate_synonyms_edge_cases(self):
        """Test deduplicate_synonyms edge cases"""
        # Test with exact length boundary (3 characters)
        synonyms = ["ab", "abc", "abcd"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should include "abc" and "abcd" but not "ab"
        self.assertNotIn("ab", result)
        self.assertIn("abc", result)
        self.assertIn("abcd", result)

    def test_determine_alignment_type_missing_data(self):
        """Test determine_alignment_type with missing or malformed data"""
        # Missing label field - empty string matches condition "'' in concept_label" so returns "close"
        alignment = {"synonyms": ["test1", "test2"]}
        result = determine_alignment_type(alignment, "concept")
        self.assertEqual(result, "close")

        # Empty label - same behavior
        alignment = {"label": "", "synonyms": []}
        result = determine_alignment_type(alignment, "concept")
        self.assertEqual(result, "close")

        # Missing synonyms field
        alignment = {"label": "test label"}
        result = determine_alignment_type(alignment, "test_label")
        self.assertEqual(result, "exact")

    def test_determine_alignment_type_complex_hierarchical(self):
        """Test complex hierarchical relationship detection"""
        # Multiple hierarchy indicators
        alignment = {"label": "Heart Disease Syndrome", "synonyms": []}
        result = determine_alignment_type(alignment, "symptom")
        self.assertEqual(result, "broader")

        # Case insensitive hierarchy detection
        alignment = {"label": "FEVER MANIFESTATION", "synonyms": []}
        result = determine_alignment_type(alignment, "disease")
        self.assertEqual(result, "narrower")

    def test_clean_description_unicode_handling(self):
        """Test clean_description with unicode characters"""
        description = "A café-related condition"
        result = clean_description(description)
        self.assertEqual(result, "Café-related condition")

    def test_deduplicate_synonyms_unicode_handling(self):
        """Test deduplicate_synonyms with unicode characters"""
        synonyms = ["café", "CAFÉ", "naïve", "naive"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # Should handle unicode properly
        self.assertGreaterEqual(len(result), 2)  # At least café and naïve/naive variants

    def test_module_imports(self):
        """Test that all expected functions can be imported"""
        from utils.helpers import clean_description, deduplicate_synonyms, determine_alignment_type

        # Verify functions are callable
        self.assertTrue(callable(clean_description))
        self.assertTrue(callable(deduplicate_synonyms))
        self.assertTrue(callable(determine_alignment_type))

    def test_function_docstrings(self):
        """Test that all functions have proper docstrings"""
        functions = [clean_description, deduplicate_synonyms, determine_alignment_type]

        for func in functions:
            with self.subTest(function=func.__name__):
                self.assertIsNotNone(func.__doc__)
                if func.__doc__:
                    self.assertGreater(len(func.__doc__.strip()), 10)

    def test_clean_description_newlines_tabs(self):
        """Test clean_description handles newlines and tabs"""
        description = "A\tdisease\nwith\tspecial\ncharacters"
        result = clean_description(description)
        self.assertEqual(result, "Disease with special characters")

    def test_deduplicate_synonyms_special_characters(self):
        """Test deduplicate_synonyms with special characters"""
        synonyms = ["COVID-19", "covid_19", "covid.19", "covid 19"]
        existing_labels: set[str] = set()

        result = deduplicate_synonyms(synonyms, existing_labels)

        # All should be kept as they normalize differently
        self.assertGreaterEqual(len(result), 3)

    def test_determine_alignment_type_underscore_normalization(self):
        """Test concept key underscore normalization"""
        alignment = {"label": "heart disease", "synonyms": []}

        # Underscore should be converted to space for comparison
        result = determine_alignment_type(alignment, "heart_disease")
        self.assertEqual(result, "exact")


if __name__ == "__main__":
    unittest.main()
