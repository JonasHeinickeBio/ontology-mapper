"""
OLS API client for ontology lookups.
"""

from typing import Dict, List, Union

import requests

from config import BIOPORTAL_TO_OLS_MAPPING
from utils.loading import LoadingBar


class OLSLookup:
    """Handles OLS (Ontology Lookup Service) API interactions"""

    def __init__(self):
        self.base_url = "https://www.ebi.ac.uk/ols/api/search"

    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Search OLS for concepts with enhanced metadata"""
        params: Dict[str, Union[str, int]] = {"q": query, "rows": max_results, "format": "json"}

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

                results.append(
                    {
                        "uri": uri,
                        "label": label,
                        "ontology": ontology,
                        "description": description,
                        "synonyms": synonyms,
                        "source": "ols",
                    }
                )
            return results
        except Exception as e:
            loading_bar.stop()
            print(f"❌ OLS API Error: {e}")
            return []
        finally:
            loading_bar.stop()

    def _convert_ontologies(self, bioportal_ontologies: str) -> str:
        """Convert BioPortal ontology names to OLS equivalents"""
        bp_onts = [ont.strip().upper() for ont in bioportal_ontologies.split(",")]
        ols_onts = [
            BIOPORTAL_TO_OLS_MAPPING.get(ont, ont.lower())
            for ont in bp_onts
            if BIOPORTAL_TO_OLS_MAPPING.get(ont)
        ]

        return ",".join(ols_onts) if ols_onts else ""
