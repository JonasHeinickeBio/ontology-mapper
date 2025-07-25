"""
Comparison and ranking service for ontology results.
"""

from typing import Any


class ResultComparator:
    """Compares results from BioPortal and OLS to identify discrepancies"""

    @staticmethod
    def compare_results(
        bp_results: list[dict], ols_results: list[dict], concept: str
    ) -> dict[str, Any]:
        """Compare BioPortal and OLS results and identify discrepancies"""
        comparison: dict[str, Any] = {
            "concept": concept,
            "bioportal_count": len(bp_results),
            "ols_count": len(ols_results),
            "common_terms": [],
            "bioportal_only": [],
            "ols_only": [],
            "discrepancies": [],
        }

        # Create lookup dictionaries for comparison
        bp_labels = {result["label"].lower(): result for result in bp_results}
        ols_labels = {result["label"].lower(): result for result in ols_results}

        # Find common terms
        common_labels: set[str] = set(bp_labels.keys()) & set(ols_labels.keys())
        for label in common_labels:
            bp_result = bp_labels[label]
            ols_result = ols_labels[label]

            common_term = {
                "label": bp_result["label"],
                "bioportal_uri": bp_result["uri"],
                "ols_uri": ols_result["uri"],
                "bioportal_ontology": bp_result["ontology"],
                "ols_ontology": ols_result["ontology"],
                "uri_match": bp_result["uri"] == ols_result["uri"],
            }
            comparison["common_terms"].append(common_term)

        # Find BioPortal-only terms
        bp_only_labels: set[str] = set(bp_labels.keys()) - set(ols_labels.keys())
        for label in bp_only_labels:
            comparison["bioportal_only"].append(bp_labels[label])

        # Find OLS-only terms
        ols_only_labels: set[str] = set(ols_labels.keys()) - set(bp_labels.keys())
        for label in ols_only_labels:
            comparison["ols_only"].append(ols_labels[label])

        # Identify discrepancies
        if len(bp_results) != len(ols_results):
            comparison["discrepancies"].append(
                f"Result count differs: BioPortal={len(bp_results)}, OLS={len(ols_results)}"
            )

        if len(bp_only_labels) > 0:
            comparison["discrepancies"].append(
                f"BioPortal has {len(bp_only_labels)} unique term(s)"
            )

        if len(ols_only_labels) > 0:
            comparison["discrepancies"].append(f"OLS has {len(ols_only_labels)} unique term(s)")

        # Check for URI mismatches in common terms
        uri_mismatches = [term for term in comparison["common_terms"] if not term["uri_match"]]
        if uri_mismatches:
            comparison["discrepancies"].append(
                f"{len(uri_mismatches)} common term(s) have different URIs"
            )

        return comparison
