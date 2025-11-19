"""
Concept lookup orchestration across multiple services.
"""

import logging
from typing import List, Dict, Tuple, Optional

from services import BioPortalLookup, OLSLookup, ResultComparator
from config import SEARCH_STRATEGIES
from utils.health_monitor import get_service_registry

logger = logging.getLogger(__name__)


class ConceptLookup:
    """Handles concept-specific lookups across multiple services"""
    
    def __init__(self, bioportal: BioPortalLookup, ols: OLSLookup, default_ontologies: Optional[str] = None):
        self.bioportal = bioportal
        self.ols = ols
        self.default_ontologies = default_ontologies
        self.search_strategies = SEARCH_STRATEGIES
        
        # Register services for health monitoring
        self.service_registry = get_service_registry()
        if hasattr(bioportal, 'circuit_breaker') and bioportal.circuit_breaker:
            self.service_registry.register('bioportal', bioportal.circuit_breaker)
        if hasattr(ols, 'circuit_breaker') and ols.circuit_breaker:
            self.service_registry.register('ols', ols.circuit_breaker)
    
    def lookup_concept(self, concept: Dict, max_results: int = 5) -> Tuple[List[Dict], Dict]:
        """Perform lookup across both BioPortal and OLS with comparison and graceful degradation"""
        key = concept['key']
        label = concept['label']
        
        # Get search strategy
        strategy = self.search_strategies.get(key, {
            'variants': [label, label.lower()],
            'ontologies': 'MONDO,HP,NCIT'
        })
        
        # Use default ontologies if specified, otherwise use strategy ontologies
        ontologies = self.default_ontologies or strategy['ontologies']
        
        # Check which services are available
        available_services = self.service_registry.get_available_services()
        bioportal_available = 'bioportal' in available_services or not hasattr(self.bioportal, 'circuit_breaker')
        ols_available = 'ols' in available_services or not hasattr(self.ols, 'circuit_breaker')
        
        # Warn if services are unavailable
        if not bioportal_available and not ols_available:
            logger.error("All services unavailable. Cannot perform lookup.")
            print("⚠️  All ontology services are currently unavailable. Please try again later.")
            return [], {}
        elif not bioportal_available:
            logger.warning("BioPortal service unavailable. Using OLS only.")
            print("⚠️  BioPortal service unavailable. Searching OLS only...")
        elif not ols_available:
            logger.warning("OLS service unavailable. Using BioPortal only.")
            print("⚠️  OLS service unavailable. Searching BioPortal only...")
        
        # Show progress for multiple variants
        variants = strategy['variants']
        if len(variants) > 1:
            print(f"🔄 Searching {len(variants)} variants for '{label}'...")
        
        # Collect results from both services with graceful degradation
        all_bp_results = []
        all_ols_results = []
        
        for i, variant in enumerate(variants, 1):
            # Show progress for multiple variants
            if len(variants) > 1:
                print(f"  [{i}/{len(variants)}] Searching: '{variant}'")
            
            # BioPortal search (if available)
            if bioportal_available:
                try:
                    bp_results = self.bioportal.search(variant, ontologies, max_results=max_results)
                    for result in bp_results:
                        if result not in all_bp_results:
                            all_bp_results.append(result)
                    self.service_registry.mark_success('bioportal')
                except Exception as e:
                    logger.error(f"BioPortal search failed: {e}")
                    self.service_registry.mark_failure('bioportal')
            
            # OLS search (if available)
            if ols_available:
                try:
                    ols_results = self.ols.search(variant, ontologies, max_results=max_results)
                    for result in ols_results:
                        if result not in all_ols_results:
                            all_ols_results.append(result)
                    self.service_registry.mark_success('ols')
                except Exception as e:
                    logger.error(f"OLS search failed: {e}")
                    self.service_registry.mark_failure('ols')
        
        # Compare results (skip if one service is unavailable)
        if bioportal_available and ols_available:
            comparison = ResultComparator.compare_results(all_bp_results, all_ols_results, label)
        else:
            # Simplified comparison when only one service is available
            comparison = {
                'bioportal_only': [] if not bioportal_available else all_bp_results,
                'ols_only': [] if not ols_available else all_ols_results,
                'common': []
            }
        
        # Combine and deduplicate results
        combined_results = self._combine_results(all_bp_results, all_ols_results)
        
        # Log if no results found
        if not combined_results:
            logger.warning(f"No results found for '{label}' from any available service")
        
        return combined_results[:max_results * 2], comparison  # Allow more options
    
    def _combine_results(self, bp_results: List[Dict], ols_results: List[Dict]) -> List[Dict]:
        """Combine results from both services, avoiding duplicates"""
        combined = []
        seen_uris = set()
        
        # Add BioPortal results first
        for result in bp_results:
            if result['uri'] not in seen_uris:
                combined.append(result)
                seen_uris.add(result['uri'])
        
        # Add OLS results that aren't already included
        for result in ols_results:
            if result['uri'] not in seen_uris:
                # Mark as OLS-only
                result['ols_only'] = True
                combined.append(result)
                seen_uris.add(result['uri'])
        
        return combined
