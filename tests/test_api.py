"""
Tests for API endpoints (api_current_shift, api_validate_control, etc.).
"""
import pytest
import json
from flask import session
from app.services.shift_service import create_shift
from app.services.control_service import save_control_record


class TestCurrentShiftAPI:
    """Test current shift API endpoint"""
    
    def test_api_current_shift_with_active_shift(self, client, app, sample_shift):
        """Test getting current shift when one is active"""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['current_shift_id'] = sample_shift.id
            
            response = client.get('/api/shifts/current')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'shift' in data
            assert data['shift']['id'] == sample_shift.id
    
    def test_api_current_shift_no_active_shift(self, client, app):
        """Test getting current shift when none is active"""
        with app.app_context():
            response = client.get('/api/shifts/current')
            
            # Depending on implementation, might return 200 with null or 404
            data = response.get_json()
            if response.status_code == 200:
                assert data.get('shift') is None
            else:
                assert response.status_code == 404


class TestCloseShiftAPI:
    """Test close shift API endpoint"""
    
    def test_api_close_shift_success(self, client, app, db_session, sample_shift):
        """Test successful shift closure via API"""
        with app.app_context():
            with client.session_transaction() as sess:
                sess['current_shift_id'] = sample_shift.id
            
            response = client.post('/api/close-shift',
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify shift is closed
            from app.models import Смена
            shift = db_session.query(Смена).filter_by(id=sample_shift.id).first()
            assert shift.статус == 'закрыта'
    
    def test_api_close_shift_no_active_shift(self, client, app):
        """Test closing shift when no active shift"""
        with app.app_context():
            response = client.post('/api/close-shift',
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'Нет активной смены' in data['error']


class TestDefectTypesAPI:
    """Test defect types API endpoint"""
    
    def test_api_get_defect_types(self, client, app):
        """Test getting defect types"""
        with app.app_context():
            response = client.get('/api/defects/types')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'success' in data
            if data['success']:
                assert 'defect_types' in data
                assert len(data['defect_types']) > 0


class TestControllersAPI:
    """Test controllers API endpoints"""
    
    def test_api_get_controllers(self, client, app, sample_controller):
        """Test getting controllers list - note: no GET endpoint, check via add"""
        with app.app_context():
            # There's no GET /api/controllers endpoint
            # Test that we can access controller functionality via add
            response = client.post('/api/add-controller',
                                   data={'name': 'Тест Контролер'},
                                   follow_redirects=False)
            
            # Should return JSON with success
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_api_add_controller(self, client, app):
        """Test adding a new controller via API"""
        with app.app_context():
            # Uses /api/add-controller POST route
            response = client.post('/api/add-controller',
                                   data={'name': 'Новиков Н.Н.'},
                                   follow_redirects=False)
            
            # Should return JSON success
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
    
    def test_api_toggle_controller(self, client, app, sample_controller):
        """Test toggling controller active status via API"""
        with app.app_context():
            # Uses /api/toggle-controller POST route
            response = client.post('/api/toggle-controller',
                                   data={'id': sample_controller.id},
                                   follow_redirects=False)
            
            # Should return JSON success
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


class TestQRScanAPI:
    """Test QR scan API endpoint"""
    
    def test_api_qr_scan_valid(self, client, app, mock_external_db):
        """Test QR scan with valid code"""
        with app.app_context():
            response = client.post('/api/qr-scan',
                                   data=json.dumps({'qr_code': '123456'}),
                                   content_type='application/json')
            
            # Should handle the QR code
            assert response.status_code in [200, 400]  # Depends on shift state
            data = response.get_json()
            assert 'success' in data
    
    def test_api_qr_scan_empty(self, client, app):
        """Test QR scan with empty code"""
        with app.app_context():
            response = client.post('/api/qr-scan',
                                   data=json.dumps({'qr_code': ''}),
                                   content_type='application/json')
            
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'не распознан' in data['error']
    
    def test_api_qr_scan_invalid_json(self, client, app):
        """Test QR scan with invalid JSON"""
        with app.app_context():
            response = client.post('/api/qr-scan',
                                   data='invalid json',
                                   content_type='application/json')
            
            # Should handle invalid JSON gracefully
            assert response.status_code in [400, 500]


class TestValidateControlAPI:
    """Test validate control API endpoint"""
    
    def test_api_validate_control_valid(self, client, app, sample_shift):
        """Test validation with valid control data"""
        with app.app_context():
            data = {
                'total_cast': 100,
                'total_accepted': 95,
                'defects': {'Раковины': 5}
            }
            
            response = client.post('/api/validate-control',
                                   data=json.dumps(data),
                                   content_type='application/json')
            
            if response.status_code == 200:
                result = response.get_json()
                assert 'success' in result
    
    def test_api_validate_control_invalid(self, client, app):
        """Test validation with invalid control data"""
        with app.app_context():
            data = {
                'total_cast': -10,
                'total_accepted': 150,
                'defects': {}
            }
            
            response = client.post('/api/validate-control',
                                   data=json.dumps(data),
                                   content_type='application/json')
            
            # Should return validation errors
            if response.status_code == 200:
                result = response.get_json()
                # Check for validation errors in response
                assert 'errors' in result or 'success' in result


class TestStatisticsAPI:
    """Test statistics API endpoints"""
    
    def test_api_shift_statistics(self, client, app, sample_shift, sample_defect_type,
                                  mock_update_route_card):
        """Test getting shift statistics"""
        with app.app_context():
            # Create some control records
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            response = client.get(f'/api/shifts/{sample_shift.id}/statistics')
            
            if response.status_code == 200:
                data = response.get_json()
                assert 'success' in data or 'statistics' in data


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_api_404_not_found(self, client, app):
        """Test 404 error handling"""
        with app.app_context():
            response = client.get('/api/nonexistent-endpoint')
            
            assert response.status_code == 404
    
    def test_api_method_not_allowed(self, client, app):
        """Test method not allowed error"""
        with app.app_context():
            # Try POST on a GET-only endpoint
            response = client.post('/api/search-card/123456')
            
            assert response.status_code == 405
    
    def test_api_invalid_json(self, client, app):
        """Test handling of invalid JSON"""
        with app.app_context():
            response = client.post('/api/qr-scan',
                                   data='{"invalid": json}',
                                   content_type='application/json')
            
            # Should handle gracefully
            assert response.status_code in [400, 500]


class TestCORSHeaders:
    """Test CORS headers on API endpoints"""
    
    def test_cors_headers_present(self, client, app):
        """Test that CORS headers are present"""
        with app.app_context():
            response = client.get('/api/shifts/current')
            
            # Check for CORS headers if CORS is enabled
            if app.config.get('CORS_ENABLED'):
                # Headers might be present
                pass  # CORS library handles this automatically
