"""
Error handling utilities and custom exceptions.
"""
import logging
from functools import wraps
from typing import Optional, Callable, Any
from flask import jsonify, request, has_request_context

logger = logging.getLogger(__name__)


# Custom exceptions
class ОшибкаБазыДанных(Exception):
    """Database error exception"""
    pass


class ОшибкаИнтеграции(Exception):
    """Integration error exception"""
    pass


class ОшибкаВалидации(Exception):
    """Validation error exception"""
    pass


class ErrorHandler:
    """Centralized error handler"""
    
    @staticmethod
    def log_user_error(message: str, request_obj=None):
        """Log user-facing error"""
        if request_obj:
            logger.error(f"User Error: {message} - {request_obj.endpoint} - {request_obj.remote_addr}")
        else:
            logger.error(f"User Error: {message}")


# Global error handler instance
error_handler = ErrorHandler()


def log_error_and_respond(error: Exception, message: str = "Произошла ошибка", status_code: int = 500):
    """
    Centralized error handling with logging and JSON response.
    
    Args:
        error: Exception that occurred
        message: User-friendly error message
        status_code: HTTP status code
        
    Returns:
        JSON response with error details
    """
    from .logging_config import log_error_with_context
    
    request_obj = request if has_request_context() else None
    error_handler.log_user_error(f"{message}: {str(error)}", request_obj)
    
    context = {"message": message, "status_code": status_code}
    log_error_with_context(logger, error, context)
    
    return jsonify({
        'success': False,
        'error': str(error),
        'error_id': f"app_{id(error)}"
    }), status_code


def validate_and_handle_errors(func: Callable) -> Callable:
    """
    Decorator for validating and handling errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ОшибкаВалидации as e:
            return log_error_and_respond(e, "Ошибка валидации", 400)
        except ОшибкаБазыДанных as e:
            return log_error_and_respond(e, "Ошибка базы данных", 500)
        except ОшибкаИнтеграции as e:
            return log_error_and_respond(e, "Ошибка интеграции", 502)
        except Exception as e:
            return log_error_and_respond(e, "Внутренняя ошибка сервера", 500)
    return wrapper


def handle_database_error(func: Callable) -> Callable:
    """
    Decorator for handling database errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise ОшибкаБазыДанных(f"Database error: {str(e)}")
    return wrapper


def handle_integration_error(critical: bool = True) -> Callable:
    """
    Decorator for handling integration errors.
    
    Args:
        critical: Whether the error is critical
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if critical:
                    raise ОшибкаИнтеграции(f"Integration error: {str(e)}")
                else:
                    logger.warning(f"Non-critical integration error in {func.__name__}: {str(e)}")
                    return None
        return wrapper
    return decorator


def handle_validation_error(func: Callable) -> Callable:
    """
    Decorator for handling validation errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise ОшибкаВалидации(f"Validation error: {str(e)}")
    return wrapper


def handle_service_error(func: Callable) -> Callable:
    """
    Decorator for handling service layer errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ОшибкаБазыДанных, ОшибкаИнтеграции, ОшибкаВалидации):
            raise
        except Exception as e:
            logger.error(f"Service error in {func.__name__}: {str(e)}")
            raise
    return wrapper


# UI Error handlers
def ui_error_handler(error: Exception, user_friendly_message: str = None) -> str:
    """
    Handle UI errors and return user-friendly message.
    
    Args:
        error: Exception that occurred
        user_friendly_message: Optional user-friendly message
        
    Returns:
        User-friendly error message
    """
    logger.error(f"UI Error: {str(error)}")
    return user_friendly_message or "Произошла ошибка. Пожалуйста, попробуйте снова."


def handle_ui_error(func: Callable) -> Callable:
    """
    Decorator for handling UI errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = ui_error_handler(e)
            return create_user_friendly_error_message(error_message)
    return wrapper


def create_user_friendly_error_message(message: str) -> str:
    """
    Create a user-friendly error message HTML.
    
    Args:
        message: Error message
        
    Returns:
        HTML string with error message
    """
    return f"""
    <div style="padding: 20px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 5px;">
        <h3>⚠️ Ошибка</h3>
        <p>{message}</p>
        <a href="/" style="color: #004085;">Вернуться на главную</a>
    </div>
    """


def handle_ui_exception(e: Exception) -> dict:
    """
    Handle UI exceptions and return structured error data.
    
    Args:
        e: Exception that occurred
        
    Returns:
        Dictionary with error data
    """
    logger.error(f"UI Exception: {str(e)}")
    return {
        'error': True,
        'message': str(e),
        'user_message': ui_error_handler(e)
    }


def create_error_response(message: str, status_code: int = 400) -> tuple:
    """
    Create a JSON error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        Tuple of (JSON response, status code)
    """
    return jsonify({
        'success': False,
        'error': message
    }), status_code


def handle_validation_errors(errors: list) -> tuple:
    """
    Handle validation errors and return JSON response.
    
    Args:
        errors: List of error messages
        
    Returns:
        Tuple of (JSON response, status code)
    """
    return jsonify({
        'success': False,
        'errors': errors
    }), 400
