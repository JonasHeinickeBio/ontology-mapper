"""
OLS API client for ontology lookups.
"""

import requests
from typing import List, Dict, Optional

from utils.loading import LoadingBar
from config import BIOPORTAL_TO_OLS_MAPPING
from cache import CacheManager, CacheConfig


class OLSLookup:
    """Handles OLS (Ontology Lookup Service) API interactions"""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.base_url = "https://www.ebi.ac.uk/ols/api/search"
        
        # Initialize cache
        if cache_manager is None:
            cache_config = CacheConfig()
            self.cache = CacheManager(cache_config)
        else:
            self.cache = cache_manager
        
    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Search OLS for concepts with enhanced metadata"""
        # Check cache first
        cached_results = self.cache.get(query, ontologies, 'ols')
        if cached_results is not None:
            print(f"💾 Using cached OLS results for '{query}'")
            return cached_results
        
        params = {
            "q": query,
            "rows": max_results,
            "format": "json"
        }
        
        # Convert BioPortal ontology names to OLS format where possible
        if ontologies:
            ols_ontologies = self._convert_ontologies(ontologies)
            if ols_ontologies:
                params["ontology"] = ols_ontologies
        
        # Start loading bar
        loading_bar = LoadingBar(f"🔬 Searching OLS for '{query}'", "dots")
        loading_bar.start()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            docs = data.get("response", {}).get("docs", [])
            
            for item in docs:
                uri = item.get("iri", "")
                label = item.get("label", "")
                ontology = item.get("ontology_name", "").upper()
                
                # Extract description and synonyms
                description = item.get("description", [""])[0] if item.get("description") else ""
                synonyms = item.get("synonym", []) or []
                
                results.append({
                    'uri': uri,
                    'label': label,
                    'ontology': ontology,
                    'description': description,
                    'synonyms': synonyms,
                    'source': 'ols'
                })
            
            # Cache the results
            self.cache.set(query, ontologies, 'ols', results)
            return results
        except Exception as e:
            loading_bar.stop()
            print(f"❌ OLS API Error: {e}")
            return []
        finally:
            loading_bar.stop()
    
    def _convert_ontologies(self, bioportal_ontologies: str) -> str:
        """Convert BioPortal ontology names to OLS equivalents"""
        bp_onts = [ont.strip().upper() for ont in bioportal_ontologies.split(',')]
        ols_onts = [BIOPORTAL_TO_OLS_MAPPING.get(ont, ont.lower()) for ont in bp_onts if BIOPORTAL_TO_OLS_MAPPING.get(ont)]
        
        return ','.join(ols_onts) if ols_onts else ""
