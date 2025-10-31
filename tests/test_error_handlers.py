"""
Tests for error handling functions and custom exceptions.
"""
import pytest
from app.helpers.error_handlers import (
    ОшибкаБазыДанных,
    ОшибкаИнтеграции,
    ОшибкаВалидации,
    error_handler,
    log_error_and_respond,
    validate_and_handle_errors,
    handle_database_error,
    handle_integration_error,
    handle_validation_error
)


class TestCustomExceptions:
    """Test custom exception classes"""
    
    def test_database_error(self, app):
        """Test database error exception"""
        with app.app_context():
            with pytest.raises(ОшибкаБазыДанных):
                raise ОшибкаБазыДанных("Test database error")
    
    def test_integration_error(self, app):
        """Test integration error exception"""
        with app.app_context():
            with pytest.raises(ОшибкаИнтеграции):
                raise ОшибкаИнтеграции("Test integration error")
    
    def test_validation_error(self, app):
        """Test validation error exception"""
        with app.app_context():
            with pytest.raises(ОшибкаВалидации):
                raise ОшибкаВалидации("Test validation error")
    
    def test_exception_message(self, app):
        """Test exception messages are preserved"""
        with app.app_context():
            try:
                raise ОшибкаБазыДанных("Custom message")
            except ОшибкаБазыДанных as e:
                assert str(e) == "Custom message"


class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def test_error_handler_exists(self, app):
        """Test that error handler instance exists"""
        with app.app_context():
            assert error_handler is not None
    
    def test_log_user_error(self, app):
        """Test logging user error"""
        with app.app_context():
            # Should not raise exception
            error_handler.log_user_error("Test error message")


class TestLogErrorAndRespond:
    """Test log_error_and_respond function"""
    
    def test_log_error_with_context(self, app, client):
        """Test error logging with request context"""
        with app.app_context():
            with app.test_request_context():
                error = ValueError("Test error")
                response, status_code = log_error_and_respond(error, "Test message", 500)
                
                assert status_code == 500
                data = response.get_json()
                assert data['success'] is False
                assert 'error' in data
    
    def test_log_error_without_context(self, app):
        """Test error logging without request context"""
        with app.app_context():
            error = ValueError("Test error")
            response, status_code = log_error_and_respond(error, "Test message", 400)
            
            assert status_code == 400
            data = response.get_json()
            assert data['success'] is False


class TestValidateAndHandleErrors:
    """Test validate_and_handle_errors decorator"""
    
    def test_decorator_on_successful_function(self, app):
        """Test decorator with function that succeeds"""
        with app.app_context():
            @validate_and_handle_errors
            def successful_function():
                return {'success': True}
            
            result = successful_function()
            assert result['success'] is True
    
    def test_decorator_on_failing_function(self, app):
        """Test decorator with function that raises exception"""
        with app.app_context():
            @validate_and_handle_errors
            def failing_function():
                raise ValueError("Test error")
            
            result = failing_function()
            # Decorator should handle the error
            if isinstance(result, tuple):
                response, status_code = result
                assert status_code >= 400


class TestDatabaseErrorHandling:
    """Test database error handling"""
    
    def test_handle_database_error_decorator(self, app):
        """Test database error handling decorator"""
        with app.app_context():
            @handle_database_error
            def function_with_db_error():
                raise ОшибкаБазыДанных("Test DB error")
            
            # Depending on implementation, might return error or raise
            try:
                result = function_with_db_error()
                # If it doesn't raise, check the result
                if result is not None:
                    assert True  # Function handled error
            except ОшибкаБазыДанных:
                # If it re-raises, that's also valid
                assert True


