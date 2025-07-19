"""
Structured logging configuration for PRP AI Assistant
12-Factor compliant logging setup with structured output
"""
import os
import sys
import structlog
from pythonjsonlogger import jsonlogger
import logging


def configure_logging():
    """Configure structured logging for the application"""
    
    # Get log level from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = os.environ.get('LOG_FORMAT', 'json').lower()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == 'json' else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s" if log_format == 'json' else "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level)
    )
    
    # Set specific loggers
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    return structlog.get_logger()


def get_logger(name: str = None):
    """Get a configured logger instance"""
    return structlog.get_logger(name)


# Request logging middleware
def log_request(request_id: str, method: str, path: str, user_id: str = None):
    """Log incoming requests with structured data"""
    logger = get_logger("request")
    logger.info(
        "incoming_request",
        request_id=request_id,
        method=method,
        path=path,
        user_id=user_id
    )


def log_response(request_id: str, status_code: int, duration_ms: float):
    """Log outgoing responses with structured data"""
    logger = get_logger("response")
    logger.info(
        "outgoing_response",
        request_id=request_id,
        status_code=status_code,
        duration_ms=duration_ms
    )


def log_task_start(task_id: str, task_name: str, args: list = None, kwargs: dict = None):
    """Log Celery task start"""
    logger = get_logger("task")
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task_name,
        args=args,
        kwargs=kwargs
    )


def log_task_complete(task_id: str, task_name: str, duration_ms: float, result=None):
    """Log Celery task completion"""
    logger = get_logger("task")
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task_name,
        duration_ms=duration_ms,
        result=result
    )


def log_error(error: Exception, context: dict = None):
    """Log errors with structured context"""
    logger = get_logger("error")
    logger.error(
        "application_error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        exc_info=True
    )


def log_security_event(event_type: str, user_id: str = None, ip_address: str = None, details: dict = None):
    """Log security-related events"""
    logger = get_logger("security")
    logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        details=details or {}
    )


def log_performance_metric(metric_name: str, value: float, unit: str = "ms", tags: dict = None):
    """Log performance metrics"""
    logger = get_logger("metrics")
    logger.info(
        "performance_metric",
        metric_name=metric_name,
        value=value,
        unit=unit,
        tags=tags or {}
    )


# PRP-specific logging functions
def log_prp_analysis(prp_id: str, analysis_type: str, score: float, factors: dict):
    """Log PRP analysis results"""
    logger = get_logger("prp.analysis")
    logger.info(
        "prp_analysis_completed",
        prp_id=prp_id,
        analysis_type=analysis_type,
        score=score,
        factors=factors
    )


def log_prp_improvement(prp_id: str, factor: str, before_score: float, after_score: float, changes: list):
    """Log PRP improvement implementation"""
    logger = get_logger("prp.improvement")
    logger.info(
        "prp_improvement_applied",
        prp_id=prp_id,
        factor=factor,
        before_score=before_score,
        after_score=after_score,
        changes=changes
    )