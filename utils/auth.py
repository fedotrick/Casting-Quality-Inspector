"""Authentication and authorization utilities."""

import os
import hashlib
import secrets
import logging
from functools import wraps
from typing import Optional, Dict, Any
from flask import session, request, jsonify, redirect, url_for
import sqlite3
from pathlib import Path


logger = logging.getLogger(__name__)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password with salt using PBKDF2."""
    if salt is None:
        salt = secrets.token_hex(32)
    
    # Use PBKDF2 with SHA-256
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )
    
    return pwd_hash.hex(), salt


def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
    """Verify password against hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, pwd_hash)


def create_user(conn: sqlite3.Connection, username: str, password: str, role: str = 'user') -> bool:
    """Create a new user with hashed password."""
    try:
        pwd_hash, salt = hash_password(password)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO пользователи (имя_пользователя, пароль_хеш, соль, роль, активен)
            VALUES (?, ?, ?, ?, 1)
        ''', (username, pwd_hash, salt, role))
        
        conn.commit()
        logger.info(f"User {username} created successfully")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"User {username} already exists")
        return False
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return False


def authenticate_user(conn: sqlite3.Connection, username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user and return user info."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, имя_пользователя, пароль_хеш, соль, роль, активен
            FROM пользователи
            WHERE имя_пользователя = ? AND активен = 1
        ''', (username,))
        
        row = cursor.fetchone()
        
        if not row:
            logger.warning(f"User {username} not found or inactive")
            return None
        
        user_id, username_db, pwd_hash, salt, role, active = row
        
        if not verify_password(password, pwd_hash, salt):
            logger.warning(f"Invalid password for user {username}")
            return None
        
        logger.info(f"User {username} authenticated successfully")
        return {
            'id': user_id,
            'username': username_db,
            'role': role
        }
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        return None


def get_user_from_env() -> Optional[Dict[str, str]]:
    """Get default admin user from environment variables."""
    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD')
    
    if username and password:
        return {'username': username, 'password': password}
    
    return None


def init_users_table(conn: sqlite3.Connection):
    """Initialize users table."""
    try:
        cursor = conn.cursor()
        
        # Create users table with Cyrillic name
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS пользователи (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                имя_пользователя TEXT UNIQUE NOT NULL,
                пароль_хеш TEXT NOT NULL,
                соль TEXT NOT NULL,
                роль TEXT DEFAULT 'user',
                активен INTEGER DEFAULT 1,
                создан DATETIME DEFAULT CURRENT_TIMESTAMP,
                последний_вход DATETIME
            )
        ''')
        
        conn.commit()
        
        # Check if we need to create default admin
        cursor.execute('SELECT COUNT(*) FROM пользователи')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Try to get admin from environment
            admin_user = get_user_from_env()
            
            if admin_user:
                create_user(conn, admin_user['username'], admin_user['password'], role='admin')
                logger.info("Default admin user created from environment")
            else:
                # Create default admin (should be changed in production)
                create_user(conn, 'admin', 'Admin123!@#', role='admin')
                logger.warning("Default admin user created with default password - CHANGE IT!")
        
        logger.info("Users table initialized")
    except Exception as e:
        logger.error(f"Error initializing users table: {str(e)}")
        raise


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For API endpoints, return JSON
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Требуется аутентификация'}), 401
            # For UI routes, redirect to login
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Требуется аутентификация'}), 401
            return redirect(url_for('login', next=request.url))
        
        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Требуются права администратора'}), 403
            return jsonify({'success': False, 'error': 'Доступ запрещен'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def update_last_login(conn: sqlite3.Connection, user_id: int):
    """Update last login timestamp for user."""
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE пользователи
            SET последний_вход = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating last login: {str(e)}")
