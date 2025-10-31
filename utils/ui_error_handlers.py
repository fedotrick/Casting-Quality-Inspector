"""UI error handlers for the quality control system."""

import logging
from typing import Optional, Dict, Any
from flask import jsonify


logger = logging.getLogger(__name__)


class UIErrorHandler:
    """Handler for UI errors."""
    
    def handle_error(self, error: Exception, user_friendly: bool = True):
        """Handle UI error."""
        logger.error(f"UI error: {str(error)}")
        if user_friendly:
            return create_user_friendly_error_message(error)
        return str(error)


ui_error_handler = UIErrorHandler()


def handle_ui_error(error: Exception) -> Dict[str, Any]:
    """Handle UI error and return formatted response."""
    return ui_error_handler.handle_error(error)


def create_user_friendly_error_message(error: Exception) -> str:
    """Create user-friendly error message."""
    # Don't leak technical details
    return "Произошла ошибка. Пожалуйста, попробуйте еще раз."


def handle_ui_exception(error: Exception) -> tuple:
    """Handle UI exception and return JSON response."""
    message = create_user_friendly_error_message(error)
    return jsonify({"success": False, "error": message}), 500


def create_error_response(message: str, status_code: int = 400) -> tuple:
    """Create error response."""
    return jsonify({"success": False, "error": message}), status_code


def handle_validation_errors(errors: list) -> tuple:
    """Handle validation errors."""
    return jsonify({"success": False, "errors": errors}), 400
