"""
Logging configuration and utilities for the application.
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from flask import request, has_request_context


def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """
    Setup application logging with file and console handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
    """
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )


def get_user_info() -> Dict[str, Any]:
    """
    Get current user information from request context.
    
    Returns:
        Dictionary with user information
    """
    if has_request_context():
        return {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'endpoint': request.endpoint,
            'method': request.method,
            'url': request.url
        }
    return {}


def log_operation(logger: logging.Logger, operation: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an operation with contextual information.
    
    Args:
        logger: Logger instance
        operation: Operation name
        details: Optional additional details
    """
    user_info = get_user_info()
    log_data = {
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
        'user_info': user_info,
        'details': details or {}
    }
    logger.info(f"ОПЕРАЦИЯ: {json.dumps(log_data, ensure_ascii=False, indent=2)}")


def log_user_action(user_id: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a user action.
    
    Args:
        user_id: User identifier
        action: Action performed
        details: Optional additional details
    """
    logger = logging.getLogger(__name__)
    action_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"ДЕЙСТВИЕ ПОЛЬЗОВАТЕЛЯ: {json.dumps(action_data, ensure_ascii=False, indent=2)}")


def log_system_event(event_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a system event.
    
    Args:
        event_type: Type of event
        message: Event message
        details: Optional additional details
    """
    logger = logging.getLogger(__name__)
    event_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"СИСТЕМНОЕ СОБЫТИЕ: {json.dumps(event_data, ensure_ascii=False, indent=2)}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with contextual information.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Optional context information
    """
    import traceback
    
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {},
        'traceback': traceback.format_exc()
    }
    logger.error(f"ОШИБКА: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
