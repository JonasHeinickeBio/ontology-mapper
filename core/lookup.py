"""
Concept lookup orchestration across multiple services.
"""

from typing import Dict, List, Optional, Tuple

from config import SEARCH_STRATEGIES
from services import BioPortalLookup, OLSLookup, ResultComparator


class ConceptLookup:
    """Handles concept-specific lookups across multiple services"""

    def __init__(
        self, bioportal: BioPortalLookup, ols: OLSLookup, default_ontologies: Optional[str] = None
    ):
        self.bioportal = bioportal
        self.ols = ols
        self.default_ontologies = default_ontologies
        self.search_strategies = SEARCH_STRATEGIES

    def lookup_concept(self, concept: Dict, max_results: int = 5) -> Tuple[List[Dict], Dict]:
        """Perform lookup across both BioPortal and OLS with comparison"""
        key = concept["key"]
        label = concept["label"]

        # Get search strategy
        strategy = self.search_strategies.get(
            key, {"variants": [label, label.lower()], "ontologies": "MONDO,HP,NCIT"}
        )

        # Use default ontologies if specified, otherwise use strategy ontologies
        ontologies = self.default_ontologies or strategy["ontologies"]

        # Show progress for multiple variants
        variants = strategy["variants"]
        if len(variants) > 1:
            print(f"🔄 Searching {len(variants)} variants for '{label}'...")

        # Collect results from both services
        all_bp_results = []
        all_ols_results = []

        for i, variant in enumerate(variants, 1):
            # Show progress for multiple variants
            if len(variants) > 1:
                print(f"  [{i}/{len(variants)}] Searching: '{variant}'")

            # BioPortal search
            bp_results = self.bioportal.search(variant, ontologies, max_results=max_results)
            for result in bp_results:
                if result not in all_bp_results:
                    all_bp_results.append(result)

            # OLS search
            ols_results = self.ols.search(variant, ontologies, max_results=max_results)
            for result in ols_results:
                if result not in all_ols_results:
                    all_ols_results.append(result)

        # Compare results
        comparison = ResultComparator.compare_results(all_bp_results, all_ols_results, label)

        # Combine and deduplicate results
        combined_results = self._combine_results(all_bp_results, all_ols_results)

        return combined_results[: max_results * 2], comparison  # Allow more options

    def _combine_results(self, bp_results: List[Dict], ols_results: List[Dict]) -> List[Dict]:
        """Combine results from both services, avoiding duplicates"""
        combined = []
        seen_uris = set()

        # Add BioPortal results first
        for result in bp_results:
            if result["uri"] not in seen_uris:
                combined.append(result)
                seen_uris.add(result["uri"])

        # Add OLS results that aren't already included
        for result in ols_results:
            if result["uri"] not in seen_uris:
                # Mark as OLS-only
                result["ols_only"] = True
                combined.append(result)
                seen_uris.add(result["uri"])

        return combined
