"""
Tests for validation functions.
"""
import pytest
from datetime import datetime, timedelta
from app.helpers.validators import (
    validate_route_card_number,
    validate_positive_integer,
    validate_input_data,
    validate_shift_data_extended,
    validate_control_data,
    validate_json_input,
    validate_form_input
)
from utils.input_validators import sanitize_string


class TestRouteCardValidation:
    """Test route card number validation"""
    
    def test_valid_card_numbers(self, app):
        """Test various valid card numbers"""
        with app.app_context():
            assert validate_route_card_number('123456') is True
            assert validate_route_card_number('000000') is True
            assert validate_route_card_number('999999') is True
    
    def test_invalid_card_numbers(self, app):
        """Test various invalid card numbers"""
        with app.app_context():
            assert validate_route_card_number('12345') is False  # Too short
            assert validate_route_card_number('1234567') is False  # Too long
            assert validate_route_card_number('12345a') is False  # Non-numeric
            assert validate_route_card_number('abc123') is False  # Non-numeric
            assert validate_route_card_number('') is False  # Empty
            assert validate_route_card_number(None) is False  # None


class TestPositiveIntegerValidation:
    """Test positive integer validation"""
    
    def test_valid_positive_integers(self, app):
        """Test valid positive integers"""
        with app.app_context():
            is_valid, msg = validate_positive_integer(1, 'test_field')
            assert is_valid is True
            
            is_valid, msg = validate_positive_integer(100, 'test_field')
            assert is_valid is True
            
            is_valid, msg = validate_positive_integer('50', 'test_field')
            assert is_valid is True
    
    def test_invalid_positive_integers(self, app):
        """Test invalid values"""
        with app.app_context():
            is_valid, msg = validate_positive_integer(0, 'test_field')
            assert is_valid is False
            assert 'положительным' in msg
            
            is_valid, msg = validate_positive_integer(-5, 'test_field')
            assert is_valid is False
            
            is_valid, msg = validate_positive_integer('abc', 'test_field')
            assert is_valid is False
            assert 'числом' in msg


class TestInputDataValidation:
    """Test input data validation"""
    
    def test_valid_input_data(self, app):
        """Test with all required fields present"""
        with app.app_context():
            data = {
                'field1': 'value1',
                'field2': 'value2',
                'field3': 'value3'
            }
            required_fields = ['field1', 'field2', 'field3']
            
            errors = validate_input_data(data, required_fields)
            assert len(errors) == 0
    
    def test_missing_required_fields(self, app):
        """Test with missing required fields"""
        with app.app_context():
            data = {
                'field1': 'value1'
            }
            required_fields = ['field1', 'field2', 'field3']
            
            errors = validate_input_data(data, required_fields)
            assert len(errors) == 2
            assert any('field2' in error for error in errors)
            assert any('field3' in error for error in errors)
    
    def test_empty_field_values(self, app):
        """Test with empty field values"""
        with app.app_context():
            data = {
                'field1': '',
                'field2': None
            }
            required_fields = ['field1', 'field2']
            
            errors = validate_input_data(data, required_fields)
            assert len(errors) == 2


class TestShiftDataValidation:
    """Test shift data validation (already covered in test_shifts.py but more detailed here)"""
    
    def test_valid_shift_data(self, app, db_session):
        """Test with valid shift data"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            errors = validate_shift_data_extended(date, 1, ['Иванов И.И.'])
            
            assert len(errors) == 0
    
    def test_invalid_date_format(self, app, db_session):
        """Test with invalid date format"""
        with app.app_context():
            errors = validate_shift_data_extended('invalid-date', 1, ['Иванов И.И.'])
            
            assert len(errors) > 0
            assert any('формат' in error.lower() for error in errors)
    
    def test_shift_number_validation(self, app, db_session):
        """Test shift number must be 1 or 2"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            
            errors = validate_shift_data_extended(date, 0, ['Иванов И.И.'])
            assert len(errors) > 0
            
            errors = validate_shift_data_extended(date, 3, ['Иванов И.И.'])
            assert len(errors) > 0
            
            errors = validate_shift_data_extended(date, None, ['Иванов И.И.'])
            assert len(errors) > 0


