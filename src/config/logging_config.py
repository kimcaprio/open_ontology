"""
Centralized logging configuration for the ontology platform
"""

import os
import sys
from pathlib import Path
from loguru import logger
from typing import Dict, Any

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Service-specific loggers configuration
LOGGING_CONFIG = {
    "ontology": {
        "file": LOGS_DIR / "ontology_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | ONTOLOGY | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "data_source": {
        "file": LOGS_DIR / "data_source_service.log", 
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | DATA_SOURCE | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "catalog": {
        "file": LOGS_DIR / "catalog_service.log",
        "level": "INFO", 
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | CATALOG | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "activity": {
        "file": LOGS_DIR / "activity_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | ACTIVITY | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB", 
        "retention": "30 days",
        "compression": "zip"
    },
    "ai_suggestions": {
        "file": LOGS_DIR / "ai_suggestions_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | AI_SUGGESTIONS | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days", 
        "compression": "zip"
    },
    "lineage": {
        "file": LOGS_DIR / "lineage_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | LINEAGE | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "minio": {
        "file": LOGS_DIR / "minio_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | MINIO | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "ollama": {
        "file": LOGS_DIR / "ollama_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | OLLAMA | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "trino": {
        "file": LOGS_DIR / "trino_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | TRINO | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    },
    "unity_catalog": {
        "file": LOGS_DIR / "unity_catalog_service.log",
        "level": "INFO",
        "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | UNITY_CATALOG | {function}:{line} | {message} | {extra}",
        "rotation": "10 MB",
        "retention": "30 days",
        "compression": "zip"
    }
}

class ServiceLogger:
    """Service-specific logger with enhanced functionality"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config = LOGGING_CONFIG.get(service_name, LOGGING_CONFIG["ontology"])
        self._logger = logger.bind(service=service_name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup service-specific logger with configuration"""
        # Add file handler for this service
        self._logger.add(
            str(self.config["file"]),
            level=self.config["level"],
            format=self.config["format"],
            rotation=self.config["rotation"],
            retention=self.config["retention"],
            compression=self.config["compression"],
            enqueue=True,  # Thread-safe logging
            backtrace=True,
            diagnose=True
        )
    
    def log_function_start(self, function_name: str, **kwargs):
        """Log function start with parameters"""
        self._logger.info(f"Starting function: {function_name}", 
                         function=function_name, 
                         status="START",
                         parameters=kwargs)
    
    def log_function_success(self, function_name: str, result=None, execution_time=None, **kwargs):
        """Log successful function completion"""
        extra_data = {"function": function_name, "status": "SUCCESS"}
        if result is not None:
            extra_data["result_type"] = type(result).__name__
            if hasattr(result, '__len__'):
                extra_data["result_count"] = len(result)
        if execution_time is not None:
            extra_data["execution_time_ms"] = execution_time
        extra_data.update(kwargs)
        
        self._logger.success(f"Function completed successfully: {function_name}", **extra_data)
    
    def log_function_error(self, function_name: str, error: Exception, **kwargs):
        """Log function error with exception details"""
        self._logger.error(f"Function failed: {function_name} - {str(error)}", 
                          function=function_name,
                          status="ERROR", 
                          error_type=type(error).__name__,
                          error_message=str(error),
                          **kwargs)
    
    def log_function_warning(self, function_name: str, message: str, **kwargs):
        """Log function warning"""
        self._logger.warning(f"Function warning: {function_name} - {message}",
                           function=function_name,
                           status="WARNING",
                           **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._logger.info(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._logger.error(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._logger.warning(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._logger.debug(message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message"""
        self._logger.success(message, **kwargs)

# Service-specific logger instances
service_loggers: Dict[str, ServiceLogger] = {}

def get_service_logger(service_name: str) -> ServiceLogger:
    """Get or create service-specific logger"""
    if service_name not in service_loggers:
        service_loggers[service_name] = ServiceLogger(service_name)
    return service_loggers[service_name]

def setup_logging():
    """Initialize logging configuration"""
    # Remove default logger to avoid duplication
    logger.remove()
    
    # Add console logger for development
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
        colorize=True
    )
    
    # Create service loggers
    for service_name in LOGGING_CONFIG.keys():
        get_service_logger(service_name)
    
    logger.info("Service logging system initialized")

def log_service_health():
    """Log health status of all services"""
    for service_name in LOGGING_CONFIG.keys():
        service_logger = get_service_logger(service_name)
        service_logger.info("Service health check", status="HEALTHY") 