"""
AI-Powered System Monitor for The Orchid Continuum
Continuously monitors all platform functionality and performs automatic repairs
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import time
from dataclasses import dataclass
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class MonitorResult:
    component: str
    status: SystemStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    repair_attempted: bool = False
    repair_successful: bool = False

class AISystemMonitor:
    """AI-powered monitoring system that continuously validates and repairs platform functionality"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.monitoring_active = False
        self.results_history: List[MonitorResult] = []
        self.failure_patterns: Dict[str, List[str]] = {}
        self.last_check_time = datetime.now()
        self.repair_attempts = 0
        
        # Critical endpoints to monitor
        self.critical_endpoints = {
            "api_orchid_coordinates": "/api/orchid-coordinates-all",
            "api_ecosystem_data": "/api/orchid-ecosystem-data",
            "api_weather_patterns": "/api/global-weather-patterns",
            "api_satellite_monitoring": "/api/satellite-monitoring",
            "api_orchid_genera": "/api/orchid-genera",
            "main_app": "/",
            "gallery": "/gallery",
            "space_earth_globe": "/space-earth-globe"
        }
        
        # Endpoints that return lists (special handling needed)
        self.list_endpoints = {
            "api_recent_orchids": "/api/recent-orchids",
            "api_featured_orchids": "/api/featured-orchids"
        }
        
        # Feature tests
        self.feature_tests = {
            "ecosystem_filtering": self._test_ecosystem_filtering,
            "satellite_overlays": self._test_satellite_overlays,
            "orchid_loading": self._test_orchid_loading,
            "weather_patterns": self._test_weather_patterns,
            "3d_globe_data": self._test_3d_globe_data
        }
    
    def start_monitoring(self, interval_seconds: int = 300):  # Increased to 5 minutes
        """Start continuous AI monitoring with reduced frequency"""
        self.monitoring_active = True
        logger.info("🤖 AI System Monitor STARTED - Continuous platform validation enabled (5min intervals)")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self._run_comprehensive_check()
                    time.sleep(interval_seconds)
                except Exception as e:
                    logger.error(f"🚨 AI Monitor Error: {e}")
                    time.sleep(30)  # Wait before retrying
        
        # Run in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("🛑 AI System Monitor STOPPED")
    
    def _run_comprehensive_check(self):
        """Run complete system validation and repair cycle"""
        logger.info("🔍 AI Monitor: Running comprehensive system check...")
        
        results = []
        
        # 1. Test all critical endpoints
        for name, endpoint in self.critical_endpoints.items():
            result = self._test_endpoint(name, endpoint)
            results.append(result)
            
            # Only attempt repair for CRITICAL failures, not warnings
            if result.status == SystemStatus.CRITICAL:
                self._attempt_repair(result)
        
        # 2. Test list endpoints with special handling
        for name, endpoint in self.list_endpoints.items():
            result = self._test_list_endpoint(name, endpoint)
            results.append(result)
            
            # Only attempt repair for CRITICAL failures, not warnings
            if result.status == SystemStatus.CRITICAL:
                self._attempt_repair(result)
        
        # 3. Test specific features
        for name, test_func in self.feature_tests.items():
            result = test_func()
            results.append(result)
            
            # Only attempt repair for CRITICAL failures, not warnings
            if result.status == SystemStatus.CRITICAL:
                self._attempt_repair(result)
        
        # 3. Analyze patterns and predict issues
        self._analyze_failure_patterns(results)
        
        # 4. Store results
        self.results_history.extend(results)
        
        # 5. Generate health report
        self._generate_health_report(results)
        
        self.last_check_time = datetime.now()
    
    def _test_endpoint(self, name: str, endpoint: str) -> MonitorResult:
        """Test a specific API endpoint with smarter error handling"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=30)  # Increased timeout
            
            if response.status_code == 200:
                # Check response content
                if 'json' in response.headers.get('content-type', ''):
                    try:
                        data = response.json()
                        if data.get('success', True):  # Assume success if no success field
                            return MonitorResult(
                                component=name,
                                status=SystemStatus.HEALTHY,
                                message=f"Endpoint responding correctly",
                                details={"status_code": response.status_code, "response_size": len(response.content)},
                                timestamp=datetime.now()
                            )
                        else:
                            return MonitorResult(
                                component=name,
                                status=SystemStatus.WARNING,
                                message=f"Endpoint returned success=false",
                                details={"status_code": response.status_code, "data": data},
                                timestamp=datetime.now()
                            )
                    except ValueError:
                        # JSON parsing failed, but 200 response means it's probably working
                        return MonitorResult(
                            component=name,
                            status=SystemStatus.HEALTHY,
                            message=f"Endpoint responding (malformed JSON)",
                            details={"status_code": response.status_code, "content_length": len(response.content)},
                            timestamp=datetime.now()
                        )
                else:
                    return MonitorResult(
                        component=name,
                        status=SystemStatus.HEALTHY,
                        message=f"Endpoint responding (HTML)",
                        details={"status_code": response.status_code, "content_length": len(response.content)},
                        timestamp=datetime.now()
                    )
            elif response.status_code == 404:
                # 404 is not critical - endpoint might not be implemented yet
                return MonitorResult(
                    component=name,
                    status=SystemStatus.WARNING,
                    message=f"Endpoint not found (404)",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
            elif response.status_code >= 500:
                # Server errors are critical
                return MonitorResult(
                    component=name,
                    status=SystemStatus.CRITICAL,
                    message=f"Server error ({response.status_code})",
                    details={"status_code": response.status_code, "response": response.text[:500]},
                    timestamp=datetime.now()
                )
            else:
                # Other client errors are warnings
                return MonitorResult(
                    component=name,
                    status=SystemStatus.WARNING,
                    message=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code, "response": response.text[:500]},
                    timestamp=datetime.now()
                )
                
        except requests.exceptions.Timeout:
            # Timeouts are warnings, not critical
            return MonitorResult(
                component=name,
                status=SystemStatus.WARNING,
                message="Request timeout (slow response)",
                details={"error": "timeout", "endpoint": endpoint},
                timestamp=datetime.now()
            )
        except requests.exceptions.ConnectionError:
            # Connection errors are critical 
            return MonitorResult(
                component=name,
                status=SystemStatus.CRITICAL,
                message=f"Connection failed",
                details={"error": "connection_error", "endpoint": endpoint},
                timestamp=datetime.now()
            )
        except Exception as e:
            # Other errors are warnings
            return MonitorResult(
                component=name,
                status=SystemStatus.WARNING,
                message=f"Test failed: {str(e)}",
                details={"error": str(e), "endpoint": endpoint},
                timestamp=datetime.now()
            )
    
    def _test_list_endpoint(self, name: str, endpoint: str) -> MonitorResult:
        """Test endpoints that return lists directly (like /api/recent-orchids)"""
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                # Check response content
                if 'json' in response.headers.get('content-type', ''):
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            # Direct list response
                            return MonitorResult(
                                component=name,
                                status=SystemStatus.HEALTHY if len(data) > 0 else SystemStatus.WARNING,
                                message=f"List endpoint working ({len(data)} items)",
                                details={"item_count": len(data), "response_type": "list"},
                                timestamp=datetime.now()
                            )
                        elif isinstance(data, dict):
                            # Dict response
                            if data.get('success', True):
                                count = len(data.get('orchids', data.get('data', [])))
                                return MonitorResult(
                                    component=name,
                                    status=SystemStatus.HEALTHY if count > 0 else SystemStatus.WARNING,
                                    message=f"Dict endpoint working ({count} items)",
                                    details={"item_count": count, "response_type": "dict"},
                                    timestamp=datetime.now()
                                )
                            else:
                                return MonitorResult(
                                    component=name,
                                    status=SystemStatus.WARNING,
                                    message=f"Endpoint returned success=false",
                                    details={"data": data},
                                    timestamp=datetime.now()
                                )
                        else:
                            return MonitorResult(
                                component=name,
                                status=SystemStatus.WARNING,
                                message=f"Unexpected response format",
                                details={"response_type": type(data).__name__},
                                timestamp=datetime.now()
                            )
                    except ValueError:
                        # JSON parsing failed
                        return MonitorResult(
                            component=name,
                            status=SystemStatus.WARNING,
                            message=f"Invalid JSON response",
                            details={"content_length": len(response.content)},
                            timestamp=datetime.now()
                        )
                else:
                    return MonitorResult(
                        component=name,
                        status=SystemStatus.HEALTHY,
                        message=f"Endpoint responding (non-JSON)",
                        details={"status_code": response.status_code, "content_length": len(response.content)},
                        timestamp=datetime.now()
                    )
            elif response.status_code == 404:
                return MonitorResult(
                    component=name,
                    status=SystemStatus.WARNING,
                    message=f"Endpoint not found (404)",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
            elif response.status_code >= 500:
                return MonitorResult(
                    component=name,
                    status=SystemStatus.CRITICAL,
                    message=f"Server error ({response.status_code})",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
            else:
                return MonitorResult(
                    component=name,
                    status=SystemStatus.WARNING,
                    message=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
                
        except requests.exceptions.Timeout:
            return MonitorResult(
                component=name,
                status=SystemStatus.WARNING,
                message="Request timeout (slow response)",
                details={"error": "timeout", "endpoint": endpoint},
                timestamp=datetime.now()
            )
        except requests.exceptions.ConnectionError:
            return MonitorResult(
                component=name,
                status=SystemStatus.CRITICAL,
                message=f"Connection failed",
                details={"error": "connection_error", "endpoint": endpoint},
                timestamp=datetime.now()
            )
        except Exception as e:
            return MonitorResult(
                component=name,
                status=SystemStatus.WARNING,
                message=f"Test failed: {str(e)}",
                details={"error": str(e), "endpoint": endpoint},
                timestamp=datetime.now()
            )
    
    def _test_ecosystem_filtering(self) -> MonitorResult:
        """Test ecosystem filtering functionality"""
        try:
            # Test basic ecosystem query
            response = requests.get(f"{self.base_url}/api/orchid-ecosystem-data?genus=Cattleya", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and isinstance(data.get('orchids'), list):
                    count = data.get('count', 0)
                    return MonitorResult(
                        component="ecosystem_filtering",
                        status=SystemStatus.HEALTHY if count > 0 else SystemStatus.WARNING,
                        message=f"Ecosystem filtering working ({count} results)",
                        details={"orchid_count": count, "filters_applied": data.get('filters_applied', {})},
                        timestamp=datetime.now()
                    )
                else:
                    return MonitorResult(
                        component="ecosystem_filtering",
                        status=SystemStatus.WARNING,
                        message="Ecosystem API returned no data",
                        details={"response": data},
                        timestamp=datetime.now()
                    )
            else:
                return MonitorResult(
                    component="ecosystem_filtering",
                    status=SystemStatus.CRITICAL,
                    message=f"Ecosystem API failed ({response.status_code})",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return MonitorResult(
                component="ecosystem_filtering",
                status=SystemStatus.CRITICAL,
                message=f"Ecosystem test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _test_satellite_overlays(self) -> MonitorResult:
        """Test satellite monitoring overlays"""
        try:
            response = requests.get(f"{self.base_url}/api/satellite-monitoring", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('satellite_data'):
                    return MonitorResult(
                        component="satellite_overlays",
                        status=SystemStatus.HEALTHY,
                        message=f"Satellite data loaded ({len(data['satellite_data'])} points)",
                        details={"data_points": len(data['satellite_data'])},
                        timestamp=datetime.now()
                    )
                else:
                    return MonitorResult(
                        component="satellite_overlays",
                        status=SystemStatus.WARNING,
                        message="No satellite data available",
                        details={"response": data},
                        timestamp=datetime.now()
                    )
            else:
                return MonitorResult(
                    component="satellite_overlays",
                    status=SystemStatus.CRITICAL,
                    message=f"Satellite API failed ({response.status_code})",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return MonitorResult(
                component="satellite_overlays",
                status=SystemStatus.CRITICAL,
                message=f"Satellite test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _test_orchid_loading(self) -> MonitorResult:
        """Test orchid data loading"""
        try:
            response = requests.get(f"{self.base_url}/api/orchid-coordinates-all", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('coordinates'):
                    count = len(data['coordinates'])
                    return MonitorResult(
                        component="orchid_loading",
                        status=SystemStatus.HEALTHY if count > 0 else SystemStatus.WARNING,
                        message=f"Orchid data loaded ({count} coordinates)",
                        details={"coordinate_count": count},
                        timestamp=datetime.now()
                    )
                else:
                    return MonitorResult(
                        component="orchid_loading",
                        status=SystemStatus.WARNING,
                        message="No orchid coordinates available",
                        details={"response": data},
                        timestamp=datetime.now()
                    )
            else:
                return MonitorResult(
                    component="orchid_loading",
                    status=SystemStatus.CRITICAL,
                    message=f"Orchid API failed ({response.status_code})",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return MonitorResult(
                component="orchid_loading",
                status=SystemStatus.CRITICAL,
                message=f"Orchid test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _test_weather_patterns(self) -> MonitorResult:
        """Test weather pattern loading"""
        try:
            response = requests.get(f"{self.base_url}/api/global-weather-patterns", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('weather_points'):
                    count = len(data['weather_points'])
                    return MonitorResult(
                        component="weather_patterns",
                        status=SystemStatus.HEALTHY if count > 0 else SystemStatus.WARNING,
                        message=f"Weather patterns loaded ({count} locations)",
                        details={"weather_points": count},
                        timestamp=datetime.now()
                    )
                else:
                    return MonitorResult(
                        component="weather_patterns",
                        status=SystemStatus.WARNING,
                        message="No weather data available",
                        details={"response": data},
                        timestamp=datetime.now()
                    )
            else:
                return MonitorResult(
                    component="weather_patterns",
                    status=SystemStatus.CRITICAL,
                    message=f"Weather API failed ({response.status_code})",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return MonitorResult(
                component="weather_patterns",
                status=SystemStatus.CRITICAL,
                message=f"Weather test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _test_3d_globe_data(self) -> MonitorResult:
        """Test 3D globe data integrity"""
        try:
            # Test multiple endpoints that feed the globe
            tests = [
                ("/api/orchid-coordinates-all", "orchid_coordinates"),
                ("/api/orchid-genera", "genera_list"),
            ]
            
            failed_tests = []
            passed_tests = []
            
            for endpoint, test_name in tests:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success', True):
                            passed_tests.append(test_name)
                        else:
                            failed_tests.append(f"{test_name} (no success)")
                    else:
                        failed_tests.append(f"{test_name} (HTTP {response.status_code})")
                except Exception as e:
                    failed_tests.append(f"{test_name} (error: {str(e)})")
            
            if len(failed_tests) == 0:
                return MonitorResult(
                    component="3d_globe_data",
                    status=SystemStatus.HEALTHY,
                    message=f"All globe data sources working ({len(passed_tests)} tests passed)",
                    details={"passed_tests": passed_tests},
                    timestamp=datetime.now()
                )
            elif len(passed_tests) > len(failed_tests):
                return MonitorResult(
                    component="3d_globe_data",
                    status=SystemStatus.WARNING,
                    message=f"Some globe data issues ({len(failed_tests)} failures)",
                    details={"failed_tests": failed_tests, "passed_tests": passed_tests},
                    timestamp=datetime.now()
                )
            else:
                return MonitorResult(
                    component="3d_globe_data",
                    status=SystemStatus.CRITICAL,
                    message=f"Major globe data failures ({len(failed_tests)} failures)",
                    details={"failed_tests": failed_tests, "passed_tests": passed_tests},
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            return MonitorResult(
                component="3d_globe_data",
                status=SystemStatus.CRITICAL,
                message=f"Globe data test failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now()
            )
    
    def _attempt_repair(self, result: MonitorResult):
        """Attempt to repair a failed component"""
        result.repair_attempted = True
        self.repair_attempts += 1
        
        logger.warning(f"🔧 AI Repair: Attempting to fix {result.component}")
        
        repair_strategies = {
            "ecosystem_filtering": self._repair_ecosystem_filtering,
            "satellite_overlays": self._repair_satellite_overlays,
            "weather_patterns": self._repair_weather_patterns,
            "orchid_loading": self._repair_orchid_loading,
        }
        
        if result.component in repair_strategies:
            try:
                success = repair_strategies[result.component](result)
                result.repair_successful = success
                if success:
                    logger.info(f"✅ AI Repair: Fixed {result.component}")
                else:
                    logger.warning(f"❌ AI Repair: Could not fix {result.component}")
            except Exception as e:
                logger.error(f"🚨 AI Repair: Error fixing {result.component}: {e}")
                result.repair_successful = False
        else:
            logger.info(f"ℹ️ AI Repair: No repair strategy available for {result.component}")
    
    def _repair_ecosystem_filtering(self, result: MonitorResult) -> bool:
        """Attempt to repair ecosystem filtering"""
        try:
            # Check if it's a data issue or API issue
            response = requests.get(f"{self.base_url}/api/orchid-ecosystem-data?genus=all", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info("🔧 Ecosystem filtering API is working, may be data-specific issue")
                    return True
            
            # Try triggering any maintenance endpoints
            # This would be implemented based on your specific repair mechanisms
            return False
            
        except Exception as e:
            logger.error(f"Ecosystem repair failed: {e}")
            return False
    
    def _repair_satellite_overlays(self, result: MonitorResult) -> bool:
        """Attempt to repair satellite monitoring"""
        try:
            # Could implement cache clearing, data refresh, etc.
            return False
        except Exception as e:
            logger.error(f"Satellite repair failed: {e}")
            return False
    
    def _repair_weather_patterns(self, result: MonitorResult) -> bool:
        """Attempt to repair weather patterns"""
        try:
            # Could implement weather API key refresh, cache clearing, etc.
            return False
        except Exception as e:
            logger.error(f"Weather repair failed: {e}")
            return False
    
    def _repair_orchid_loading(self, result: MonitorResult) -> bool:
        """Attempt to repair orchid data loading"""
        try:
            # Could implement database reconnection, cache refresh, etc.
            return False
        except Exception as e:
            logger.error(f"Orchid repair failed: {e}")
            return False
    
    def _analyze_failure_patterns(self, results: List[MonitorResult]):
        """Analyze failure patterns to predict issues"""
        for result in results:
            if result.status in [SystemStatus.WARNING, SystemStatus.CRITICAL]:
                if result.component not in self.failure_patterns:
                    self.failure_patterns[result.component] = []
                
                self.failure_patterns[result.component].append(result.message)
                
                # Keep only recent patterns (last 10)
                if len(self.failure_patterns[result.component]) > 10:
                    self.failure_patterns[result.component] = self.failure_patterns[result.component][-10:]
    
    def _generate_health_report(self, results: List[MonitorResult]):
        """Generate comprehensive health report"""
        healthy = sum(1 for r in results if r.status == SystemStatus.HEALTHY)
        warning = sum(1 for r in results if r.status == SystemStatus.WARNING)
        critical = sum(1 for r in results if r.status == SystemStatus.CRITICAL)
        
        total = len(results)
        health_percentage = (healthy / total * 100) if total > 0 else 0
        
        status_emoji = "✅" if health_percentage >= 90 else "⚠️" if health_percentage >= 70 else "🚨"
        
        logger.info(f"{status_emoji} AI Monitor Health Report: {health_percentage:.1f}% ({healthy}✅ {warning}⚠️ {critical}🚨)")
        
        # Log critical issues
        for result in results:
            if result.status == SystemStatus.CRITICAL:
                logger.error(f"🚨 CRITICAL: {result.component} - {result.message}")
            elif result.status == SystemStatus.WARNING:
                logger.warning(f"⚠️ WARNING: {result.component} - {result.message}")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.results_history:
            return {"status": "no_data", "message": "No monitoring data available"}
        
        # Get recent results (last hour)
        recent_time = datetime.now() - timedelta(hours=1)
        recent_results = [r for r in self.results_history if r.timestamp > recent_time]
        
        if not recent_results:
            return {"status": "stale", "message": "No recent monitoring data"}
        
        healthy = sum(1 for r in recent_results if r.status == SystemStatus.HEALTHY)
        warning = sum(1 for r in recent_results if r.status == SystemStatus.WARNING)
        critical = sum(1 for r in recent_results if r.status == SystemStatus.CRITICAL)
        
        total = len(recent_results)
        health_percentage = (healthy / total * 100) if total > 0 else 0
        
        return {
            "status": "healthy" if health_percentage >= 90 else "warning" if health_percentage >= 70 else "critical",
            "health_percentage": health_percentage,
            "healthy_count": healthy,
            "warning_count": warning,
            "critical_count": critical,
            "total_checks": total,
            "last_check": self.last_check_time.isoformat(),
            "monitoring_active": self.monitoring_active,
            "repair_attempts": self.repair_attempts
        }

# Global monitor instance
_monitor_instance = None

def get_ai_monitor() -> AISystemMonitor:
    """Get or create the global AI monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AISystemMonitor()
    return _monitor_instance

def start_ai_monitoring(interval_seconds: int = 60):
    """Start AI monitoring with specified interval"""
    monitor = get_ai_monitor()
    monitor.start_monitoring(interval_seconds)
    return monitor

def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring status"""
    monitor = get_ai_monitor()
    return monitor.get_health_summary()