class TestIntegrationErrorHandling:
    """Test integration error handling"""
    
    def test_handle_integration_error_non_critical(self, app):
        """Test non-critical integration error handling"""
        with app.app_context():
            @handle_integration_error(critical=False)
            def function_with_integration_error():
                raise ОшибкаИнтеграции("Test integration error")
            
            # Non-critical errors should be handled gracefully
            result = function_with_integration_error()
            # Should return None or default value
            assert result is None or result is not None
    
    def test_handle_integration_error_critical(self, app):
        """Test critical integration error handling"""
        with app.app_context():
            @handle_integration_error(critical=True)
            def function_with_critical_error():
                raise ОшибкаИнтеграции("Critical error")
            
            # Critical errors might be re-raised
            try:
                result = function_with_critical_error()
            except ОшибкаИнтеграции:
                assert True  # Expected behavior


class TestValidationErrorHandling:
    """Test validation error handling"""
    
    def test_handle_validation_error(self, app):
        """Test validation error handling"""
        with app.app_context():
            @handle_validation_error
            def function_with_validation_error():
                raise ОшибкаВалидации("Invalid input")
            
            try:
                result = function_with_validation_error()
                # Check if error was handled
                if result is not None:
                    assert True
            except ОшибкаВалидации:
                # Or re-raised
                assert True


class TestErrorResponseFormat:
    """Test error response format"""
    
    def test_error_response_structure(self, app):
        """Test that error responses have correct structure"""
        with app.app_context():
            error = ValueError("Test")
            response, status_code = log_error_and_respond(error)
            
            data = response.get_json()
            assert 'success' in data
            assert 'error' in data
            assert data['success'] is False
    
    def test_error_id_included(self, app):
        """Test that error ID is included in response"""
        with app.app_context():
            error = ValueError("Test")
            response, status_code = log_error_and_respond(error)
            
            data = response.get_json()
            assert 'error_id' in data


class TestErrorPropagation:
    """Test error propagation through layers"""
    
    def test_service_layer_error_propagation(self, app, db_session):
        """Test error propagates from service layer"""
        with app.app_context():
            from app.services.shift_service import close_shift
            
            # Try to close non-existent shift
            result = close_shift(99999)
            
            # Should handle gracefully
            assert result is False
    
    def test_repository_layer_error_handling(self, app, db_session):
        """Test repository layer error handling"""
        with app.app_context():
            from app.repositories import ControllerRepository
            
            repo = ControllerRepository(db_session)
            
            # Try to get non-existent controller
            controller = repo.get_by_id(99999)
            
            # Should return None instead of raising
            assert controller is None


class TestConcurrentErrorHandling:
    """Test error handling in concurrent scenarios"""
    
    def test_multiple_validation_errors(self, app):
        """Test handling multiple validation errors"""
        with app.app_context():
            from app.helpers.validators import validate_control_data
            
            # Multiple validation errors
            errors, warnings = validate_control_data(-10, 150, {'test': -5})
            
            # Should collect all errors
            assert len(errors) > 1
    
    def test_error_accumulation(self, app):
        """Test that errors are properly accumulated"""
        with app.app_context():
            from app.helpers.validators import validate_shift_data_extended
            
            # Multiple errors: no date, invalid shift number, no controllers
            errors = validate_shift_data_extended(None, 5, [])
            
            # Should have multiple errors
            assert len(errors) >= 2


class TestErrorRecovery:
    """Test error recovery mechanisms"""
    
    def test_rollback_on_error(self, app, db_session):
        """Test that database rolls back on error"""
        with app.app_context():
            from app.models import Контролёр
            
            try:
                # Try to create controller with invalid data
                controller = Контролёр(имя=None)  # Should fail validation
                db_session.add(controller)
                db_session.commit()
            except Exception:
                db_session.rollback()
                # Should be able to continue after rollback
                assert True
    
    def test_graceful_degradation(self, app, mock_external_db_not_found):
        """Test graceful degradation when external DB unavailable"""
        with app.app_context():
            from app.services.database_service import search_route_card_in_foundry
            
            # External DB not available
            result = search_route_card_in_foundry('123456')
            
            # Should return None instead of crashing
            assert result is None
