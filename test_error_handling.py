#!/usr/bin/env python3
"""
Test script for error handling and retry mechanisms
"""

import sys
import os
import time
import tempfile
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from utils.error_handling import (
    OntologyMapperError,
    NetworkError,
    TimeoutError,
    RateLimitError,
    ServiceUnavailableError,
    AuthenticationError,
    RetryConfig,
    retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerState,
    check_network_connectivity,
    format_error_message,
    ServiceHealthMonitor
)
from config.error_config import ErrorHandlingConfig


def test_custom_exceptions():
    """Test custom exception classes"""
    print("Testing custom exception classes...")
    
    # Test base exception
    try:
        raise OntologyMapperError("Base error")
    except OntologyMapperError as e:
        assert str(e) == "Base error"
        print("✓ Base exception test passed")
    
    # Test specific exceptions
    exceptions = [
        (NetworkError("Network failed"), NetworkError),
        (TimeoutError("Timeout"), TimeoutError),
        (ServiceUnavailableError("Service down"), ServiceUnavailableError),
        (AuthenticationError("Auth failed"), AuthenticationError)
    ]
    
    for exc, exc_type in exceptions:
        assert isinstance(exc, exc_type)
        assert isinstance(exc, OntologyMapperError)
    
    # Test RateLimitError with retry_after
    rate_limit_err = RateLimitError("Rate limited", retry_after=60)
    assert rate_limit_err.retry_after == 60
    print("✓ All custom exception tests passed")


def test_retry_config():
    """Test retry configuration"""
    print("\nTesting retry configuration...")
    
    config = RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0
    )
    
    # Test delay calculation
    delay0 = config.calculate_delay(0)
    delay1 = config.calculate_delay(1)
    delay2 = config.calculate_delay(2)
    
    assert delay0 >= 0.5 and delay0 <= 1.5  # With jitter
    assert delay1 >= 1.0 and delay1 <= 3.0
    assert delay2 >= 2.0 and delay2 <= 6.0
    
    # Test max delay cap (allow small tolerance for jitter)
    delay10 = config.calculate_delay(10)
    assert delay10 <= 30.5  # Small tolerance for jitter calculation
    
    print("✓ Retry configuration test passed")


def test_retry_decorator_success():
    """Test retry decorator with successful operation"""
    print("\nTesting retry decorator with success...")
    
    call_count = [0]
    
    @retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.1, jitter=False))
    def successful_operation():
        call_count[0] += 1
        return "success"
    
    result = successful_operation()
    assert result == "success"
    assert call_count[0] == 1  # Should only be called once
    print("✓ Retry decorator success test passed")


def test_retry_decorator_eventual_success():
    """Test retry decorator with eventual success"""
    print("\nTesting retry decorator with eventual success...")
    
    call_count = [0]
    
    @retry_with_backoff(RetryConfig(max_retries=3, initial_delay=0.1, jitter=False))
    def eventually_successful():
        call_count[0] += 1
        if call_count[0] < 3:
            raise NetworkError("Network error")
        return "success"
    
    result = eventually_successful()
    assert result == "success"
    assert call_count[0] == 3  # Should be called 3 times
    print("✓ Retry decorator eventual success test passed")


def test_retry_decorator_failure():
    """Test retry decorator with permanent failure"""
    print("\nTesting retry decorator with permanent failure...")
    
    call_count = [0]
    
    @retry_with_backoff(RetryConfig(max_retries=2, initial_delay=0.1, jitter=False))
    def always_fails():
        call_count[0] += 1
        raise NetworkError("Network error")
    
    try:
        always_fails()
        assert False, "Should have raised exception"
    except NetworkError:
        assert call_count[0] == 3  # Initial + 2 retries
        print("✓ Retry decorator failure test passed")


def test_circuit_breaker():
    """Test circuit breaker pattern"""
    print("\nTesting circuit breaker pattern...")
    
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0,
        expected_exception=NetworkError,
        name="TestBreaker"
    )
    
    # Test initial state
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.failure_count == 0
    print("  ✓ Initial state: CLOSED")
    
    # Test successful calls
    result = breaker.call(lambda: "success")
    assert result == "success"
    assert breaker.state == CircuitBreakerState.CLOSED
    print("  ✓ Successful call maintains CLOSED state")
    
    # Test failures leading to OPEN state
    for i in range(3):
        try:
            breaker.call(lambda: (_ for _ in ()).throw(NetworkError("Network error")))
        except NetworkError:
            pass
    
    assert breaker.state == CircuitBreakerState.OPEN
    assert breaker.failure_count >= 3
    print("  ✓ Multiple failures trigger OPEN state")
    
    # Test that circuit breaker blocks requests when OPEN
    try:
        breaker.call(lambda: "should not execute")
        assert False, "Should have raised ServiceUnavailableError"
    except ServiceUnavailableError:
        print("  ✓ OPEN circuit blocks requests")
    
    # Test recovery to HALF_OPEN after timeout
    time.sleep(1.5)
    assert breaker._should_attempt_reset()
    print("  ✓ Recovery timeout triggers HALF_OPEN attempt")
    
    # Test successful call in HALF_OPEN leads to CLOSED
    breaker.state = CircuitBreakerState.HALF_OPEN
    result = breaker.call(lambda: "recovered")
    assert result == "recovered"
    assert breaker.state == CircuitBreakerState.CLOSED
    print("  ✓ Successful call in HALF_OPEN returns to CLOSED")
    
    # Test manual reset
    breaker.state = CircuitBreakerState.OPEN
    breaker.reset()
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.failure_count == 0
    print("  ✓ Manual reset works correctly")
    
    print("✓ Circuit breaker test passed")


