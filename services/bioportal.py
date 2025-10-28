"""
BioPortal API client for ontology lookups.
"""

import os
import requests
from typing import List, Dict, Optional

from utils.loading import LoadingBar
from cache import CacheManager, CacheConfig


class BioPortalLookup:
    """Handles BioPortal API interactions"""
    
    def __init__(self, api_key: Optional[str] = None, cache_manager: Optional[CacheManager] = None):
        self.api_key = api_key or os.getenv('BIOPORTAL_API_KEY')
        self.base_url = "https://data.bioontology.org/search"
        
        # Initialize cache
        if cache_manager is None:
            cache_config = CacheConfig()
            self.cache = CacheManager(cache_config)
        else:
            self.cache = cache_manager
        
    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Search BioPortal for concepts with enhanced metadata"""
        # Check cache first
        cached_results = self.cache.get(query, ontologies, 'bioportal')
        if cached_results is not None:
            print(f"💾 Using cached BioPortal results for '{query}'")
            return cached_results
        
        if not self.api_key or self.api_key == 'your_api_key_here':
            # Demo mode
            demo_results = [{
                'uri': f"http://demo.org/{query.replace(' ', '_')}",
                'label': f"Demo: {query}",
                'ontology': "DEMO",
                'description': f"Demo description for {query}",
                'synonyms': [f"Demo synonym for {query}"],
                'source': 'bioportal_demo'
            }]
            # Cache demo results
            self.cache.set(query, ontologies, 'bioportal', demo_results)
            return demo_results
        
        params = {
            "q": query,
            "apikey": self.api_key,
            "pagesize": max_results,
            "format": "json"
        }
        if ontologies:
            params["ontologies"] = ontologies
        
        # Start loading bar
        loading_bar = LoadingBar(f"🌐 Searching BioPortal for '{query}'", "pulse")
        loading_bar.start()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("collection", []):
                uri = item.get("@id", "")
                label = item.get("prefLabel", "")
                
                # Extract ontology from links
                ontology = ""
                for link in item.get("links", {}).values():
                    if isinstance(link, str) and "/ontologies/" in link:
                        ontology = link.split("/ontologies/")[-1].split("/")[0]
                        break
                
                # Get additional metadata if available
                definition = item.get("definition", [""])[0] if item.get("definition") else ""
                synonyms = item.get("synonym", []) or []
                
                results.append({
                    'uri': uri,
                    'label': label,
                    'ontology': ontology,
                    'description': definition,
                    'synonyms': synonyms,
                    'source': 'bioportal'
                })
            
            # Cache the results
            self.cache.set(query, ontologies, 'bioportal', results)
            return results
        except Exception as e:
            loading_bar.stop()
            print(f"❌ BioPortal API Error: {e}")
            return []
        finally:
            loading_bar.stop()
