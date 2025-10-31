"""Error handlers for the quality control system."""

import logging
from typing import Optional
from flask import request, has_request_context


logger = logging.getLogger(__name__)


class ОшибкаБазыДанных(Exception):
    """Database error."""
    pass


class ОшибкаИнтеграции(Exception):
    """Integration error."""
    pass


class ОшибкаВалидации(Exception):
    """Validation error."""
    pass


class ErrorHandler:
    """Central error handler."""
    
    def log_user_error(self, message: str, request_obj: Optional[object] = None):
        """Log user error."""
        if request_obj and has_request_context():
            logger.error(f"User error: {message} - IP: {request.remote_addr}")
        else:
            logger.error(f"User error: {message}")


error_handler = ErrorHandler()


def validate_and_handle_errors(func):
    """Decorator to validate and handle errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ОшибкаВалидации as e:
            return handle_validation_error(e)
        except ОшибкаБазыДанных as e:
            return handle_database_error(e)
        except ОшибкаИнтеграции as e:
            return handle_integration_error(e)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return {"success": False, "error": "Внутренняя ошибка сервера"}, 500
    return wrapper


def handle_service_error(error: Exception) -> dict:
    """Handle service error."""
    logger.error(f"Service error: {str(error)}")
    return {"success": False, "error": "Ошибка сервиса"}


def handle_database_error(error: Exception) -> dict:
    """Handle database error."""
    logger.error(f"Database error: {str(error)}")
    return {"success": False, "error": "Ошибка базы данных"}


def handle_integration_error(error: Exception) -> dict:
    """Handle integration error."""
    logger.error(f"Integration error: {str(error)}")
    return {"success": False, "error": "Ошибка интеграции"}


def handle_validation_error(error: Exception) -> dict:
    """Handle validation error."""
    logger.warning(f"Validation error: {str(error)}")
    return {"success": False, "error": str(error)}
