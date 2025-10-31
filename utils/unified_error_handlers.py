"""Unified error handling with custom exceptions and Flask error handlers."""

import logging
import traceback
from typing import Optional, Dict, Any, Union, Tuple
from flask import jsonify, render_template, request, has_request_context
from werkzeug.exceptions import HTTPException
from datetime import datetime

from .unified_logging import get_logger, log_error_with_context, get_correlation_id, get_request_id


logger = get_logger(__name__)


# ===== Custom Exception Classes =====

class QualityControlError(Exception):
    """Base exception for quality control system."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.user_message = user_message or "Произошла ошибка в системе контроля качества"
        self.correlation_id = get_correlation_id()
        self.request_id = get_request_id()


class DatabaseError(QualityControlError):
    """Database operation error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message,
            details,
            user_message or "Ошибка при работе с базой данных"
        )


class IntegrationError(QualityControlError):
    """External system integration error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_attempted: bool = False
    ):
        super().__init__(
            message,
            details,
            user_message or "Ошибка при интеграции с внешней системой"
        )
        self.retry_attempted = retry_attempted


class ValidationError(QualityControlError):
    """Input validation error."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message,
            details,
            user_message or "Ошибка валидации данных"
        )
        self.field = field


class AuthenticationError(QualityControlError):
    """Authentication error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message,
            details,
            user_message or "Ошибка аутентификации"
        )


class AuthorizationError(QualityControlError):
    """Authorization error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message,
            details,
            user_message or "Недостаточно прав для выполнения операции"
        )


class ResourceNotFoundError(QualityControlError):
    """Resource not found error."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        message = f"{resource_type} не найден" + (f": {resource_id}" if resource_id else "")
        super().__init__(
            message,
            details,
            user_message or message
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class BusinessLogicError(QualityControlError):
    """Business logic violation error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message,
            details,
            user_message or message
        )


# Legacy exception classes for backward compatibility
ОшибкаБазыДанных = DatabaseError
ОшибкаИнтеграции = IntegrationError
ОшибкаВалидации = ValidationError


# ===== Error Response Builders =====

