#!/usr/bin/env python3
"""
Demo script showing error handling and retry mechanisms in action.

This script demonstrates:
- Retry with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Error message formatting
- Health monitoring
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.error_handling import (
    retry_with_backoff,
    RetryConfig,
    CircuitBreaker,
    NetworkError,
    ServiceUnavailableError,
    format_error_message,
    check_network_connectivity
)
from utils.health_monitor import get_service_registry


def demo_retry_mechanism():
    """Demo: Retry with exponential backoff"""
    print("\n" + "="*60)
    print("DEMO 1: Retry Mechanism with Exponential Backoff")
    print("="*60)
    
    attempt_count = [0]
    
    # Configure retry with custom settings
    retry_config = RetryConfig(
        max_retries=3,
        initial_delay=0.5,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    
    @retry_with_backoff(retry_config)
    def flaky_operation():
        """Simulates an operation that fails initially but eventually succeeds"""
        attempt_count[0] += 1
        print(f"  Attempt {attempt_count[0]}: Making API call...")
        
        if attempt_count[0] < 3:
            raise NetworkError("Network temporarily unavailable")
        
        return "Success!"
    
    try:
        print("\nSimulating a flaky network connection...")
        result = flaky_operation()
        print(f"\n✅ Operation succeeded: {result}")
        print(f"Total attempts: {attempt_count[0]}")
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")


def demo_circuit_breaker():
    """Demo: Circuit breaker pattern"""
    print("\n" + "="*60)
    print("DEMO 2: Circuit Breaker Pattern")
    print("="*60)
    
    # Create a circuit breaker
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=5.0,
        expected_exception=NetworkError,
        name="DemoAPI"
    )
    
    print(f"\nInitial state: {breaker.state}")
    
    # Simulate multiple failures
    print("\nSimulating repeated failures...")
    for i in range(5):
        try:
            def failing_call():
                raise NetworkError("Service down")
            
            breaker.call(failing_call)
        except (NetworkError, ServiceUnavailableError) as e:
            print(f"  Attempt {i+1}: {type(e).__name__}")
            if breaker.state == "OPEN":
                print(f"    → Circuit breaker is now OPEN!")
                break
    
    print(f"\nCircuit state after failures: {breaker.state}")
    print(f"Failure count: {breaker.failure_count}")
    
    # Show that requests are blocked
    print("\nTrying to make a call while circuit is open...")
    try:
        breaker.call(lambda: "Should not execute")
    except ServiceUnavailableError as e:
        print(f"  ✓ Request blocked: {format_error_message(e, user_friendly=True)}")
    
    # Demonstrate recovery
    print("\nWaiting for recovery timeout...")
    print("  (In production, this would be 60+ seconds)")
    time.sleep(2)
    breaker.recovery_timeout = 1.0  # Reduce for demo
    
    print("\nManually resetting circuit breaker...")
    breaker.reset()
    print(f"Circuit state after reset: {breaker.state}")


def demo_error_messages():
    """Demo: Error message formatting"""
    print("\n" + "="*60)
    print("DEMO 3: User-Friendly Error Messages")
    print("="*60)
    
    errors = [
        NetworkError("Connection refused"),
        ServiceUnavailableError("Service is down for maintenance"),
        # Note: Cannot import TimeoutError and RateLimitError without conflict
    ]
    
    print("\nFormatting various error types for users:")
    for error in errors:
        user_msg = format_error_message(error, user_friendly=True)
        tech_msg = format_error_message(error, user_friendly=False, context="API Call")
        
        print(f"\n  Error Type: {type(error).__name__}")
        print(f"  User Message: {user_msg}")
        print(f"  Technical Message: {tech_msg}")


def demo_health_monitoring():
    """Demo: Service health monitoring"""
    print("\n" + "="*60)
    print("DEMO 4: Service Health Monitoring")
    print("="*60)
    
    # Get service registry
    registry = get_service_registry()
    
    # Register demo services with circuit breakers
    bp_breaker = CircuitBreaker(name="BioPortal", failure_threshold=3)
    ols_breaker = CircuitBreaker(name="OLS", failure_threshold=3)
    
    registry.register("bioportal", bp_breaker)
    registry.register("ols", ols_breaker)
    
    print("\nRegistered services:")
    for service in ["bioportal", "ols"]:
        available = registry.is_available(service)
        status = "✓ Available" if available else "✗ Unavailable"
        print(f"  {service}: {status}")
    
    # Simulate a service failure
    print("\nSimulating BioPortal failures...")
    for i in range(3):
        try:
            bp_breaker.call(lambda: (_ for _ in ()).throw(NetworkError("Error")))
        except (NetworkError, ServiceUnavailableError):
            print(f"  Failure {i+1} recorded")
    
    print("\nUpdated service status:")
    available_services = registry.get_available_services()
    print(f"  Available services: {', '.join(available_services) or 'None'}")
    
    # Get health report
    print("\nDetailed health report:")
    health = registry.get_health_report()
    print(f"  Total services: {health['summary']['total_services']}")
    print(f"  Available: {health['summary']['available_services']}")
    print(f"  Unavailable: {health['summary']['unavailable_services']}")


def demo_network_check():
    """Demo: Network connectivity check"""
    print("\n" + "="*60)
    print("DEMO 5: Network Connectivity Check")
    print("="*60)
    
    print("\nChecking network connectivity...")
    is_connected = check_network_connectivity(timeout=3.0)
    
    if is_connected:
        print("  ✓ Network is available")
    else:
        print("  ✗ Network is unavailable")
    
    print("\nThis check happens automatically before API calls to fail fast.")


def demo_graceful_degradation():
    """Demo: Graceful degradation concept"""
    print("\n" + "="*60)
    print("DEMO 6: Graceful Degradation")
    print("="*60)
    
    print("\nScenario: Searching with multiple services")
    print("\nBoth services available:")
    print("  → Search BioPortal ✓")
    print("  → Search OLS ✓")
    print("  → Compare results")
    print("  → Return combined results")
    
    print("\nOne service unavailable:")
    print("  → Search BioPortal ✗ (circuit breaker open)")
    print("  → Search OLS ✓")
    print("  → Skip comparison")
    print("  → Return OLS results only")
    print("  → User notification: '⚠️ BioPortal unavailable, using OLS only'")
    
    print("\nBoth services unavailable:")
    print("  → Search BioPortal ✗")
    print("  → Search OLS ✗")
    print("  → Return empty results")
    print("  → User notification: '⚠️ All services unavailable, please try later'")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "ERROR HANDLING DEMO" + " "*24 + "║")
    print("║" + " "*11 + "Advanced Retry & Fault Tolerance" + " "*14 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        demo_retry_mechanism()
        demo_circuit_breaker()
        demo_error_messages()
        demo_health_monitoring()
        demo_network_check()
        demo_graceful_degradation()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60)
        print("\nFor more information, see ERROR_HANDLING.md")
        print()
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
