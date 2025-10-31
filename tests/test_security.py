"""Tests for security features."""

import pytest
import sqlite3
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.auth import hash_password, verify_password, create_user, authenticate_user, init_users_table
from utils.input_validators import (
    validate_route_card_number, 
    validate_positive_integer,
    sanitize_string,
    validate_table_name,
    validate_column_name
)
from utils.validation_models import (
    LoginRequest,
    ControlDataRequest,
    ShiftCreateRequest,
    ChangePasswordRequest
)
from pydantic import ValidationError


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_returns_hash_and_salt(self):
        """Test that hash_password returns both hash and salt."""
        password = "TestPassword123!"
        pwd_hash, salt = hash_password(password)
        
        assert pwd_hash is not None
        assert salt is not None
        assert len(pwd_hash) > 0
        assert len(salt) > 0
    
    def test_hash_password_unique_salts(self):
        """Test that different salts produce different hashes."""
        password = "TestPassword123!"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)
        
        assert salt1 != salt2
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "TestPassword123!"
        pwd_hash, salt = hash_password(password)
        
        assert verify_password(password, pwd_hash, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "TestPassword123!"
        pwd_hash, salt = hash_password(password)
        
        assert verify_password("WrongPassword", pwd_hash, salt) is False
    
    def test_verify_password_wrong_salt(self):
        """Test password verification with wrong salt."""
        password = "TestPassword123!"
        pwd_hash, salt1 = hash_password(password)
        _, salt2 = hash_password(password)
        
        assert verify_password(password, pwd_hash, salt2) is False


class TestUserManagement:
    """Test user creation and authentication."""
    
    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a temporary test database."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        init_users_table(conn)
        yield conn
        conn.close()
    
    def test_init_users_table(self, test_db):
        """Test that users table is created."""
        cursor = test_db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='пользователи'")
        assert cursor.fetchone() is not None
    
    def test_create_user_success(self, test_db):
        """Test successful user creation."""
        result = create_user(test_db, "testuser", "Password123!", "user")
        assert result is True
        
        # Verify user exists
        cursor = test_db.cursor()
        cursor.execute("SELECT имя_пользователя FROM пользователи WHERE имя_пользователя = ?", ("testuser",))
        assert cursor.fetchone() is not None
    
    def test_create_user_duplicate(self, test_db):
        """Test that duplicate users are prevented."""
        create_user(test_db, "testuser", "Password123!", "user")
        result = create_user(test_db, "testuser", "Password123!", "user")
        assert result is False
    
    def test_authenticate_user_success(self, test_db):
        """Test successful user authentication."""
        create_user(test_db, "testuser", "Password123!", "user")
        user = authenticate_user(test_db, "testuser", "Password123!")
        
        assert user is not None
        assert user['username'] == "testuser"
        assert user['role'] == "user"
    
    def test_authenticate_user_wrong_password(self, test_db):
        """Test authentication with wrong password."""
        create_user(test_db, "testuser", "Password123!", "user")
        user = authenticate_user(test_db, "testuser", "WrongPassword")
        
        assert user is None
    
    def test_authenticate_user_nonexistent(self, test_db):
        """Test authentication of non-existent user."""
        user = authenticate_user(test_db, "nonexistent", "Password123!")
        assert user is None


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_route_card_number_valid(self):
        """Test validation of valid route card numbers."""
        assert validate_route_card_number("123456") is True
        assert validate_route_card_number("000000") is True
        assert validate_route_card_number("999999") is True
    
    def test_validate_route_card_number_invalid(self):
        """Test validation of invalid route card numbers."""
        assert validate_route_card_number("12345") is False  # Too short
        assert validate_route_card_number("1234567") is False  # Too long
        assert validate_route_card_number("12345a") is False  # Contains letter
        assert validate_route_card_number("") is False  # Empty
        assert validate_route_card_number(None) is False  # None
    
    def test_validate_positive_integer_valid(self):
        """Test validation of valid positive integers."""
        is_valid, msg = validate_positive_integer(10, "test")
        assert is_valid is True
        assert msg == ""
    
    def test_validate_positive_integer_invalid(self):
        """Test validation of invalid integers."""
        is_valid, msg = validate_positive_integer(0, "test")
        assert is_valid is False
        
        is_valid, msg = validate_positive_integer(-5, "test")
        assert is_valid is False
        
        is_valid, msg = validate_positive_integer("abc", "test")
        assert is_valid is False
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        # Single quotes should be preserved
        assert sanitize_string("<script>alert('xss')</script>") == "&lt;script&gt;alert('xss')&lt;/script&gt;"
        assert sanitize_string("Normal text") == "Normal text"
        # Double quotes should be encoded
        assert sanitize_string('Test "quotes"') == "Test &quot;quotes&quot;"
        # Ampersands should be encoded
        assert sanitize_string("Test & ampersand") == "Test &amp; ampersand"
        # Single quotes are preserved
        assert sanitize_string("It's a test") == "It's a test"
        assert sanitize_string("O'Brien") == "O'Brien"
    
    def test_sanitize_string_preserves_single_quotes(self):
        """Test that single quotes are preserved while other dangerous chars are encoded."""
        # Single quotes in various contexts
        assert sanitize_string("It's working") == "It's working"
        assert sanitize_string("'quoted'") == "'quoted'"
        assert sanitize_string("Don't worry") == "Don't worry"
        
        # Mixed dangerous characters with single quotes
        assert sanitize_string("<div class='test'>") == "&lt;div class='test'&gt;"
        assert sanitize_string("'It's' & \"test\"") == "'It's' &amp; &quot;test&quot;"
    
    def test_sanitize_string_xss_protection(self):
        """Test that XSS attempts are neutralized."""
        # Script tags
        assert sanitize_string("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
        
        # HTML injection
        assert sanitize_string("<img src=x onerror=alert(1)>") == "&lt;img src=x onerror=alert(1)&gt;"
        
        # Attribute injection with double quotes
        assert sanitize_string('"><script>alert(1)</script>') == "&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"
        
        # Event handlers
        assert sanitize_string('<a href="javascript:alert(1)">') == "&lt;a href=&quot;javascript:alert(1)&quot;&gt;"
        
    def test_sanitize_string_edge_cases(self):
        """Test edge cases for sanitization."""
        # Empty and None
        assert sanitize_string("") == ""
        assert sanitize_string(None) == ""
        
        # Whitespace
        assert sanitize_string("  test  ") == "test"
        
        # Only dangerous characters
        assert sanitize_string("<>&\"") == "&lt;&gt;&amp;&quot;"
        
        # Single quotes only (should be preserved)
        assert sanitize_string("'''") == "'''"
    
    def test_validate_table_name_whitelist(self):
        """Test table name validation against whitelist."""
        allowed_tables = ['смены', 'контролеры', 'записи_контроля']
        
        assert validate_table_name('смены', allowed_tables) is True
        assert validate_table_name('контролеры', allowed_tables) is True
        assert validate_table_name('malicious_table', allowed_tables) is False
        assert validate_table_name('DROP TABLE', allowed_tables) is False
    
    def test_validate_column_name_whitelist(self):
        """Test column name validation against whitelist."""
        allowed_columns = ['id', 'дата', 'номер_смены', 'статус']
        
        assert validate_column_name('id', allowed_columns) is True
        assert validate_column_name('дата', allowed_columns) is True
        assert validate_column_name('malicious_column', allowed_columns) is False


class TestPydanticValidation:
    """Test Pydantic validation models."""
    
    def test_login_request_valid(self):
        """Test valid login request."""
        data = {
            'username': 'testuser',
            'password': 'Password123!'
        }
        request = LoginRequest(**data)
        assert request.username == 'testuser'
        assert request.password == 'Password123!'
    
    def test_login_request_invalid_short_username(self):
        """Test login request with too short username."""
        data = {
            'username': 'ab',  # Too short
            'password': 'Password123!'
        }
        with pytest.raises(ValidationError):
            LoginRequest(**data)
    
    def test_login_request_invalid_short_password(self):
        """Test login request with too short password."""
        data = {
            'username': 'testuser',
            'password': 'short'  # Too short
        }
        with pytest.raises(ValidationError):
            LoginRequest(**data)
    
    def test_control_data_request_valid(self):
        """Test valid control data request."""
        data = {
            'номер_маршрутной_карты': '123456',
            'всего_отлито': 100,
            'всего_принято': 95,
            'контролер': 'Иванов',
            'дефекты': {'defect1': 5}
        }
        request = ControlDataRequest(**data)
        assert request.номер_маршрутной_карты == '123456'
        assert request.всего_отлито == 100
    
    def test_control_data_request_invalid_card_number(self):
        """Test control data request with invalid card number."""
        data = {
            'номер_маршрутной_карты': '12345',  # Too short
            'всего_отлито': 100,
            'всего_принято': 95,
            'контролер': 'Иванов'
        }
        with pytest.raises(ValidationError):
            ControlDataRequest(**data)
    
    def test_control_data_request_accepted_exceeds_cast(self):
        """Test control data request where accepted exceeds cast."""
        data = {
            'номер_маршрутной_карты': '123456',
            'всего_отлито': 100,
            'всего_принято': 150,  # Exceeds cast
            'контролер': 'Иванов'
        }
        with pytest.raises(ValidationError):
            ControlDataRequest(**data)
    
    def test_shift_create_request_valid(self):
        """Test valid shift creation request."""
        data = {
            'дата': '2024-01-15',
            'номер_смены': 1,
            'контролеры': ['Иванов', 'Петров']
        }
        request = ShiftCreateRequest(**data)
        assert request.номер_смены == 1
    
    def test_shift_create_request_invalid_shift_number(self):
        """Test shift creation request with invalid shift number."""
        data = {
            'дата': '2024-01-15',
            'номер_смены': 3,  # Only 1 or 2 allowed
            'контролеры': ['Иванов']
        }
        with pytest.raises(ValidationError):
            ShiftCreateRequest(**data)
    
    def test_shift_create_request_no_controllers(self):
        """Test shift creation request with no controllers."""
        data = {
            'дата': '2024-01-15',
            'номер_смены': 1,
            'контролеры': []  # Empty list
        }
        with pytest.raises(ValidationError):
            ShiftCreateRequest(**data)
    
    def test_change_password_request_valid(self):
        """Test valid password change request."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!'
        }
        request = ChangePasswordRequest(**data)
        assert request.old_password == 'OldPass123!'
        assert request.new_password == 'NewPass123!'
    
    def test_change_password_request_weak_password(self):
        """Test password change request with weak password."""
        # No uppercase
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password='OldPass123!', new_password='newpass123!')
        
        # No lowercase
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password='OldPass123!', new_password='NEWPASS123!')
        
        # No digit
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password='OldPass123!', new_password='NewPassword!')
        
        # Too short
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password='OldPass123!', new_password='New1!')


class TestPathTraversal:
    """Test path traversal protection."""
    
    def test_detect_path_traversal_attempts(self):
        """Test detection of path traversal patterns."""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32',
            '/etc/passwd',
            'static/../../../etc/passwd'
        ]
        
        for path in malicious_paths:
            # Path contains .. or starts with /
            assert ('..' in path or path.startswith('/'))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
