"""
BioPortal API client for ontology lookups.
"""

import os
import requests
import logging
from typing import List, Dict, Optional

from utils.loading import LoadingBar
from cache import CacheManager, CacheConfig
from utils.error_handling import (
    retry_with_backoff,
    RetryConfig,
    CircuitBreaker,
    NetworkError,
    TimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    AuthenticationError,
    format_error_message,
    check_network_connectivity
)
from config.error_config import DEFAULT_ERROR_CONFIG

logger = logging.getLogger(__name__)


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
        
        # Initialize error handling
        self.error_config = DEFAULT_ERROR_CONFIG
        
        # Initialize circuit breaker
        if self.error_config.circuit_breaker_enabled:
            self.circuit_breaker = CircuitBreaker(
                failure_threshold=self.error_config.circuit_breaker_threshold,
                recovery_timeout=self.error_config.circuit_breaker_timeout,
                expected_exception=(NetworkError, TimeoutError, ServiceUnavailableError),
                name="BioPortal"
            )
        else:
            self.circuit_breaker = None
        
    def search(self, query: str, ontologies: str = "", max_results: int = 5) -> List[Dict]:
        """Search BioPortal for concepts with enhanced metadata and error handling"""
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
        
        # Check network connectivity if enabled
        if self.error_config.network_check_enabled:
            if not check_network_connectivity(timeout=self.error_config.network_check_timeout):
                error_msg = format_error_message(
                    NetworkError("No network connectivity"),
                    context="BioPortal search"
                )
                print(error_msg)
                logger.error(f"Network check failed for BioPortal search: {query}")
                return []
        
        # Use circuit breaker if enabled
        if self.circuit_breaker:
            try:
                return self.circuit_breaker.call(self._perform_search, query, ontologies, max_results)
            except ServiceUnavailableError as e:
                error_msg = format_error_message(e, context="BioPortal search")
                print(error_msg)
                logger.warning(f"Circuit breaker open for BioPortal: {e}")
                return []
        else:
            return self._perform_search(query, ontologies, max_results)
    
    def _perform_search(self, query: str, ontologies: str, max_results: int) -> List[Dict]:
        """Perform the actual search with retry logic"""
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
            self.cache.set(query, ontologies, 'bioportal', results)
            return results
            
        except (NetworkError, TimeoutError, ServiceUnavailableError) as e:
            loading_bar.stop()
            error_msg = format_error_message(e, context="BioPortal search")
            print(error_msg)
            logger.error(f"API error in BioPortal search for '{query}': {e}")
            return []
        except AuthenticationError as e:
            loading_bar.stop()
            error_msg = format_error_message(e, context="BioPortal search")
            print(error_msg)
            logger.error(f"Authentication error in BioPortal: {e}")
            return []
        except RateLimitError as e:
            loading_bar.stop()
            error_msg = format_error_message(e, context="BioPortal search")
            print(error_msg)
            logger.warning(f"Rate limit exceeded for BioPortal: {e}")
            return []
        except Exception as e:
            loading_bar.stop()
            error_msg = f"❌ BioPortal API Error: {e}"
            print(error_msg)
            logger.error(f"Unexpected error in BioPortal search for '{query}': {e}")
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
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError(f"Authentication failed: {response.status_code}")
            elif response.status_code == 429:
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
            
            return results
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.error_config.request_timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            # Let other request exceptions be handled by the caller
            raise