class TestControlDataValidation:
    """Test control data validation (more detailed)"""
    
    def test_perfect_data(self, app):
        """Test with perfect data - no errors or warnings"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 100, {})
            assert len(errors) == 0
            assert len(warnings) == 0
    
    def test_negative_values(self, app):
        """Test with negative values"""
        with app.app_context():
            errors, warnings = validate_control_data(-10, 5, {})
            assert len(errors) > 0
            
            errors, warnings = validate_control_data(10, -5, {})
            assert len(errors) > 0
    
    def test_mismatch_calculation(self, app):
        """Test mismatch between calculated and stated accepted"""
        with app.app_context():
            # 100 cast - 10 defects = 90 accepted, but we say 85
            errors, warnings = validate_control_data(100, 85, {'Раковины': 10})
            
            # Should have warning about mismatch
            assert len(warnings) > 0
            assert any('не совпадает' in warning for warning in warnings)
    
    def test_very_high_reject_rate(self, app):
        """Test warning for very high reject rate"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 40, {'Раковины': 60})
            
            assert len(warnings) > 0
            assert any('брак' in warning.lower() for warning in warnings)
    
    def test_very_large_numbers(self, app):
        """Test warning for suspiciously large numbers"""
        with app.app_context():
            errors, warnings = validate_control_data(15000, 14000, {})
            
            assert len(warnings) > 0


class TestJSONInputValidation:
    """Test JSON input validation"""
    
    def test_valid_json_schema(self, app):
        """Test with valid JSON matching schema"""
        with app.app_context():
            data = {
                'name': 'Test',
                'age': 25,
                'active': True
            }
            schema = {
                'name': str,
                'age': int,
                'active': bool
            }
            
            errors = validate_json_input(data, schema)
            assert len(errors) == 0
    
    def test_missing_fields(self, app):
        """Test with missing required fields"""
        with app.app_context():
            data = {
                'name': 'Test'
            }
            schema = {
                'name': str,
                'age': int
            }
            
            errors = validate_json_input(data, schema)
            assert len(errors) > 0
            assert any('age' in error for error in errors)
    
    def test_wrong_types(self, app):
        """Test with wrong field types"""
        with app.app_context():
            data = {
                'name': 123,  # Should be string
                'age': 'twenty'  # Should be int
            }
            schema = {
                'name': str,
                'age': int
            }
            
            errors = validate_json_input(data, schema)
            assert len(errors) > 0


class TestFormInputValidation:
    """Test form input validation"""
    
    def test_valid_form_data(self, app):
        """Test with valid form data"""
        with app.app_context():
            form_data = {
                'count': 100,
                'name': 'Test'
            }
            
            def validate_count(value):
                return (value > 0, "Count must be positive")
            
            def validate_name(value):
                return (len(value) > 0, "Name required")
            
            validations = {
                'count': validate_count,
                'name': validate_name
            }
            
            errors = validate_form_input(form_data, validations)
            assert len(errors) == 0
    
    def test_invalid_form_data(self, app):
        """Test with invalid form data"""
        with app.app_context():
            form_data = {
                'count': -5
            }
            
            def validate_count(value):
                return (value > 0, "Count must be positive")
            
            validations = {
                'count': validate_count
            }
            
            errors = validate_form_input(form_data, validations)
            assert len(errors) > 0
            assert any('positive' in error for error in errors)