def create_error_response(
    error: Union[Exception, str],
    status_code: int = 500,
    include_details: bool = False
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        error: Exception or error message
        status_code: HTTP status code
        include_details: Include detailed error information (for debugging)
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    correlation_id = get_correlation_id()
    request_id = get_request_id()
    
    if isinstance(error, QualityControlError):
        response = {
            'success': False,
            'error': error.user_message,
            'correlation_id': correlation_id,
            'request_id': request_id,
        }
        if include_details:
            response['details'] = error.details
            response['technical_message'] = error.message
    elif isinstance(error, Exception):
        response = {
            'success': False,
            'error': 'Произошла внутренняя ошибка сервера',
            'correlation_id': correlation_id,
            'request_id': request_id,
        }
        if include_details:
            response['technical_message'] = str(error)
            response['error_type'] = type(error).__name__
    else:
        response = {
            'success': False,
            'error': str(error),
            'correlation_id': correlation_id,
            'request_id': request_id,
        }
    
    return response, status_code


def render_error_page(
    error: Union[Exception, str],
    status_code: int = 500,
    title: str = "Ошибка"
) -> Tuple[str, int]:
    """
    Render an error page.
    
    Args:
        error: Exception or error message
        status_code: HTTP status code
        title: Page title
    
    Returns:
        Tuple of (rendered_html, status_code)
    """
    correlation_id = get_correlation_id()
    request_id = get_request_id()
    
    if isinstance(error, QualityControlError):
        error_message = error.user_message
    elif isinstance(error, HTTPException):
        error_message = error.description
    elif isinstance(error, Exception):
        error_message = "Произошла внутренняя ошибка сервера"
    else:
        error_message = str(error)
    
    # Determine icon based on status code
    if status_code == 404:
        icon = "🚫"
        title = "Страница не найдена"
    elif status_code == 403:
        icon = "🔒"
        title = "Доступ запрещен"
    elif status_code == 401:
        icon = "🔐"
        title = "Требуется авторизация"
    elif status_code >= 500:
        icon = "⚠️"
        title = "Внутренняя ошибка сервера"
    else:
        icon = "❌"
    
    html = f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .error-container {{
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
                max-width: 600px;
                padding: 40px;
                text-align: center;
                margin: 20px;
            }}
            .error-icon {{
                font-size: 80px;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                font-size: 28px;
                margin: 0 0 20px 0;
            }}
            .error-message {{
                color: #666;
                font-size: 16px;
                line-height: 1.6;
                margin: 20px 0;
            }}
            .error-ids {{
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                font-size: 12px;
                color: #6c757d;
                font-family: 'Courier New', monospace;
            }}
            .error-ids div {{
                margin: 5px 0;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-top: 20px;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            }}
            .btn-secondary {{
                background: #6c757d;
                margin-left: 10px;
            }}
            .btn-secondary:hover {{
                box-shadow: 0 5px 20px rgba(108, 117, 125, 0.4);
            }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <div class="error-icon">{icon}</div>
            <h1>{title}</h1>
            <div class="error-message">{error_message}</div>
            <div class="error-ids">
                <div><strong>ID корреляции:</strong> {correlation_id}</div>
                <div><strong>ID запроса:</strong> {request_id}</div>
            </div>
            <div>
                <a href="/" class="btn">🏠 На главную</a>
                <a href="javascript:history.back()" class="btn btn-secondary">← Назад</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html, status_code


# ===== Flask Error Handlers =====

def register_error_handlers(app):
    """
    Register all error handlers with Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        log_error_with_context(
            error,
            context={'status_code': 404, 'url': request.url if has_request_context() else 'no-context'},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response("Ресурс не найден", 404)[0]), 404
        
        return render_error_page(error, 404, "Страница не найдена")
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors."""
        log_error_with_context(
            error,
            context={'status_code': 403, 'url': request.url if has_request_context() else 'no-context'},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response("Доступ запрещен", 403)[0]), 403
        
        return render_error_page(error, 403, "Доступ запрещен")
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors."""
        log_error_with_context(
            error,
            context={'status_code': 401, 'url': request.url if has_request_context() else 'no-context'},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response("Требуется авторизация", 401)[0]), 401
        
        return render_error_page(error, 401, "Требуется авторизация")
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server Error."""
        log_error_with_context(
            error,
            context={'status_code': 500, 'url': request.url if has_request_context() else 'no-context'},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 500)[0]), 500
        
        return render_error_page(error, 500, "Внутренняя ошибка сервера")
    
    @app.errorhandler(DatabaseError)
    def handle_database_error(error):
        """Handle database errors."""
        log_error_with_context(
            error,
            context={'details': error.details},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 500)[0]), 500
        
        return render_error_page(error, 500, "Ошибка базы данных")
    
    @app.errorhandler(IntegrationError)
    def handle_integration_error(error):
        """Handle integration errors."""
        log_error_with_context(
            error,
            context={'details': error.details, 'retry_attempted': error.retry_attempted},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 503)[0]), 503
        
        return render_error_page(error, 503, "Ошибка интеграции")
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors."""
        logger.warning(
            f"Validation error: {error.message}",
            field=error.field,
            details=error.details
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 400)[0]), 400
        
        return render_error_page(error, 400, "Ошибка валидации")
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors."""
        log_error_with_context(
            error,
            context={'details': error.details},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 401)[0]), 401
        
        return render_error_page(error, 401, "Ошибка аутентификации")
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        """Handle authorization errors."""
        log_error_with_context(
            error,
            context={'details': error.details},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 403)[0]), 403
        
        return render_error_page(error, 403, "Недостаточно прав")
    
    @app.errorhandler(ResourceNotFoundError)
    def handle_resource_not_found(error):
        """Handle resource not found errors."""
        logger.warning(
            f"Resource not found: {error.resource_type}",
            resource_id=error.resource_id,
            details=error.details
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 404)[0]), 404
        
        return render_error_page(error, 404, "Ресурс не найден")
    
    @app.errorhandler(BusinessLogicError)
    def handle_business_logic_error(error):
        """Handle business logic errors."""
        logger.warning(
            f"Business logic error: {error.message}",
            details=error.details
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 400)[0]), 400
        
        return render_error_page(error, 400, "Ошибка бизнес-логики")
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle all unexpected errors."""
        log_error_with_context(
            error,
            context={'error_type': type(error).__name__},
            logger=logger
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify(create_error_response(error, 500)[0]), 500
        
        return render_error_page(error, 500, "Внутренняя ошибка сервера")


# ===== Utility Functions =====

def safe_execute(func, *args, **kwargs):
    """
    Execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Result of function execution
    
    Raises:
        Appropriate QualityControlError subclass
    """
    try:
        return func(*args, **kwargs)
    except QualityControlError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        logger.exception(f"Unexpected error in {func.__name__}")
        raise QualityControlError(
            f"Unexpected error in {func.__name__}: {str(e)}",
            details={'function': func.__name__, 'error_type': type(e).__name__}
        )


def error_boundary(default_return=None, log_level='error'):
    """
    Decorator to create an error boundary around a function.
    
    Args:
        default_return: Value to return on error
        log_level: Logging level for errors ('error', 'warning', 'critical')
    
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except QualityControlError as e:
                log_method = getattr(logger, log_level, logger.error)
                log_method(
                    f"Error in {func.__name__}: {e.message}",
                    function=func.__name__,
                    details=e.details
                )
                if default_return is not None:
                    return default_return
                raise
            except Exception as e:
                log_method = getattr(logger, log_level, logger.error)
                log_method(
                    f"Unexpected error in {func.__name__}",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__
                )
                if default_return is not None:
                    return default_return
                raise QualityControlError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    details={'function': func.__name__, 'error_type': type(e).__name__}
                )
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
