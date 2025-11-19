"""
Health monitoring system for external services.
Tracks service availability and provides graceful degradation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from utils.error_handling import ServiceHealthMonitor, CircuitBreaker

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for tracking external service health"""
    
    def __init__(self):
        self.monitor = ServiceHealthMonitor()
        self._services = {}
    
    def register(self, name: str, circuit_breaker: Optional[CircuitBreaker] = None):
        """Register a service for health monitoring"""
        self._services[name] = {
            'circuit_breaker': circuit_breaker,
            'enabled': True,
            'last_success': None,
            'last_failure': None,
            'consecutive_failures': 0
        }
        
        if circuit_breaker:
            self.monitor.register_service(name, circuit_breaker)
    
    def mark_success(self, name: str):
        """Mark a successful operation for a service"""
        if name in self._services:
            self._services[name]['last_success'] = datetime.now()
            self._services[name]['consecutive_failures'] = 0
            logger.debug(f"Service {name} marked as successful")
    
    def mark_failure(self, name: str):
        """Mark a failed operation for a service"""
        if name in self._services:
            self._services[name]['last_failure'] = datetime.now()
            self._services[name]['consecutive_failures'] += 1
            logger.warning(f"Service {name} marked as failed (consecutive: {self._services[name]['consecutive_failures']})")
    
    def is_available(self, name: str) -> bool:
        """Check if a service is available"""
        if name not in self._services:
            return False
        
        service = self._services[name]
        
        # Check if manually disabled
        if not service['enabled']:
            return False
        
        # Check circuit breaker if available
        if service['circuit_breaker']:
            from utils.error_handling import CircuitBreakerState
            return service['circuit_breaker'].state == CircuitBreakerState.CLOSED
        
        return True
    
    def get_available_services(self) -> List[str]:
        """Get list of currently available services"""
        return [name for name in self._services if self.is_available(name)]
    
    def get_health_report(self) -> Dict:
        """Get comprehensive health report for all services"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for name, service in self._services.items():
            status = {
                'available': self.is_available(name),
                'enabled': service['enabled'],
                'last_success': service['last_success'].isoformat() if service['last_success'] else None,
                'last_failure': service['last_failure'].isoformat() if service['last_failure'] else None,
                'consecutive_failures': service['consecutive_failures']
            }
            
            if service['circuit_breaker']:
                status['circuit_breaker'] = service['circuit_breaker'].get_state()
            
            report['services'][name] = status
        
        # Add summary
        available = self.get_available_services()
        report['summary'] = {
            'total_services': len(self._services),
            'available_services': len(available),
            'unavailable_services': len(self._services) - len(available),
            'available_service_names': available
        }
        
        return report
    
    def enable_service(self, name: str):
        """Manually enable a service"""
        if name in self._services:
            self._services[name]['enabled'] = True
            logger.info(f"Service {name} manually enabled")
    
    def disable_service(self, name: str):
        """Manually disable a service"""
        if name in self._services:
            self._services[name]['enabled'] = False
            logger.info(f"Service {name} manually disabled")
    
    def reset_service(self, name: str):
        """Reset a service's circuit breaker and status"""
        if name in self._services:
            service = self._services[name]
            if service['circuit_breaker']:
                service['circuit_breaker'].reset()
            service['consecutive_failures'] = 0
            logger.info(f"Service {name} reset")


# Global service registry instance
_global_registry = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ServiceRegistry()
    return _global_registry
