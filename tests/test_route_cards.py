"""
Tests for route card search with mocked external DB.
"""
import pytest
from app.services.database_service import (
    search_route_card_in_foundry,
    check_card_already_processed
)
from app.helpers.validators import validate_route_card_number


class TestRouteCardValidation:
    """Test route card number validation"""
    
    def test_validate_route_card_valid(self, app):
        """Test validation with valid card number"""
        with app.app_context():
            assert validate_route_card_number('123456') is True
    
    def test_validate_route_card_invalid_length(self, app):
        """Test validation with invalid length"""
        with app.app_context():
            assert validate_route_card_number('12345') is False
            assert validate_route_card_number('1234567') is False
    
    def test_validate_route_card_non_numeric(self, app):
        """Test validation with non-numeric characters"""
        with app.app_context():
            assert validate_route_card_number('12345a') is False
            assert validate_route_card_number('abc123') is False
    
    def test_validate_route_card_empty(self, app):
        """Test validation with empty string"""
        with app.app_context():
            assert validate_route_card_number('') is False
            assert validate_route_card_number(None) is False


class TestRouteCardSearch:
    """Test route card search functionality"""
    
    def test_search_route_card_found(self, app, mock_external_db):
        """Test successful route card search"""
        with app.app_context():
            result = search_route_card_in_foundry('123456')
            
            assert result is not None
            assert result['Маршрутная_карта'] == '123456'
            assert 'Наименование_отливки' in result
            mock_external_db.assert_called_once_with('123456')
    
    def test_search_route_card_not_found(self, app, mock_external_db_not_found):
        """Test route card not found"""
        with app.app_context():
            result = search_route_card_in_foundry('999999')
            
            assert result is None
            mock_external_db_not_found.assert_called_once_with('999999')
    
    def test_search_route_card_invalid_format(self, app, mock_external_db):
        """Test search with invalid card format"""
        with app.app_context():
            result = search_route_card_in_foundry('invalid')
            
            # Should return None for invalid format
            assert result is None


class TestDuplicateCardCheck:
    """Test duplicate card checking"""
    
    def test_check_card_not_processed(self, app, db_session, sample_shift):
        """Test card that hasn't been processed"""
        with app.app_context():
            is_duplicate = check_card_already_processed('123456')
            assert is_duplicate is False
    
    def test_check_card_already_processed(self, app, db_session, sample_shift,
                                          sample_defect_type, mock_update_route_card):
        """Test card that has already been processed"""
        with app.app_context():
            from flask import session
            from app.services.control_service import save_control_record
            
            # Set current shift in session
            session['current_shift_id'] = sample_shift.id
            
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='777777',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            # Check if it's marked as processed
            is_duplicate = check_card_already_processed('777777')
            assert is_duplicate is True


class TestRouteCardAPIIntegration:
    """Test route card API integration"""
    
    def test_api_search_card_success(self, client, app, mock_external_db):
        """Test API endpoint for card search - success"""
        with app.app_context():
            response = client.get('/api/search-card/123456')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'card' in data
            assert data['card']['Маршрутная_карта'] == '123456'
    
    def test_api_search_card_not_found(self, client, app, mock_external_db_not_found):
        """Test API endpoint for card search - not found"""
        with app.app_context():
            response = client.get('/api/search-card/999999')
            
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert 'не найдена' in data['error']
    
    def test_api_search_card_invalid_format(self, client, app):
        """Test API endpoint with invalid card format"""
        with app.app_context():
            response = client.get('/api/search-card/invalid')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'Неверный формат' in data['error']
    
    def test_api_search_card_already_processed(self, client, app, db_session, 
                                               sample_shift, sample_defect_type,
                                               mock_external_db, mock_update_route_card):
        """Test API endpoint when card already processed"""
        with app.app_context():
            from flask import session
            from app.services.control_service import save_control_record
            
            # Create a session for the test
            with client.session_transaction() as sess:
                sess['current_shift_id'] = sample_shift.id
            
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='123456',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            response = client.get('/api/search-card/123456')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'уже обработана' in data['error']
            assert data.get('already_processed') is True
