"""
Unit tests for core/lookup.py module.
"""

import unittest
from unittest.mock import Mock, patch

from core.lookup import ConceptLookup
from services import BioPortalLookup, OLSLookup, ResultComparator


class TestConceptLookup(unittest.TestCase):
    """Unit tests for ConceptLookup class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_bioportal = Mock(spec=BioPortalLookup)
        self.mock_ols = Mock(spec=OLSLookup)
        self.lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)

    def test_concept_lookup_init(self):
        """Test ConceptLookup initialization"""
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols)
        self.assertEqual(lookup.bioportal, self.mock_bioportal)
        self.assertEqual(lookup.ols, self.mock_ols)
        self.assertIsNone(lookup.default_ontologies)

    def test_concept_lookup_init_with_default_ontologies(self):
        """Test ConceptLookup initialization with default ontologies"""
        default_ontologies = "MONDO,HP"
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols, default_ontologies)
        self.assertEqual(lookup.default_ontologies, default_ontologies)

    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_basic(self, mock_compare):
        """Test basic concept lookup"""
        # Mock search strategies on the instance
        self.lookup.search_strategies = {"test_key": {"variants": ["test"], "ontologies": "NCIT"}}
        concept = {"key": "test_key", "label": "Test Label"}

        # Mock search results
        bp_results = [{"uri": "http://bp.example.org/1", "label": "BP Result"}]
        ols_results = [{"uri": "http://ols.example.org/1", "label": "OLS Result"}]

        self.mock_bioportal.search.return_value = bp_results
        self.mock_ols.search.return_value = ols_results

        # Mock comparison
        comparison = {"concept": "Test Label", "common_terms": []}
        mock_compare.return_value = comparison

        # Call method
        results, returned_comparison = self.lookup.lookup_concept(concept)

        # Verify searches were called with correct parameters - test strategy uses only 'test' variant
        self.mock_bioportal.search.assert_called_once_with("test", "NCIT", max_results=5)
        self.mock_ols.search.assert_called_once_with(
            "test", "NCIT", max_results=5
        )  # Verify comparison was called
        mock_compare.assert_called_once_with(bp_results, ols_results, "Test Label")

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(returned_comparison, comparison)

    @patch("core.lookup.SEARCH_STRATEGIES", {})
    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_no_strategy(self, mock_compare):
        """Test concept lookup with no predefined strategy"""
        concept = {"key": "unknown_key", "label": "Unknown Label"}

        # Mock search results
        bp_results = []
        ols_results = []

        self.mock_bioportal.search.return_value = bp_results
        self.mock_ols.search.return_value = ols_results

        # Mock comparison
        comparison = {"concept": "Unknown Label", "common_terms": []}
        mock_compare.return_value = comparison

        # Call method
        results, returned_comparison = self.lookup.lookup_concept(concept)

        # Should use default strategy with label and lowercased label
        # Verify both services were called twice (for both variants)
        self.assertEqual(self.mock_bioportal.search.call_count, 2)
        self.assertEqual(self.mock_ols.search.call_count, 2)

    @patch(
        "core.lookup.SEARCH_STRATEGIES",
        {"test_key": {"variants": ["variant1", "variant2"], "ontologies": "HP"}},
    )
    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_multiple_variants(self, mock_compare):
        """Test concept lookup with multiple variants"""
        concept = {"key": "test_key", "label": "Test Label"}

        # Mock search results for different variants
        bp_results_1 = [{"uri": "http://bp.example.org/1", "label": "BP Result 1"}]
        bp_results_2 = [{"uri": "http://bp.example.org/2", "label": "BP Result 2"}]
        ols_results_1 = [{"uri": "http://ols.example.org/1", "label": "OLS Result 1"}]
        ols_results_2 = [{"uri": "http://ols.example.org/2", "label": "OLS Result 2"}]

        # Configure mock to return different results for different calls
        self.mock_bioportal.search.side_effect = [bp_results_1, bp_results_2]
        self.mock_ols.search.side_effect = [ols_results_1, ols_results_2]

        # Mock comparison
        comparison = {"concept": "Test Label", "common_terms": []}
        mock_compare.return_value = comparison

        # Call method
        results, returned_comparison = self.lookup.lookup_concept(concept)

        # Verify both variants were searched
        self.assertEqual(self.mock_bioportal.search.call_count, 2)
        self.assertEqual(self.mock_ols.search.call_count, 2)

        # Verify all results are combined
        self.assertEqual(len(results), 4)

    def test_lookup_concept_with_default_ontologies(self):
        """Test concept lookup uses default ontologies when specified"""
        lookup = ConceptLookup(self.mock_bioportal, self.mock_ols, "DEFAULT,ONTOLOGIES")
        concept = {"key": "test_key", "label": "Test Label"}

        # Mock search results
        self.mock_bioportal.search.return_value = []
        self.mock_ols.search.return_value = []

        # Call method - unknown key uses default strategy with [label, label.lower()]
        with patch.object(ResultComparator, "compare_results", return_value={}):
            lookup.lookup_concept(concept)

        # Verify default ontologies were used - check last call (lowercase variant)
        self.mock_bioportal.search.assert_called_with(
            "test label", "DEFAULT,ONTOLOGIES", max_results=5
        )
        self.mock_ols.search.assert_called_with("test label", "DEFAULT,ONTOLOGIES", max_results=5)

    def test_combine_results_no_duplicates(self):
        """Test _combine_results with no duplicate URIs"""
        bp_results = [
            {"uri": "http://bp.example.org/1", "label": "BP Result 1"},
            {"uri": "http://bp.example.org/2", "label": "BP Result 2"},
        ]
        ols_results = [
            {"uri": "http://ols.example.org/1", "label": "OLS Result 1"},
            {"uri": "http://ols.example.org/2", "label": "OLS Result 2"},
        ]

        combined = self.lookup._combine_results(bp_results, ols_results)

        # Should have all 4 results
        self.assertEqual(len(combined), 4)

        # BP results should come first
        self.assertEqual(combined[0], bp_results[0])
        self.assertEqual(combined[1], bp_results[1])

        # OLS results should have ols_only flag
        self.assertTrue(combined[2].get("ols_only", False))
        self.assertTrue(combined[3].get("ols_only", False))

    def test_combine_results_with_duplicates(self):
        """Test _combine_results with duplicate URIs"""
        bp_results = [
            {"uri": "http://example.org/1", "label": "BP Result 1", "source": "bioportal"},
            {"uri": "http://example.org/2", "label": "BP Result 2", "source": "bioportal"},
        ]
        ols_results = [
            {
                "uri": "http://example.org/1",
                "label": "OLS Result 1",
                "source": "ols",
            },  # Duplicate URI
            {"uri": "http://example.org/3", "label": "OLS Result 3", "source": "ols"},
        ]

        combined = self.lookup._combine_results(bp_results, ols_results)

        # Should have 3 results (one duplicate removed)
        self.assertEqual(len(combined), 3)

        # First two should be from BioPortal
        self.assertEqual(combined[0]["source"], "bioportal")
        self.assertEqual(combined[1]["source"], "bioportal")

        # Third should be from OLS (non-duplicate)
        self.assertEqual(combined[2]["source"], "ols")
        self.assertTrue(combined[2].get("ols_only", False))

    def test_combine_results_empty_inputs(self):
        """Test _combine_results with empty input lists"""
        combined = self.lookup._combine_results([], [])
        self.assertEqual(combined, [])

    def test_combine_results_bp_only(self):
        """Test _combine_results with only BioPortal results"""
        bp_results = [{"uri": "http://bp.example.org/1", "label": "BP Result 1"}]
        combined = self.lookup._combine_results(bp_results, [])

        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0], bp_results[0])
        self.assertNotIn("ols_only", combined[0])

    def test_combine_results_ols_only(self):
        """Test _combine_results with only OLS results"""
        ols_results = [{"uri": "http://ols.example.org/1", "label": "OLS Result 1"}]
        combined = self.lookup._combine_results([], ols_results)

        self.assertEqual(len(combined), 1)
        self.assertTrue(combined[0].get("ols_only", False))

    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_max_results_parameter(self, mock_compare):
        """Test that max_results parameter is passed correctly"""
        # Mock search strategies on the instance
        self.lookup.search_strategies = {"test_key": {"variants": ["test"], "ontologies": "NCIT"}}
        concept = {"key": "test_key", "label": "Test Label"}
        max_results = 10

        self.mock_bioportal.search.return_value = []
        self.mock_ols.search.return_value = []
        mock_compare.return_value = {}

        # Call method with custom max_results
        self.lookup.lookup_concept(concept, max_results=max_results)

        # Verify max_results was passed to both services
        self.mock_bioportal.search.assert_called_with("test", "NCIT", max_results=max_results)
        self.mock_ols.search.assert_called_with("test", "NCIT", max_results=max_results)

    @patch("core.lookup.logger")
    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_logging_multiple_variants(self, mock_compare, mock_logger):
        """Test that appropriate logging occurs for multiple variants"""
        # Mock search strategies on the instance with 3 variants to match expected debug calls
        self.lookup.search_strategies = {
            "test_key": {"variants": ["variant1", "variant2", "variant3"], "ontologies": "HP"}
        }
        concept = {"key": "test_key", "label": "Test Label"}

        self.mock_bioportal.search.return_value = []
        self.mock_ols.search.return_value = []
        mock_compare.return_value = {}

        # Call method
        self.lookup.lookup_concept(concept)

        # Verify logging for multiple variants (3 in strategy)
        mock_logger.info.assert_called_with("Searching 3 variants for 'Test Label'...")

        # Verify debug logging for individual variants
        expected_debug_calls = [
            "[1/3] Searching: 'variant1'",
            "[2/3] Searching: 'variant2'",
            "[3/3] Searching: 'variant3'",
        ]

        debug_calls = [call.args[0] for call in mock_logger.debug.call_args_list]
        for expected_call in expected_debug_calls:
            self.assertIn(expected_call, debug_calls)

    @patch(
        "core.lookup.SEARCH_STRATEGIES",
        {"test_key": {"variants": ["single_variant"], "ontologies": "HP"}},
    )
    @patch("core.lookup.logger")
    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_no_logging_single_variant(self, mock_compare, mock_logger):
        """Test that no special logging occurs for single variant"""
        concept = {
            "key": "unknown_key",
            "label": "Test Label",
        }  # Unknown key will use default strategy

        self.mock_bioportal.search.return_value = []
        self.mock_ols.search.return_value = []
        mock_compare.return_value = {}

        # Call method - default strategy creates 2 variants: [label, label.lower()]
        self.lookup.lookup_concept(concept)

        # Verify logging does occur because default strategy creates 2 variants
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        variant_logs = [log for log in info_calls if "variants for" in log]
        self.assertEqual(
            len(variant_logs), 1
        )  # Should have 1 log about searching variants    def test_search_strategies_access(self):
        """Test that search_strategies are accessible"""
        self.assertIsNotNone(self.lookup.search_strategies)

    @patch(
        "core.lookup.SEARCH_STRATEGIES", {"test_key": {"variants": ["test"], "ontologies": "NCIT"}}
    )
    @patch.object(ResultComparator, "compare_results")
    def test_lookup_concept_result_limit(self, mock_compare):
        """Test that results are limited to max_results * 2"""
        concept = {"key": "test_key", "label": "Test Label"}
        max_results = 2

        # Create more results than the limit
        bp_results = [
            {"uri": f"http://bp.example.org/{i}", "label": f"BP Result {i}"} for i in range(5)
        ]
        ols_results = [
            {"uri": f"http://ols.example.org/{i}", "label": f"OLS Result {i}"} for i in range(5)
        ]

        self.mock_bioportal.search.return_value = bp_results
        self.mock_ols.search.return_value = ols_results
        mock_compare.return_value = {}

        # Call method
        results, _ = self.lookup.lookup_concept(concept, max_results=max_results)

        # Should be limited to max_results * 2
        self.assertEqual(len(results), max_results * 2)


if __name__ == "__main__":
    unittest.main()