def test_error_message_formatting():
    """Test error message formatting"""
    print("\nTesting error message formatting...")
    
    # Test NetworkError
    msg = format_error_message(NetworkError("Connection failed"), user_friendly=True)
    assert "❌" in msg or "Network" in msg
    print("  ✓ NetworkError formatted correctly")
    
    # Test TimeoutError
    msg = format_error_message(TimeoutError("Request timeout"), user_friendly=True)
    assert "⏱️" in msg or "timeout" in msg.lower()
    print("  ✓ TimeoutError formatted correctly")
    
    # Test RateLimitError
    rate_err = RateLimitError("Too many requests", retry_after=60)
    msg = format_error_message(rate_err, user_friendly=True)
    assert "60" in msg or "rate" in msg.lower()
    print("  ✓ RateLimitError formatted correctly")
    
    # Test ServiceUnavailableError
    msg = format_error_message(ServiceUnavailableError("Service down"), user_friendly=True)
    assert "🔧" in msg or "unavailable" in msg.lower()
    print("  ✓ ServiceUnavailableError formatted correctly")
    
    # Test AuthenticationError
    msg = format_error_message(AuthenticationError("Invalid key"), user_friendly=True)
    assert "🔐" in msg or "Authentication" in msg
    print("  ✓ AuthenticationError formatted correctly")
    
    print("✓ Error message formatting test passed")


def test_health_monitor():
    """Test service health monitoring"""
    print("\nTesting service health monitoring...")
    
    monitor = ServiceHealthMonitor()
    
    # Create circuit breakers
    bp_breaker = CircuitBreaker(name="BioPortal", failure_threshold=3)
    ols_breaker = CircuitBreaker(name="OLS", failure_threshold=3)
    
    # Register services
    monitor.register_service("bioportal", bp_breaker)
    monitor.register_service("ols", ols_breaker)
    
    # Test health status
    status = monitor.get_health_status()
    assert "bioportal" in status
    assert "ols" in status
    assert status["bioportal"]["healthy"] == True
    assert status["ols"]["healthy"] == True
    print("  ✓ Health status reports correctly")
    
    # Test available services
    available = monitor.get_available_services()
    assert "bioportal" in available
    assert "ols" in available
    print("  ✓ Available services list correct")
    
    # Test when one service fails
    for _ in range(3):
        try:
            bp_breaker.call(lambda: (_ for _ in ()).throw(NetworkError("Error")))
        except (NetworkError, ServiceUnavailableError):
            pass
    
    assert bp_breaker.state == CircuitBreakerState.OPEN
    available = monitor.get_available_services()
    assert "bioportal" not in available
    assert "ols" in available
    print("  ✓ Health monitor tracks unavailable services")
    
    # Test is_any_service_available
    assert monitor.is_any_service_available() == True
    print("  ✓ At least one service available check works")
    
    print("✓ Health monitor test passed")


def test_error_config():
    """Test error handling configuration"""
    print("\nTesting error handling configuration...")
    
    config = ErrorHandlingConfig()
    
    # Test default values
    assert config.retry_enabled == True
    assert config.max_retries >= 0
    assert config.circuit_breaker_enabled == True
    assert config.request_timeout > 0
    print("  ✓ Default configuration values correct")
    
    # Test environment variable overrides
    os.environ['ERROR_MAX_RETRIES'] = '5'
    os.environ['ERROR_CIRCUIT_BREAKER_THRESHOLD'] = '10'
    config2 = ErrorHandlingConfig()
    assert config2.max_retries == 5
    assert config2.circuit_breaker_threshold == 10
    print("  ✓ Environment variable overrides work")
    
    # Clean up
    del os.environ['ERROR_MAX_RETRIES']
    del os.environ['ERROR_CIRCUIT_BREAKER_THRESHOLD']
    
    print("✓ Error config test passed")


def run_integration_test():
    """Run integration test with mocked API calls"""
    print("\n" + "="*50)
    print("Running integration test...")
    print("="*50)
    
    # This would test the full integration with mocked services
    # Skipping for brevity as it requires more setup
    print("⚠️  Integration test skipped (requires full setup)")


def main():
    """Run all tests"""
    print("\nTesting Error Handling and Retry Mechanisms")
    print("=" * 60)
    
    try:
        test_custom_exceptions()
        test_retry_config()
        test_retry_decorator_success()
        test_retry_decorator_eventual_success()
        test_retry_decorator_failure()
        test_circuit_breaker()
        test_error_message_formatting()
        test_health_monitor()
        test_error_config()
        run_integration_test()
        
        print("\n" + "=" * 60)
        print("✅ All error handling tests passed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
