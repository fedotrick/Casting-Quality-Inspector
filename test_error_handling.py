#!/usr/bin/env python3
"""
Test script to verify unified error handling and logging
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request
from utils.unified_logging import setup_logging, get_logger, log_operation
from utils.unified_error_handlers import (
    register_error_handlers, 
    ValidationError, 
    DatabaseError,
    IntegrationError,
    ResourceNotFoundError
)

# Setup logging
setup_logging(log_level="INFO", log_file=Path("logs/test_error_handling.log"))
logger = get_logger(__name__)

# Create test Flask app
app = Flask(__name__)
app.config['TESTING'] = True

# Register error handlers
register_error_handlers(app)

# Test routes
@app.route('/test/validation-error')
def test_validation_error():
    """Test validation error handling"""
    raise ValidationError(
        "Invalid card number format",
        field="card_number",
        user_message="Номер карты должен состоять из 6 цифр"
    )

@app.route('/test/database-error')
def test_database_error():
    """Test database error handling"""
    raise DatabaseError(
        "Failed to connect to database",
        details={"database": "quality_control.db"},
        user_message="Не удалось подключиться к базе данных"
    )

@app.route('/test/integration-error')
def test_integration_error():
    """Test integration error handling"""
    raise IntegrationError(
        "External API timeout",
        details={"api": "foundry_api", "timeout": 30},
        user_message="Внешняя система не отвечает"
    )

@app.route('/test/not-found')
def test_not_found():
    """Test resource not found error"""
    raise ResourceNotFoundError(
        "Route card",
        "123456",
        user_message="Маршрутная карта не найдена"
    )

@app.route('/test/unexpected-error')
def test_unexpected_error():
    """Test unexpected error handling"""
    # This should be caught by the generic exception handler
    raise RuntimeError("Something went wrong unexpectedly")

@app.route('/test/success')
def test_success():
    """Test successful request with logging"""
    from utils.unified_logging import get_correlation_id, get_request_id
    log_operation("test_success", details={"test": "value"})
    return jsonify({
        "success": True, 
        "message": "Test passed",
        "correlation_id": get_correlation_id(),
        "request_id": get_request_id()
    })

@app.route('/test/api/error')
def test_api_error():
    """Test API error response (should return JSON)"""
    raise ValidationError("API validation failed")

def run_tests():
    """Run all tests"""
    with app.test_client() as client:
        tests = [
            ("/test/validation-error", 400, "ValidationError"),
            ("/test/database-error", 500, "DatabaseError"),
            ("/test/integration-error", 503, "IntegrationError"),
            ("/test/not-found", 404, "ResourceNotFoundError"),
            ("/test/unexpected-error", 500, "UnexpectedError"),
            ("/test/success", 200, "Success"),
            ("/test/api/error", 400, "API Error"),
        ]
        
        print("=" * 60)
        print("Testing Unified Error Handling")
        print("=" * 60)
        print()
        
        passed = 0
        failed = 0
        
        for url, expected_status, test_name in tests:
            try:
                response = client.get(url)
                
                # Check status code
                if response.status_code == expected_status:
                    print(f"✅ {test_name}: Status {response.status_code}")
                    
                    # Check response format
                    if response.is_json:
                        data = response.get_json()
                        if 'correlation_id' in data and 'request_id' in data:
                            print(f"   ✅ Contains correlation_id and request_id")
                        else:
                            print(f"   ⚠️  Missing correlation_id or request_id")
                    
                    passed += 1
                else:
                    print(f"❌ {test_name}: Expected {expected_status}, got {response.status_code}")
                    failed += 1
                
            except Exception as e:
                print(f"❌ {test_name}: Exception - {e}")
                failed += 1
            
            print()
        
        print("=" * 60)
        print(f"Results: {passed} passed, {failed} failed")
        print("=" * 60)
        print()
        
        # Check log file
        log_file = Path("logs/test_error_handling.log")
        if log_file.exists():
            print("✅ Log file created")
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"   {len(lines)} log entries")
                
                # Check for correlation IDs
                has_cid = any('CID:' in line for line in lines)
                if has_cid:
                    print("   ✅ Logs contain correlation IDs")
                else:
                    print("   ⚠️  Logs missing correlation IDs")
        else:
            print("⚠️  Log file not created")
        
        print()
        return failed == 0

if __name__ == '__main__':
    logger.info("Starting error handling tests")
    success = run_tests()
    logger.info(f"Tests completed: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
