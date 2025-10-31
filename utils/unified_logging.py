"""Unified logging configuration with correlation IDs and structured context."""

import logging
import sys
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from flask import request, has_request_context, g
from datetime import datetime
import json
import re


# Patterns for sensitive data that should be excluded from logs
SENSITIVE_PATTERNS = [
    re.compile(r'password\s*[=:]\s*["\']?([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'token\s*[=:]\s*["\']?([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'api[_-]?key\s*[=:]\s*["\']?([^"\'\s]+)', re.IGNORECASE),
    re.compile(r'secret\s*[=:]\s*["\']?([^"\'\s]+)', re.IGNORECASE),
]


def sanitize_sensitive_data(data: Any) -> Any:
    """Remove sensitive data from logs."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key contains sensitive information
            key_lower = str(key).lower()
            if any(word in key_lower for word in ['password', 'token', 'secret', 'key', 'credential']):
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = sanitize_sensitive_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Replace sensitive patterns in strings
        sanitized = data
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r'\1***REDACTED***', sanitized)
        return sanitized
    else:
        return data


def get_correlation_id() -> str:
    """Get or create correlation ID for the current request."""
    if has_request_context():
        if not hasattr(g, 'correlation_id'):
            # Try to get from header first
            g.correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        return g.correlation_id
    return 'no-context'


def get_request_id() -> str:
    """Get or create request ID for the current request."""
    if has_request_context():
        if not hasattr(g, 'request_id'):
            g.request_id = str(uuid.uuid4())
        return g.request_id
    return 'no-context'


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID and request ID to log records."""
    
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        record.request_id = get_request_id()
        return True


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs structured JSON logs."""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'correlation_id': getattr(record, 'correlation_id', 'no-context'),
            'request_id': getattr(record, 'request_id', 'no-context'),
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data['extra'] = sanitize_sensitive_data(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """Formatter for human-readable logs with correlation IDs."""
    
    def format(self, record):
        correlation_id = getattr(record, 'correlation_id', 'no-context')
        request_id = getattr(record, 'request_id', 'no-context')
        
        base_format = f'%(asctime)s - %(name)s - %(levelname)s - [CID:{correlation_id}] [RID:{request_id}] - %(message)s'
        formatter = logging.Formatter(base_format)
        return formatter.format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    use_json_format: bool = False
):
    """
    Set up unified logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        use_json_format: Use structured JSON format for logs
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Choose formatter
    if use_json_format:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIDFilter())
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(CorrelationIDFilter())
        root_logger.addHandler(file_handler)


def get_request_context() -> Dict[str, Any]:
    """Get current request context information."""
    if not has_request_context():
        return {
            "context": "no-request",
            "correlation_id": get_correlation_id(),
            "request_id": get_request_id()
        }
    
    from flask import session
    
    context = {
        "correlation_id": get_correlation_id(),
        "request_id": get_request_id(),
        "method": request.method,
        "path": request.path,
        "remote_addr": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'Unknown'),
    }
    
    # Add user info if available
    if 'user_id' in session:
        context["user_id"] = session.get('user_id')
        context["username"] = session.get('username', 'anonymous')
    
    return context


class StructuredLogger:
    """Logger with structured context support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, extra_fields: Optional[Dict[str, Any]] = None):
        """Log with structured context."""
        if extra_fields:
            # Sanitize sensitive data
            extra_fields = sanitize_sensitive_data(extra_fields)
            # Create a LogRecord with extra fields
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None
            )
            record.extra_fields = extra_fields
            self.logger.handle(record)
        else:
            self.logger.log(level, message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, kwargs if kwargs else None)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, kwargs if kwargs else None)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, kwargs if kwargs else None)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, kwargs if kwargs else None)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, kwargs if kwargs else None)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs):
        """Log exception with traceback."""
        if kwargs:
            kwargs = sanitize_sensitive_data(kwargs)
            record = self.logger.makeRecord(
                self.logger.name,
                logging.ERROR,
                "(unknown file)",
                0,
                message,
                (),
                sys.exc_info() if exc_info else None
            )
            record.extra_fields = kwargs
            self.logger.handle(record)
        else:
            self.logger.exception(message)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def log_operation(
    operation: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[StructuredLogger] = None
):
    """
    Log an operation with context.
    
    Args:
        operation: Operation name/description
        details: Additional details about the operation
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    context = get_request_context()
    log_data = {
        'operation': operation,
        'context': context,
        'details': details or {}
    }
    
    logger.info(f"OPERATION: {operation}", **log_data)


def log_user_action(
    action: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[StructuredLogger] = None
):
    """
    Log a user action.
    
    Args:
        action: Action description
        user_id: User ID (auto-detected if not provided)
        details: Additional details
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if has_request_context() and user_id is None:
        from flask import session
        user_id = session.get('user_id', 'anonymous')
    
    log_data = {
        'action': action,
        'user_id': user_id or 'system',
        'correlation_id': get_correlation_id(),
        'details': details or {}
    }
    
    logger.info(f"USER_ACTION: {action}", **log_data)


def log_system_event(
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[StructuredLogger] = None
):
    """
    Log a system event.
    
    Args:
        event_type: Type of event
        message: Event message
        details: Additional details
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    log_data = {
        'event_type': event_type,
        'message': message,
        'details': details or {}
    }
    
    logger.info(f"SYSTEM_EVENT: {event_type} - {message}", **log_data)


def log_error_with_context(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    logger: Optional[StructuredLogger] = None
):
    """
    Log an error with context information.
    
    Args:
        error: Exception instance
        context: Additional context information
        logger: Logger instance (uses default if not provided)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'correlation_id': get_correlation_id(),
        'request_id': get_request_id(),
        'context': context or {},
        'request_context': get_request_context() if has_request_context() else {}
    }
    
    logger.exception(f"ERROR: {type(error).__name__}: {str(error)}", **error_data)
