"""
Unit tests for services/comparator.py module.
"""

import unittest

from services.comparator import ResultComparator


class TestResultComparator(unittest.TestCase):
    """Unit tests for ResultComparator class"""

    def test_compare_results_empty_lists(self):
        """Test comparison with empty result lists"""
        bp_results: list[dict] = []
        ols_results: list[dict] = []
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["concept"], "test concept")
        self.assertEqual(comparison["bioportal_count"], 0)
        self.assertEqual(comparison["ols_count"], 0)
        self.assertEqual(comparison["common_terms"], [])
        self.assertEqual(comparison["bioportal_only"], [])
        self.assertEqual(comparison["ols_only"], [])
        self.assertEqual(comparison["discrepancies"], [])

    def test_compare_results_no_common_terms(self):
        """Test comparison with no common terms"""
        bp_results = [
            {"label": "BP Term 1", "uri": "http://bp.example.org/1", "ontology": "MONDO"},
            {"label": "BP Term 2", "uri": "http://bp.example.org/2", "ontology": "HP"},
        ]
        ols_results = [
            {"label": "OLS Term 1", "uri": "http://ols.example.org/1", "ontology": "GO"},
            {"label": "OLS Term 2", "uri": "http://ols.example.org/2", "ontology": "NCIT"},
        ]
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["concept"], "test concept")
        self.assertEqual(comparison["bioportal_count"], 2)
        self.assertEqual(comparison["ols_count"], 2)
        self.assertEqual(comparison["common_terms"], [])
        self.assertEqual(len(comparison["bioportal_only"]), 2)
        self.assertEqual(len(comparison["ols_only"]), 2)

        # Check discrepancies
        expected_discrepancies = ["BioPortal has 2 unique term(s)", "OLS has 2 unique term(s)"]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_with_common_terms_same_uri(self):
        """Test comparison with common terms having same URI"""
        bp_results = [
            {"label": "Common Term", "uri": "http://example.org/same", "ontology": "MONDO"},
            {"label": "BP Only Term", "uri": "http://bp.example.org/1", "ontology": "HP"},
        ]
        ols_results = [
            {"label": "Common Term", "uri": "http://example.org/same", "ontology": "MONDO"},
            {"label": "OLS Only Term", "uri": "http://ols.example.org/1", "ontology": "GO"},
        ]
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["bioportal_count"], 2)
        self.assertEqual(comparison["ols_count"], 2)

        # Check common terms
        self.assertEqual(len(comparison["common_terms"]), 1)
        common_term = comparison["common_terms"][0]
        self.assertEqual(common_term["label"], "Common Term")
        self.assertEqual(common_term["bioportal_uri"], "http://example.org/same")
        self.assertEqual(common_term["ols_uri"], "http://example.org/same")
        self.assertEqual(common_term["bioportal_ontology"], "MONDO")
        self.assertEqual(common_term["ols_ontology"], "MONDO")
        self.assertTrue(common_term["uri_match"])

        # Check unique terms
        self.assertEqual(len(comparison["bioportal_only"]), 1)
        self.assertEqual(comparison["bioportal_only"][0]["label"], "BP Only Term")

        self.assertEqual(len(comparison["ols_only"]), 1)
        self.assertEqual(comparison["ols_only"][0]["label"], "OLS Only Term")

        # Check discrepancies
        expected_discrepancies = ["BioPortal has 1 unique term(s)", "OLS has 1 unique term(s)"]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_with_common_terms_different_uri(self):
        """Test comparison with common terms having different URIs"""
        bp_results = [
            {"label": "Common Term", "uri": "http://bp.example.org/term", "ontology": "MONDO"}
        ]
        ols_results = [
            {"label": "Common Term", "uri": "http://ols.example.org/term", "ontology": "HP"}
        ]
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Check common terms
        self.assertEqual(len(comparison["common_terms"]), 1)
        common_term = comparison["common_terms"][0]
        self.assertEqual(common_term["label"], "Common Term")
        self.assertEqual(common_term["bioportal_uri"], "http://bp.example.org/term")
        self.assertEqual(common_term["ols_uri"], "http://ols.example.org/term")
        self.assertEqual(common_term["bioportal_ontology"], "MONDO")
        self.assertEqual(common_term["ols_ontology"], "HP")
        self.assertFalse(common_term["uri_match"])

        # Should have no unique terms
        self.assertEqual(len(comparison["bioportal_only"]), 0)
        self.assertEqual(len(comparison["ols_only"]), 0)

        # Check discrepancies for URI mismatch
        expected_discrepancies = ["1 common term(s) have different URIs"]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_case_insensitive_matching(self):
        """Test that label matching is case insensitive"""
        bp_results = [
            {
                "label": "Hypertension",
                "uri": "http://bp.example.org/hypertension",
                "ontology": "MONDO",
            }
        ]
        ols_results = [
            {
                "label": "HYPERTENSION",
                "uri": "http://ols.example.org/hypertension",
                "ontology": "HP",
            }
        ]
        concept = "hypertension"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Should be treated as common term due to case-insensitive matching
        self.assertEqual(len(comparison["common_terms"]), 1)
        self.assertEqual(len(comparison["bioportal_only"]), 0)
        self.assertEqual(len(comparison["ols_only"]), 0)

        common_term = comparison["common_terms"][0]
        self.assertEqual(common_term["label"], "Hypertension")  # Uses BP label
        self.assertFalse(common_term["uri_match"])

    def test_compare_results_different_counts(self):
        """Test comparison when result counts differ"""
        bp_results = [{"label": "Term 1", "uri": "http://bp.example.org/1", "ontology": "MONDO"}]
        ols_results = [
            {"label": "Term 2", "uri": "http://ols.example.org/2", "ontology": "HP"},
            {"label": "Term 3", "uri": "http://ols.example.org/3", "ontology": "GO"},
        ]
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Check count discrepancy
        self.assertIn("Result count differs: BioPortal=1, OLS=2", comparison["discrepancies"])
        self.assertIn("BioPortal has 1 unique term(s)", comparison["discrepancies"])
        self.assertIn("OLS has 2 unique term(s)", comparison["discrepancies"])

    def test_compare_results_multiple_common_terms(self):
        """Test comparison with multiple common terms"""
        bp_results = [
            {"label": "Term A", "uri": "http://example.org/a", "ontology": "MONDO"},
            {"label": "Term B", "uri": "http://example.org/b", "ontology": "HP"},
            {"label": "BP Only", "uri": "http://bp.example.org/only", "ontology": "NCIT"},
        ]
        ols_results = [
            {"label": "Term A", "uri": "http://example.org/a", "ontology": "MONDO"},
            {"label": "Term B", "uri": "http://different.org/b", "ontology": "GO"},
            {"label": "OLS Only", "uri": "http://ols.example.org/only", "ontology": "EFO"},
        ]
        concept = "test concept"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Check common terms
        self.assertEqual(len(comparison["common_terms"]), 2)

        # Find specific common terms
        term_a = next(t for t in comparison["common_terms"] if t["label"] == "Term A")
        term_b = next(t for t in comparison["common_terms"] if t["label"] == "Term B")

        self.assertTrue(term_a["uri_match"])
        self.assertFalse(term_b["uri_match"])

        # Check unique terms
        self.assertEqual(len(comparison["bioportal_only"]), 1)
        self.assertEqual(comparison["bioportal_only"][0]["label"], "BP Only")

        self.assertEqual(len(comparison["ols_only"]), 1)
        self.assertEqual(comparison["ols_only"][0]["label"], "OLS Only")

    def test_compare_results_complex_scenario(self):
        """Test a complex comparison scenario"""
        bp_results = [
            {"label": "Exact Match", "uri": "http://same.org/exact", "ontology": "MONDO"},
            {"label": "URI Mismatch", "uri": "http://bp.org/mismatch", "ontology": "HP"},
            {"label": "BP Unique 1", "uri": "http://bp.org/unique1", "ontology": "NCIT"},
            {"label": "BP Unique 2", "uri": "http://bp.org/unique2", "ontology": "GO"},
        ]
        ols_results = [
            {"label": "Exact Match", "uri": "http://same.org/exact", "ontology": "MONDO"},
            {"label": "URI Mismatch", "uri": "http://ols.org/mismatch", "ontology": "EFO"},
            {"label": "OLS Unique 1", "uri": "http://ols.org/unique1", "ontology": "DOID"},
        ]
        concept = "complex test"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Check counts
        self.assertEqual(comparison["bioportal_count"], 4)
        self.assertEqual(comparison["ols_count"], 3)

        # Check common terms
        self.assertEqual(len(comparison["common_terms"]), 2)

        # Check unique terms
        self.assertEqual(len(comparison["bioportal_only"]), 2)
        self.assertEqual(len(comparison["ols_only"]), 1)

        # Check discrepancies
        expected_discrepancies = [
            "Result count differs: BioPortal=4, OLS=3",
            "BioPortal has 2 unique term(s)",
            "OLS has 1 unique term(s)",
            "1 common term(s) have different URIs",
        ]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_only_bioportal_results(self):
        """Test comparison with only BioPortal results"""
        bp_results = [
            {"label": "BP Term 1", "uri": "http://bp.example.org/1", "ontology": "MONDO"},
            {"label": "BP Term 2", "uri": "http://bp.example.org/2", "ontology": "HP"},
        ]
        ols_results: list[dict] = []
        concept = "bp only"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["bioportal_count"], 2)
        self.assertEqual(comparison["ols_count"], 0)
        self.assertEqual(len(comparison["common_terms"]), 0)
        self.assertEqual(len(comparison["bioportal_only"]), 2)
        self.assertEqual(len(comparison["ols_only"]), 0)

        expected_discrepancies = [
            "Result count differs: BioPortal=2, OLS=0",
            "BioPortal has 2 unique term(s)",
        ]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_only_ols_results(self):
        """Test comparison with only OLS results"""
        bp_results: list[dict] = []
        ols_results = [
            {"label": "OLS Term 1", "uri": "http://ols.example.org/1", "ontology": "GO"},
            {"label": "OLS Term 2", "uri": "http://ols.example.org/2", "ontology": "NCIT"},
        ]
        concept = "ols only"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["bioportal_count"], 0)
        self.assertEqual(comparison["ols_count"], 2)
        self.assertEqual(len(comparison["common_terms"]), 0)
        self.assertEqual(len(comparison["bioportal_only"]), 0)
        self.assertEqual(len(comparison["ols_only"]), 2)

        expected_discrepancies = [
            "Result count differs: BioPortal=0, OLS=2",
            "OLS has 2 unique term(s)",
        ]
        self.assertEqual(comparison["discrepancies"], expected_discrepancies)

    def test_compare_results_identical_results(self):
        """Test comparison with identical results"""
        bp_results = [
            {"label": "Term 1", "uri": "http://example.org/1", "ontology": "MONDO"},
            {"label": "Term 2", "uri": "http://example.org/2", "ontology": "HP"},
        ]
        ols_results = [
            {"label": "Term 1", "uri": "http://example.org/1", "ontology": "MONDO"},
            {"label": "Term 2", "uri": "http://example.org/2", "ontology": "HP"},
        ]
        concept = "identical test"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        self.assertEqual(comparison["bioportal_count"], 2)
        self.assertEqual(comparison["ols_count"], 2)
        self.assertEqual(len(comparison["common_terms"]), 2)
        self.assertEqual(len(comparison["bioportal_only"]), 0)
        self.assertEqual(len(comparison["ols_only"]), 0)
        self.assertEqual(comparison["discrepancies"], [])

        # All common terms should have matching URIs
        for term in comparison["common_terms"]:
            self.assertTrue(term["uri_match"])

    def test_compare_results_whitespace_and_special_chars(self):
        """Test comparison with labels containing whitespace and special characters"""
        bp_results = [
            {"label": "COVID-19", "uri": "http://bp.example.org/covid", "ontology": "MONDO"}
        ]
        ols_results = [
            {"label": "covid-19", "uri": "http://ols.example.org/covid", "ontology": "HP"}
        ]
        concept = "covid"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Should be treated as common due to case-insensitive matching
        self.assertEqual(len(comparison["common_terms"]), 1)
        self.assertEqual(len(comparison["bioportal_only"]), 0)
        self.assertEqual(len(comparison["ols_only"]), 0)

    def test_compare_results_same_label_different_ontologies(self):
        """Test comparison with same label but different ontologies"""
        bp_results = [
            {"label": "Heart Disease", "uri": "http://bp.example.org/heart", "ontology": "MONDO"}
        ]
        ols_results = [
            {"label": "Heart Disease", "uri": "http://ols.example.org/heart", "ontology": "HP"}
        ]
        concept = "heart disease"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Should be common term despite different ontologies and URIs
        self.assertEqual(len(comparison["common_terms"]), 1)
        common_term = comparison["common_terms"][0]
        self.assertEqual(common_term["bioportal_ontology"], "MONDO")
        self.assertEqual(common_term["ols_ontology"], "HP")
        self.assertFalse(common_term["uri_match"])

    def test_compare_results_preserve_original_data(self):
        """Test that original result data is preserved in comparison"""
        bp_results = [
            {
                "label": "Test Term",
                "uri": "http://bp.example.org/test",
                "ontology": "MONDO",
                "description": "BP description",
                "extra_field": "bp_value",
            }
        ]
        ols_results = [
            {
                "label": "Other Term",
                "uri": "http://ols.example.org/other",
                "ontology": "HP",
                "description": "OLS description",
                "extra_field": "ols_value",
            }
        ]
        concept = "preservation test"

        comparison = ResultComparator.compare_results(bp_results, ols_results, concept)

        # Check that original data is preserved in unique terms
        bp_only = comparison["bioportal_only"][0]
        self.assertEqual(bp_only["description"], "BP description")
        self.assertEqual(bp_only["extra_field"], "bp_value")

        ols_only = comparison["ols_only"][0]
        self.assertEqual(ols_only["description"], "OLS description")
        self.assertEqual(ols_only["extra_field"], "ols_value")


if __name__ == "__main__":
    unittest.main()
