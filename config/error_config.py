"""
Error handling configuration for the ontology mapper.
Provides configurable policies for retries, circuit breakers, and timeouts.
"""

import os
from typing import Optional


class ErrorHandlingConfig:
    """Configuration for error handling behavior"""
    
    def __init__(self):
        """Initialize error handling configuration from environment variables"""
        
        # Retry configuration
        self.retry_enabled = self._get_bool_env('ERROR_RETRY_ENABLED', True)
        self.max_retries = self._get_int_env('ERROR_MAX_RETRIES', 3)
        self.initial_retry_delay = self._get_float_env('ERROR_INITIAL_DELAY', 1.0)
        self.max_retry_delay = self._get_float_env('ERROR_MAX_DELAY', 60.0)
        self.retry_exponential_base = self._get_float_env('ERROR_EXPONENTIAL_BASE', 2.0)
        self.retry_jitter = self._get_bool_env('ERROR_RETRY_JITTER', True)
        
        # Circuit breaker configuration
        self.circuit_breaker_enabled = self._get_bool_env('ERROR_CIRCUIT_BREAKER_ENABLED', True)
        self.circuit_breaker_threshold = self._get_int_env('ERROR_CIRCUIT_BREAKER_THRESHOLD', 5)
        self.circuit_breaker_timeout = self._get_float_env('ERROR_CIRCUIT_BREAKER_TIMEOUT', 60.0)
        
        # Timeout configuration
        self.request_timeout = self._get_float_env('ERROR_REQUEST_TIMEOUT', 30.0)
        self.long_request_timeout = self._get_float_env('ERROR_LONG_REQUEST_TIMEOUT', 120.0)
        
        # Network check configuration
        self.network_check_enabled = self._get_bool_env('ERROR_NETWORK_CHECK_ENABLED', True)
        self.network_check_timeout = self._get_float_env('ERROR_NETWORK_CHECK_TIMEOUT', 3.0)
        
        # Logging configuration
        self.verbose_errors = self._get_bool_env('ERROR_VERBOSE', False)
        self.log_errors_to_file = self._get_bool_env('ERROR_LOG_TO_FILE', False)
        self.error_log_path = os.getenv('ERROR_LOG_PATH', 'logs/errors.log')
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    def __repr__(self) -> str:
        """String representation of configuration"""
        return (
            f"ErrorHandlingConfig("
            f"retry_enabled={self.retry_enabled}, "
            f"max_retries={self.max_retries}, "
            f"circuit_breaker_enabled={self.circuit_breaker_enabled}, "
            f"request_timeout={self.request_timeout}s)"
        )


# Default configuration instance
DEFAULT_ERROR_CONFIG = ErrorHandlingConfig()
