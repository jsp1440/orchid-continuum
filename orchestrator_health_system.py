#!/usr/bin/env python3
"""
🏥 Orchestrator Health System - Production Readiness Validation
Critical dependency validation, health checks, and strict mode enforcement
Ensures all dependencies and APIs are available before allowing operations

Created for Orchid Continuum - Production Readiness Enhancement
Addresses: Mock fallbacks masking failures, missing dependency checks, silent degradation
"""

import os
import sys
import json
import time
import uuid
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import tempfile

# Configure logging
logger = logging.getLogger(__name__)

class CriticalityLevel(Enum):
    """Dependency criticality levels"""
    CRITICAL = "critical"     # System cannot function without this
    IMPORTANT = "important"   # Major features unavailable without this
    OPTIONAL = "optional"     # Nice-to-have features only

class HealthStatus(Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class DependencyCheck:
    """Individual dependency validation"""
    name: str
    category: str  # 'library', 'api', 'service', 'file', 'environment'
    criticality: CriticalityLevel
    check_function: Optional[Callable] = None
    status: HealthStatus = HealthStatus.UNKNOWN
    error_message: Optional[str] = None
    last_checked: Optional[datetime] = None
    check_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""
    overall_status: HealthStatus
    strict_mode_enabled: bool
    critical_failures: List[str]
    important_failures: List[str]
    optional_failures: List[str]
    healthy_dependencies: List[str]
    total_checks: int
    failed_checks: int
    check_timestamp: datetime
    startup_allowed: bool
    detailed_results: Dict[str, DependencyCheck] = field(default_factory=dict)

class ProductionHealthValidator:
    """
    Production-ready health validation system
    Enforces strict dependency checking and fails fast on critical issues
    """
    
    def __init__(self, strict_mode: bool = True):
        """Initialize health validator with strict mode (default ON)"""
        self.strict_mode = strict_mode
        self.dependencies: Dict[str, DependencyCheck] = {}
        self.health_history: List[SystemHealthReport] = []
        self.last_full_check: Optional[datetime] = None
        
        # Override strict mode with environment variable if set
        env_strict = os.environ.get('ORCHESTRATOR_STRICT_MODE', 'true').lower()
        if env_strict in ['false', '0', 'no', 'off']:
            self.strict_mode = False
            logger.warning("⚠️ STRICT MODE DISABLED - System may continue with missing dependencies")
        
        # Register all required dependencies
        self._register_dependencies()
        
        logger.info(f"🏥 Health Validator initialized - Strict Mode: {'ON' if self.strict_mode else 'OFF'}")
    
    def _register_dependencies(self):
        """Register all system dependencies with their validation functions"""
        
        # Critical Python Libraries
        self._register_dependency(
            "flask", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("flask", "Flask")
        )
        self._register_dependency(
            "sqlalchemy", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("sqlalchemy", "create_engine")
        )
        
        # Google Libraries (Critical for Google integrations)
        self._register_dependency(
            "google_api_client", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("googleapiclient.discovery", "build")
        )
        self._register_dependency(
            "google_auth", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("google.oauth2.service_account", "Credentials")
        )
        self._register_dependency(
            "gspread", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("gspread", "Client")
        )
        
        # OpenAI Library (Critical for AI features)
        self._register_dependency(
            "openai", "library", CriticalityLevel.CRITICAL,
            lambda: self._check_python_import("openai", "OpenAI")
        )
        
        # SendGrid Library (Important for notifications)
        self._register_dependency(
            "sendgrid", "library", CriticalityLevel.IMPORTANT,
            lambda: self._check_python_import("sendgrid", "SendGridAPIClient")
        )
        
        # Report Generation Libraries
        self._register_dependency(
            "reportlab", "library", CriticalityLevel.IMPORTANT,
            lambda: self._check_python_import("reportlab.pdfgen", "canvas")
        )
        self._register_dependency(
            "pandas", "library", CriticalityLevel.IMPORTANT,
            lambda: self._check_python_import("pandas", "DataFrame")
        )
        
        # Environment Variables (Critical)
        self._register_dependency(
            "database_url", "environment", CriticalityLevel.CRITICAL,
            lambda: self._check_environment_variable("DATABASE_URL")
        )
        self._register_dependency(
            "openai_api_key", "environment", CriticalityLevel.CRITICAL,
            lambda: self._check_environment_variable("OPENAI_API_KEY")
        )
        self._register_dependency(
            "google_credentials", "environment", CriticalityLevel.CRITICAL,
            lambda: self._check_google_credentials()
        )
        
        # Optional Environment Variables
        self._register_dependency(
            "sendgrid_api_key", "environment", CriticalityLevel.IMPORTANT,
            lambda: self._check_environment_variable("SENDGRID_API_KEY")
        )
        
        # API Connectivity (Critical)
        self._register_dependency(
            "google_drive_api", "api", CriticalityLevel.CRITICAL,
            lambda: self._check_google_drive_connectivity()
        )
        self._register_dependency(
            "google_sheets_api", "api", CriticalityLevel.CRITICAL,
            lambda: self._check_google_sheets_connectivity()
        )
        self._register_dependency(
            "openai_api", "api", CriticalityLevel.CRITICAL,
            lambda: self._check_openai_connectivity()
        )
        
        # Database Connectivity (Critical)
        self._register_dependency(
            "database_connection", "service", CriticalityLevel.CRITICAL,
            lambda: self._check_database_connectivity()
        )
        
        # File System Access (Important)
        self._register_dependency(
            "temp_directory", "file", CriticalityLevel.IMPORTANT,
            lambda: self._check_temp_directory_access()
        )
        self._register_dependency(
            "static_directory", "file", CriticalityLevel.IMPORTANT,
            lambda: self._check_static_directory_access()
        )
    
    def _register_dependency(self, name: str, category: str, criticality: CriticalityLevel, 
                           check_function: Callable):
        """Register a dependency with its validation function"""
        self.dependencies[name] = DependencyCheck(
            name=name,
            category=category,
            criticality=criticality,
            check_function=check_function
        )
    
    def _check_python_import(self, module_name: str, attribute: str = None) -> Tuple[bool, Optional[str]]:
        """Check if a Python module/attribute can be imported"""
        try:
            module = __import__(module_name, fromlist=[attribute] if attribute else [])
            if attribute and not hasattr(module, attribute):
                return False, f"Module '{module_name}' missing attribute '{attribute}'"
            return True, None
        except ImportError as e:
            return False, f"Import error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def _check_environment_variable(self, var_name: str) -> Tuple[bool, Optional[str]]:
        """Check if environment variable exists and is non-empty"""
        value = os.environ.get(var_name)
        if not value:
            return False, f"Environment variable '{var_name}' not set or empty"
        return True, None
    
    def _check_google_credentials(self) -> Tuple[bool, Optional[str]]:
        """Check Google Cloud credentials availability"""
        # Check for service account file
        service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
        if service_account_file and os.path.exists(service_account_file):
            return True, None
        
        # Check for service account JSON
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        if service_account_json:
            try:
                json.loads(service_account_json)
                return True, None
            except json.JSONDecodeError:
                return False, "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON"
        
        return False, "No valid Google Cloud credentials found"
    
    def _check_google_drive_connectivity(self) -> Tuple[bool, Optional[str]]:
        """Check Google Drive API connectivity"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            
            # Get credentials
            success, error = self._check_google_credentials()
            if not success:
                return False, f"Credentials error: {error}"
            
            # Try to create service
            credentials = self._get_google_credentials()
            if not credentials:
                return False, "Could not initialize Google credentials"
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Test API call - list drives (minimal permissions needed)
            result = service.about().get(fields="user").execute()
            if 'user' in result:
                return True, None
            else:
                return False, "API call succeeded but unexpected response"
                
        except Exception as e:
            return False, f"Google Drive API error: {e}"
    
    def _check_google_sheets_connectivity(self) -> Tuple[bool, Optional[str]]:
        """Check Google Sheets API connectivity"""
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Get credentials
            credentials = self._get_google_credentials()
            if not credentials:
                return False, "Could not initialize Google credentials"
            
            # Test gspread connection
            gc = gspread.authorize(credentials)
            
            # Try to get user info (minimal API call)
            # This will fail if sheets API is not enabled or accessible
            service = gc.auth.service
            result = service.about().get(fields="user").execute()
            
            if 'user' in result:
                return True, None
            else:
                return False, "API call succeeded but unexpected response"
                
        except Exception as e:
            return False, f"Google Sheets API error: {e}"
    
    def _check_openai_connectivity(self) -> Tuple[bool, Optional[str]]:
        """Check OpenAI API connectivity"""
        try:
            from openai import OpenAI
            
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return False, "OPENAI_API_KEY not set"
            
            client = OpenAI(api_key=api_key, timeout=10)
            
            # Test API call - list models (minimal usage)
            models = client.models.list()
            if models and hasattr(models, 'data') and len(models.data) > 0:
                return True, None
            else:
                return False, "API accessible but no models available"
                
        except Exception as e:
            return False, f"OpenAI API error: {e}"
    
    def _check_database_connectivity(self) -> Tuple[bool, Optional[str]]:
        """Check database connectivity"""
        try:
            from sqlalchemy import create_engine, text
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                return False, "DATABASE_URL not set"
            
            engine = create_engine(db_url, pool_pre_ping=True)
            
            # Test connection with simple query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    return True, None
                else:
                    return False, "Query succeeded but unexpected result"
                    
        except Exception as e:
            return False, f"Database connection error: {e}"
    
    def _check_temp_directory_access(self) -> Tuple[bool, Optional[str]]:
        """Check temporary directory write access"""
        try:
            temp_dir = tempfile.gettempdir()
            test_file = os.path.join(temp_dir, f"health_check_{uuid.uuid4().hex}.tmp")
            
            # Test write access
            with open(test_file, 'w') as f:
                f.write("health check")
            
            # Test read access
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Cleanup
            os.unlink(test_file)
            
            if content == "health check":
                return True, None
            else:
                return False, "File write/read test failed"
                
        except Exception as e:
            return False, f"Temp directory access error: {e}"
    
    def _check_static_directory_access(self) -> Tuple[bool, Optional[str]]:
        """Check static directory access"""
        try:
            static_dir = os.path.join(os.getcwd(), 'static')
            if not os.path.exists(static_dir):
                return False, "Static directory does not exist"
            
            if not os.access(static_dir, os.R_OK):
                return False, "Static directory not readable"
            
            return True, None
            
        except Exception as e:
            return False, f"Static directory access error: {e}"
    
    def _get_google_credentials(self):
        """Get Google credentials from environment"""
        try:
            from google.oauth2.service_account import Credentials
            
            # Try service account file first
            service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
            if service_account_file and os.path.exists(service_account_file):
                return Credentials.from_service_account_file(
                    service_account_file,
                    scopes=[
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
            
            # Try service account JSON
            service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                credentials_info = json.loads(service_account_json)
                return Credentials.from_service_account_info(
                    credentials_info,
                    scopes=[
                        'https://www.googleapis.com/auth/drive',
                        'https://www.googleapis.com/auth/spreadsheets'
                    ]
                )
            
            return None
            
        except Exception:
            return None
    
    def run_full_health_check(self, timeout_per_check: float = 30.0) -> SystemHealthReport:
        """Run comprehensive health check on all dependencies"""
        logger.info("🔍 Starting comprehensive health check...")
        start_time = datetime.now()
        
        critical_failures = []
        important_failures = []
        optional_failures = []
        healthy_dependencies = []
        
        # Run all dependency checks
        for name, dependency in self.dependencies.items():
            logger.debug(f"Checking dependency: {name}")
            check_start = time.time()
            
            try:
                if dependency.check_function:
                    success, error_msg = dependency.check_function()
                    dependency.status = HealthStatus.HEALTHY if success else HealthStatus.CRITICAL
                    dependency.error_message = error_msg
                else:
                    dependency.status = HealthStatus.UNKNOWN
                    dependency.error_message = "No check function defined"
                    
            except Exception as e:
                dependency.status = HealthStatus.CRITICAL
                dependency.error_message = f"Check function error: {e}"
                logger.error(f"Health check error for {name}: {e}")
            
            dependency.last_checked = datetime.now()
            dependency.check_duration = time.time() - check_start
            
            # Categorize results
            if dependency.status == HealthStatus.HEALTHY:
                healthy_dependencies.append(name)
            else:
                failure_msg = f"{name}: {dependency.error_message}"
                if dependency.criticality == CriticalityLevel.CRITICAL:
                    critical_failures.append(failure_msg)
                elif dependency.criticality == CriticalityLevel.IMPORTANT:
                    important_failures.append(failure_msg)
                else:
                    optional_failures.append(failure_msg)
        
        # Determine overall system status
        if critical_failures:
            overall_status = HealthStatus.CRITICAL
        elif important_failures:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Determine if startup should be allowed
        startup_allowed = True
        if self.strict_mode and critical_failures:
            startup_allowed = False
        
        # Create health report
        report = SystemHealthReport(
            overall_status=overall_status,
            strict_mode_enabled=self.strict_mode,
            critical_failures=critical_failures,
            important_failures=important_failures,
            optional_failures=optional_failures,
            healthy_dependencies=healthy_dependencies,
            total_checks=len(self.dependencies),
            failed_checks=len(critical_failures) + len(important_failures) + len(optional_failures),
            check_timestamp=start_time,
            startup_allowed=startup_allowed,
            detailed_results=self.dependencies.copy()
        )
        
        self.health_history.append(report)
        self.last_full_check = start_time
        
        # Log results
        self._log_health_report(report)
        
        return report
    
    def _log_health_report(self, report: SystemHealthReport):
        """Log health check results"""
        logger.info(f"🏥 Health Check Complete - Status: {report.overall_status.value.upper()}")
        logger.info(f"📊 Results: {len(report.healthy_dependencies)} healthy, {report.failed_checks} failed")
        
        if report.critical_failures:
            logger.error(f"❌ CRITICAL FAILURES ({len(report.critical_failures)}):")
            for failure in report.critical_failures:
                logger.error(f"  - {failure}")
        
        if report.important_failures:
            logger.warning(f"⚠️ IMPORTANT FAILURES ({len(report.important_failures)}):")
            for failure in report.important_failures:
                logger.warning(f"  - {failure}")
        
        if report.optional_failures:
            logger.info(f"ℹ️ OPTIONAL FAILURES ({len(report.optional_failures)}):")
            for failure in report.optional_failures:
                logger.info(f"  - {failure}")
        
        if not report.startup_allowed:
            logger.error("🚫 SYSTEM STARTUP BLOCKED - Critical dependencies missing in strict mode")
        elif report.overall_status == HealthStatus.CRITICAL:
            logger.error("🚨 SYSTEM IN CRITICAL STATE - Operations may fail")
        elif report.overall_status == HealthStatus.DEGRADED:
            logger.warning("⚠️ SYSTEM DEGRADED - Some features unavailable")
        else:
            logger.info("✅ ALL SYSTEMS HEALTHY")
    
    def validate_for_operation(self, operation_name: str, required_dependencies: List[str]) -> Tuple[bool, List[str]]:
        """Validate that specific dependencies are available for an operation"""
        if not self.last_full_check:
            logger.warning("No health check performed yet - running preflight check")
            report = self.run_full_health_check()
            if not report.startup_allowed:
                return False, ["System failed startup validation"]
        
        missing_deps = []
        for dep_name in required_dependencies:
            if dep_name not in self.dependencies:
                missing_deps.append(f"Unknown dependency: {dep_name}")
                continue
                
            dep = self.dependencies[dep_name]
            if dep.status != HealthStatus.HEALTHY:
                missing_deps.append(f"{dep_name}: {dep.error_message}")
        
        operation_allowed = True
        if self.strict_mode and missing_deps:
            operation_allowed = False
        
        return operation_allowed, missing_deps
    
    def enforce_startup_validation(self) -> bool:
        """Enforce startup validation - returns True if startup allowed"""
        logger.info("🚀 Enforcing startup validation...")
        
        report = self.run_full_health_check()
        
        if not report.startup_allowed:
            error_msg = (
                "SYSTEM STARTUP BLOCKED - Critical dependencies missing\n"
                f"Failed checks: {report.failed_checks}/{report.total_checks}\n"
                "Critical failures:\n" + 
                "\n".join(f"  - {failure}" for failure in report.critical_failures)
            )
            
            if self.strict_mode:
                logger.error(error_msg)
                logger.error("Set ORCHESTRATOR_STRICT_MODE=false to bypass (NOT RECOMMENDED)")
                return False
            else:
                logger.warning("Startup validation failed but strict mode disabled - continuing")
                logger.warning(error_msg)
        
        return True
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary"""
        if not self.last_full_check:
            return {
                'status': 'unknown',
                'message': 'No health check performed yet',
                'strict_mode': self.strict_mode
            }
        
        latest_report = self.health_history[-1]
        return {
            'status': latest_report.overall_status.value,
            'strict_mode': self.strict_mode,
            'startup_allowed': latest_report.startup_allowed,
            'total_checks': latest_report.total_checks,
            'failed_checks': latest_report.failed_checks,
            'critical_failures': len(latest_report.critical_failures),
            'important_failures': len(latest_report.important_failures),
            'optional_failures': len(latest_report.optional_failures),
            'last_check': latest_report.check_timestamp.isoformat(),
            'detailed_failures': {
                'critical': latest_report.critical_failures,
                'important': latest_report.important_failures,
                'optional': latest_report.optional_failures
            }
        }

# Global health validator instance
_health_validator: Optional[ProductionHealthValidator] = None

def get_health_validator() -> ProductionHealthValidator:
    """Get global health validator instance"""
    global _health_validator
    if _health_validator is None:
        _health_validator = ProductionHealthValidator()
    return _health_validator

def enforce_dependencies(required_deps: List[str]):
    """Decorator to enforce dependencies for specific operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            validator = get_health_validator()
            allowed, errors = validator.validate_for_operation(func.__name__, required_deps)
            
            if not allowed:
                error_msg = f"Operation '{func.__name__}' blocked - missing dependencies: {errors}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Quick validation functions for immediate use
def validate_google_integration() -> bool:
    """Quick validation for Google integrations"""
    validator = get_health_validator()
    allowed, _ = validator.validate_for_operation(
        "google_integration", 
        ["google_api_client", "google_auth", "gspread", "google_credentials", "google_drive_api", "google_sheets_api"]
    )
    return allowed

def validate_openai_integration() -> bool:
    """Quick validation for OpenAI integration"""
    validator = get_health_validator()
    allowed, _ = validator.validate_for_operation(
        "openai_integration", 
        ["openai", "openai_api_key", "openai_api"]
    )
    return allowed

def validate_core_system() -> bool:
    """Quick validation for core system components"""
    validator = get_health_validator()
    allowed, _ = validator.validate_for_operation(
        "core_system", 
        ["flask", "sqlalchemy", "database_url", "database_connection"]
    )
    return allowed

if __name__ == "__main__":
    # CLI interface for health checking
    validator = ProductionHealthValidator()
    report = validator.run_full_health_check()
    
    print(f"\nHealth Check Summary:")
    print(f"Overall Status: {report.overall_status.value.upper()}")
    print(f"Startup Allowed: {report.startup_allowed}")
    print(f"Checks: {len(report.healthy_dependencies)}/{report.total_checks} passed")
    
    if not report.startup_allowed:
        sys.exit(1)