class TestEdgeCases:
    """Test edge cases in validation"""
    
    def test_boundary_values(self, app):
        """Test boundary values"""
        with app.app_context():
            # Test exactly 6 digits
            assert validate_route_card_number('123456') is True
            
            # Test exactly 5 and 7 digits
            assert validate_route_card_number('12345') is False
            assert validate_route_card_number('1234567') is False
    
    def test_unicode_handling(self, app):
        """Test handling of unicode characters"""
        with app.app_context():
            # Cyrillic characters should not be valid in card number
            assert validate_route_card_number('абвгде') is False
    
    def test_whitespace_handling(self, app):
        """Test handling of whitespace"""
        with app.app_context():
            # Whitespace should make validation fail
            assert validate_route_card_number('123 456') is False
            assert validate_route_card_number(' 123456') is False
            assert validate_route_card_number('123456 ') is False


class TestSanitization:
    """Test string sanitization (XSS protection)"""
    
    def test_sanitize_preserves_single_quotes(self, app):
        """Test that single quotes are preserved"""
        with app.app_context():
            # Common use cases with single quotes
            assert sanitize_string("It's working") == "It's working"
            assert sanitize_string("O'Brien") == "O'Brien"
            assert sanitize_string("Don't") == "Don't"
            assert sanitize_string("'quoted text'") == "'quoted text'"
    
    def test_sanitize_encodes_dangerous_characters(self, app):
        """Test that dangerous characters are HTML encoded"""
        with app.app_context():
            # Less-than and greater-than signs
            assert sanitize_string("<tag>") == "&lt;tag&gt;"
            
            # Double quotes
            assert sanitize_string('He said "hello"') == "He said &quot;hello&quot;"
            
            # Ampersands
            assert sanitize_string("Tom & Jerry") == "Tom &amp; Jerry"
            
            # All dangerous chars together (except single quotes)
            assert sanitize_string('<>&"') == "&lt;&gt;&amp;&quot;"
    
    def test_sanitize_xss_attempts(self, app):
        """Test that XSS attempts are neutralized"""
        with app.app_context():
            # Script injection
            assert sanitize_string("<script>alert('XSS')</script>") == "&lt;script&gt;alert('XSS')&lt;/script&gt;"
            
            # Image tag with onerror
            assert sanitize_string('<img src=x onerror=alert(1)>') == "&lt;img src=x onerror=alert(1)&gt;"
            
            # Event handler injection
            assert sanitize_string('"><script>evil()</script>') == "&quot;&gt;&lt;script&gt;evil()&lt;/script&gt;"
    
    def test_sanitize_mixed_content(self, app):
        """Test sanitization with mixed safe and dangerous content"""
        with app.app_context():
            # Single quotes with HTML tags
            assert sanitize_string("<div class='test'>content</div>") == "&lt;div class='test'&gt;content&lt;/div&gt;"
            
            # Apostrophes with other dangerous chars
            assert sanitize_string("It's <b>bold</b> & \"quoted\"") == "It's &lt;b&gt;bold&lt;/b&gt; &amp; &quot;quoted&quot;"
            
            # Russian text with single quotes and dangerous chars
            assert sanitize_string("Не может's быть & <test>") == "Не может's быть &amp; &lt;test&gt;"
    
    def test_sanitize_edge_cases(self, app):
        """Test edge cases"""
        with app.app_context():
            # Empty string
            assert sanitize_string("") == ""
            
            # None
            assert sanitize_string(None) == ""
            
            # Only single quotes
            assert sanitize_string("'''") == "'''"
            
            # Whitespace trimming
            assert sanitize_string("  text  ") == "text"
            
            # Multiple encodings needed
            assert sanitize_string("&lt;already&gt;") == "&amp;lt;already&amp;gt;"
    
    def test_sanitize_real_world_scenarios(self, app):
        """Test realistic user input scenarios"""
        with app.app_context():
            # User comments with apostrophes
            assert sanitize_string("I can't believe it's not butter!") == "I can't believe it's not butter!"
            
            # Technical descriptions with units
            assert sanitize_string("Temperature > 100°C & < 200°C") == "Temperature &gt; 100°C &amp; &lt; 200°C"
            
            # Names with apostrophes
            assert sanitize_string("O'Reilly & Sons") == "O'Reilly &amp; Sons"
            
            # Measurements and formulas
            assert sanitize_string("A = b' * c") == "A = b' * c"
