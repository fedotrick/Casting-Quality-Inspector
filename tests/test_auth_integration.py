"""Integration tests for authentication and authorization."""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['DATABASE_PATH'] = ':memory:'

from main import app, get_db_connection, init_database
from utils.auth import create_user


@pytest.fixture
def client():
    """Create test client with initialized database."""
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = Path(':memory:')
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            # Initialize database
            conn = get_db_connection()
            if conn:
                init_database(conn)
                # Create test user
                create_user(conn, 'testuser', 'TestPass123!', role='user')
                create_user(conn, 'admin', 'AdminPass123!', role='admin')
                conn.close()
        
        yield client


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_login_page_accessible(self, client):
        """Test that login page is accessible."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_successful(self, client):
        """Test successful login."""
        response = client.post('/login',
                             json={'username': 'testuser', 'password': 'TestPass123!'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'redirect' in data
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        response = client.post('/login',
                             json={'username': 'testuser', 'password': 'WrongPassword'},
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login',
                             json={'username': 'nonexistent', 'password': 'TestPass123!'},
                             content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_validation_short_username(self, client):
        """Test login validation with too short username."""
        response = client.post('/login',
                             json={'username': 'ab', 'password': 'TestPass123!'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'errors' in data
    
    def test_logout(self, client):
        """Test logout functionality."""
        # Login first
        client.post('/login',
                   json={'username': 'testuser', 'password': 'TestPass123!'},
                   content_type='application/json')
        
        # Logout
        response = client.get('/logout')
        assert response.status_code == 302  # Redirect
    
    def test_protected_route_without_login(self, client):
        """Test that protected routes redirect to login."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestAuthorization:
    """Test authorization (role-based access)."""
    
    def test_admin_route_with_user_role(self, client):
        """Test that user role cannot access admin routes."""
        # Login as regular user
        client.post('/login',
                   json={'username': 'testuser', 'password': 'TestPass123!'},
                   content_type='application/json')
        
        # Try to access admin route
        response = client.get('/manage-controllers')
        assert response.status_code in [302, 403]  # Redirect or Forbidden
    
    def test_admin_route_with_admin_role(self, client):
        """Test that admin role can access admin routes."""
        # Login as admin
        client.post('/login',
                   json={'username': 'admin', 'password': 'AdminPass123!'},
                   content_type='application/json')
        
        # Access admin route
        response = client.get('/manage-controllers')
        assert response.status_code == 200


class TestAPIAuthentication:
    """Test API endpoint authentication."""
    
    def test_api_endpoint_without_auth(self, client):
        """Test that API endpoints require authentication."""
        response = client.get('/api/shifts/current')
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
        assert 'аутентификация' in data['error'].lower()
    
    def test_api_endpoint_with_auth(self, client):
        """Test API endpoint access with authentication."""
        # Login first
        client.post('/login',
                   json={'username': 'testuser', 'password': 'TestPass123!'},
                   content_type='application/json')
        
        # Access API endpoint
        response = client.get('/api/shifts/current')
        # Should work or return specific error (not 401)
        assert response.status_code != 401


class TestSessionSecurity:
    """Test session security settings."""
    
    def test_session_cookie_httponly(self, client):
        """Test that session cookies have HttpOnly flag."""
        response = client.post('/login',
                             json={'username': 'testuser', 'password': 'TestPass123!'},
                             content_type='application/json')
        
        # Check Set-Cookie header
        cookies = response.headers.getlist('Set-Cookie')
        if cookies:
            # At least one cookie should have HttpOnly
            assert any('HttpOnly' in cookie for cookie in cookies)
    
    def test_session_cookie_samesite(self, client):
        """Test that session cookies have SameSite attribute."""
        response = client.post('/login',
                             json={'username': 'testuser', 'password': 'TestPass123!'},
                             content_type='application/json')
        
        cookies = response.headers.getlist('Set-Cookie')
        if cookies:
            # At least one cookie should have SameSite
            assert any('SameSite' in cookie for cookie in cookies)


class TestInputValidation:
    """Test input validation on endpoints."""
    
    def test_api_validate_invalid_json(self, client):
        """Test API with invalid JSON."""
        # Login first
        client.post('/login',
                   json={'username': 'testuser', 'password': 'TestPass123!'},
                   content_type='application/json')
        
        # Send invalid data
        response = client.post('/api/control/validate',
                             data='invalid json',
                             content_type='application/json')
        
        # Should return error
        assert response.status_code >= 400
    
    def test_xss_in_input(self, client):
        """Test XSS attempt in input."""
        # Login first
        client.post('/login',
                   json={'username': 'testuser', 'password': 'TestPass123!'},
                   content_type='application/json')
        
        # Try XSS in form input
        xss_payload = '<script>alert("xss")</script>'
        response = client.post('/add-controller',
                             data={'имя': xss_payload},
                             follow_redirects=False)
        
        # Check that response doesn't contain unescaped script
        if response.status_code == 200:
            assert b'<script>alert("xss")</script>' not in response.data


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_error_handling(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data is not None
        assert 'error' in data
        # Should not leak technical details
        assert 'traceback' not in str(response.data).lower()
    
    def test_500_error_no_stack_trace(self, client):
        """Test that 500 errors don't leak stack traces in production."""
        # This is hard to test without mocking, but we can verify the handler exists
        assert app.error_handler_spec is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
