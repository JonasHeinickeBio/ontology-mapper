"""
OLS API client for ontology lookups.
"""

import requests
import logging
from typing import List, Dict, Optional

from utils.loading import LoadingBar
from config import BIOPORTAL_TO_OLS_MAPPING
from cache import CacheManager, CacheConfig
from utils.error_handling import (
    retry_with_backoff,
    RetryConfig,
    CircuitBreaker,
    NetworkError,
    TimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    format_error_message,
    check_network_connectivity
)
from config.error_config import DEFAULT_ERROR_CONFIG

logger = logging.getLogger(__name__)


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
        
        # Initialize error handling
        self.error_config = DEFAULT_ERROR_CONFIG
        
        # Initialize circuit breaker
        if self.error_config.circuit_breaker_enabled:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=self.error_config.circuit_breaker_threshold,
                recovery_timeout=self.error_config.circuit_breaker_timeout,
                expected_exception=(NetworkError, TimeoutError, ServiceUnavailableError),
                name="OLS"
            )
        else:
            self.circuit_breaker = None
        
    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Search OLS for concepts with enhanced metadata and error handling"""
        # Check cache first
        cached_results = self.cache.get(query, ontologies, 'ols')
        if cached_results is not None:
            print(f"💾 Using cached OLS results for '{query}'")
            return cached_results
        
        # Check network connectivity if enabled
        if self.error_config.network_check_enabled:
            if not check_network_connectivity(timeout=self.error_config.network_check_timeout):
                error_msg = format_error_message(
                    NetworkError("No network connectivity"),
                    context="OLS search"
                )
                print(error_msg)
                logger.error(f"Network check failed for OLS search: {query}")
                return []
        
        # Use circuit breaker if enabled
        if self.circuit_breaker:
            try:
                return self.circuit_breaker.call(self._perform_search, query, ontologies, max_results)
            except ServiceUnavailableError as e:
                error_msg = format_error_message(e, context="OLS search")
                print(error_msg)
                logger.warning(f"Circuit breaker open for OLS: {e}")
                return []
        else:
            return self._perform_search(query, ontologies, max_results)
    
    def _perform_search(self, query: str, ontologies: str, max_results: int) -> List[Dict]:
        """Perform the actual search with retry logic"""
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
            # Apply retry logic if enabled
            if self.error_config.retry_enabled:
                retry_config = RetryConfig(
                    max_retries=self.error_config.max_retries,
                    initial_delay=self.error_config.initial_retry_delay,
                    max_delay=self.error_config.max_retry_delay,
                    exponential_base=self.error_config.retry_exponential_base,
                    jitter=self.error_config.retry_jitter
                )
                
                @retry_with_backoff(retry_config)
                def make_request():
                    return self._make_api_request(params)
                
                results = make_request()
            else:
                results = self._make_api_request(params)
            
            # Cache the results
            self.cache.set(query, ontologies, 'ols', results)
            return results
            
        except (NetworkError, TimeoutError, ServiceUnavailableError) as e:
            loading_bar.stop()
            error_msg = format_error_message(e, context="OLS search")
            print(error_msg)
            logger.error(f"API error in OLS search for '{query}': {e}")
            return []
        except RateLimitError as e:
            loading_bar.stop()
            error_msg = format_error_message(e, context="OLS search")
            print(error_msg)
            logger.warning(f"Rate limit exceeded for OLS: {e}")
            return []
        except Exception as e:
            loading_bar.stop()
            error_msg = f"❌ OLS API Error: {e}"
            print(error_msg)
            logger.error(f"Unexpected error in OLS search for '{query}': {e}")
            return []
        finally:
            loading_bar.stop()
    
    def _make_api_request(self, params: Dict) -> List[Dict]:
        """Make the actual API request with proper error translation"""
        try:
            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.error_config.request_timeout
            )
            
            # Handle different HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=int(retry_after) if retry_after else None
                )
            elif response.status_code == 503 or response.status_code == 502:
                raise ServiceUnavailableError(f"Service unavailable: {response.status_code}")
            elif response.status_code >= 500:
                raise ServiceUnavailableError(f"Server error: {response.status_code}")
            
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
            
            return results
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.error_config.request_timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            # Let other request exceptions be handled by the caller
            raise
    
    def _convert_ontologies(self, bioportal_ontologies: str) -> str:
        """Convert BioPortal ontology names to OLS equivalents"""
        bp_onts = [ont.strip().upper() for ont in bioportal_ontologies.split(',')]
        ols_onts = [BIOPORTAL_TO_OLS_MAPPING.get(ont, ont.lower()) for ont in bp_onts if BIOPORTAL_TO_OLS_MAPPING.get(ont)]
        
        return ','.join(ols_onts) if ols_onts else ""
