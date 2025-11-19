"""
Advanced error handling utilities including retry mechanisms, circuit breakers,
and custom exception classes for the ontology mapper.
"""

import time
import functools
import logging
from typing import Callable, Optional, Tuple, Type, Any
from datetime import datetime, timedelta


# Configure logging
logger = logging.getLogger(__name__)


# Custom Exception Classes
class OntologyMapperError(Exception):
    """Base exception for all ontology mapper errors"""
    pass


class APIError(OntologyMapperError):
    """Base class for API-related errors"""
    pass


class NetworkError(APIError):
    """Network connectivity issues"""
    pass


class TimeoutError(APIError):
    """Request timeout errors"""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServiceUnavailableError(APIError):
    """External service is unavailable"""
    pass


class AuthenticationError(APIError):
    """Authentication/authorization failures"""
    pass


class CacheError(OntologyMapperError):
    """Cache-related errors"""
    pass


class ParseError(OntologyMapperError):
    """Parsing errors"""
    pass


# Retry Mechanism with Exponential Backoff
class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (
            NetworkError,
            TimeoutError,
            ServiceUnavailableError,
        )
    ):
        """
        Initialize retry configuration
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Add random jitter to avoid thundering herd
            retryable_exceptions: Tuple of exception types that should trigger retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt with exponential backoff"""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator that implements retry logic with exponential backoff
    
    Args:
        config: RetryConfig instance or None for defaults
        on_retry: Optional callback function called on each retry
    
    Example:
        @retry_with_backoff(RetryConfig(max_retries=5))
        def fetch_data():
            return requests.get(url)
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}"
                        )
                except Exception as e:
                    # Non-retryable exception, raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            # All retries exhausted
            raise last_exception
        
        return wrapper
    return decorator


# Circuit Breaker Pattern
class CircuitBreakerState:
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance
    
    Prevents cascading failures by stopping requests to failing services
    and allowing them time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying half-open state
            expected_exception: Exception type that counts as failure
            name: Name for logging purposes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments for the function
        
        Returns:
            Function result
        
        Raises:
            ServiceUnavailableError: If circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"{self.name}: Attempting recovery (HALF_OPEN)")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise ServiceUnavailableError(
                    f"{self.name}: Circuit breaker is OPEN. "
                    f"Service unavailable. Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"{self.name}: Recovery successful. Circuit CLOSED")
        
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(
                f"{self.name}: Failure threshold reached ({self.failure_count}). "
                f"Circuit OPEN for {self.recovery_timeout}s"
            )
            self.state = CircuitBreakerState.OPEN
    
    def reset(self):
        """Manually reset the circuit breaker"""
        logger.info(f"{self.name}: Manual reset")
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


def circuit_breaker(breaker: CircuitBreaker):
    """
    Decorator to apply circuit breaker to a function
    
    Args:
        breaker: CircuitBreaker instance
    
    Example:
        api_breaker = CircuitBreaker(name="BioPortal")
        
        @circuit_breaker(api_breaker)
        def fetch_data():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Network Connectivity Check
def check_network_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Check if network connectivity is available
    
    Args:
        host: Host to check (default: Google DNS)
        port: Port to check
        timeout: Timeout in seconds
    
    Returns:
        True if network is available, False otherwise
    """
    import socket
    
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except (socket.error, socket.timeout):
        return False


# Error Message Formatting
def format_error_message(
    error: Exception,
    context: Optional[str] = None,
    user_friendly: bool = True
) -> str:
    """
    Format error message for display
    
    Args:
        error: Exception to format
        context: Additional context about what was being attempted
        user_friendly: If True, return simplified message for end users
    
    Returns:
        Formatted error message
    """
    if isinstance(error, NetworkError):
        base_msg = "Network connection failed"
        if user_friendly:
            return f"❌ {base_msg}. Please check your internet connection."
    
    elif isinstance(error, TimeoutError):
        base_msg = "Request timed out"
        if user_friendly:
            return f"⏱️ {base_msg}. The service is taking too long to respond. Please try again."
    
    elif isinstance(error, RateLimitError):
        base_msg = "API rate limit exceeded"
        if user_friendly:
            retry_msg = f" Try again in {error.retry_after}s." if error.retry_after else ""
            return f"⚠️ {base_msg}.{retry_msg}"
    
    elif isinstance(error, ServiceUnavailableError):
        base_msg = "Service is temporarily unavailable"
        if user_friendly:
            return f"🔧 {base_msg}. Please try again later."
    
    elif isinstance(error, AuthenticationError):
        base_msg = "Authentication failed"
        if user_friendly:
            return f"🔐 {base_msg}. Please check your API key configuration."
    
    else:
        base_msg = str(error)
    
    if context and not user_friendly:
        return f"{context}: {base_msg}"
    
    return base_msg if user_friendly else f"Error: {base_msg}"


# Graceful Degradation Helper
class ServiceHealthMonitor:
    """Monitor health of external services"""
    
    def __init__(self):
        self.services = {}
    
    def register_service(self, name: str, circuit_breaker: CircuitBreaker):
        """Register a service for health monitoring"""
        self.services[name] = circuit_breaker
    
    def get_health_status(self) -> dict:
        """Get health status of all registered services"""
        return {
            name: {
                'healthy': breaker.state == CircuitBreakerState.CLOSED,
                'state': breaker.get_state()
            }
            for name, breaker in self.services.items()
        }
    
    def get_available_services(self) -> list:
        """Get list of currently available services"""
        return [
            name for name, breaker in self.services.items()
            if breaker.state == CircuitBreakerState.CLOSED
        ]
    
    def is_any_service_available(self) -> bool:
        """Check if at least one service is available"""
        return len(self.get_available_services()) > 0
