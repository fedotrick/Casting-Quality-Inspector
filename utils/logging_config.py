"""Logging configuration for the quality control system."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from flask import request, has_request_context
from datetime import datetime
import json


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None):
    """Set up logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )


def get_user_info() -> Dict[str, Any]:
    """Get current user information from session/request."""
    if not has_request_context():
        return {"user_id": "system", "ip": "N/A"}
    
    from flask import session
    return {
        "user_id": session.get('user_id', 'anonymous'),
        "username": session.get('username', 'anonymous'),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    }


def log_operation(operation: str, details: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
    """Log an operation with context."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    user_info = get_user_info()
    log_data = {
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
        'user_info': user_info,
        'details': details or {}
    }
    logger.info(f"OPERATION: {json.dumps(log_data, ensure_ascii=False)}")


def log_user_action(user_id: str, action: str, details: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
    """Log a user action."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    action_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"USER_ACTION: {json.dumps(action_data, ensure_ascii=False)}")


def log_system_event(event_type: str, message: str, details: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
    """Log a system event."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    event_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"SYSTEM_EVENT: {json.dumps(event_data, ensure_ascii=False)}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log an error with context information."""
    import traceback
    
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {},
        'user_info': get_user_info() if has_request_context() else {}
    }
    
    # Log error without stack trace in production
    logger.error(f"ERROR: {json.dumps(error_data, ensure_ascii=False)}")
    
    # Log full stack trace at debug level
    logger.debug(f"TRACEBACK: {traceback.format_exc()}")
