# Error Handling Quick Reference

## Quick Start

### 1. Import and Setup

```python
from utils.unified_logging import setup_logging, get_logger, log_operation
from utils.unified_error_handlers import (
    register_error_handlers, 
    DatabaseError, 
    ValidationError,
    IntegrationError
)

# Setup (once at app startup)
setup_logging(log_level="INFO", log_file=Path("logs/app.log"))
logger = get_logger(__name__)

# Register error handlers (Flask app)
register_error_handlers(app)
```

### 2. Raise Exceptions

```python
# Validation error
raise ValidationError("Invalid input", field="card_number")

# Database error
raise DatabaseError("Failed to save", details={"table": "shifts"})

# Integration error  
raise IntegrationError("External service unavailable")
```

### 3. Log Operations

```python
# Log an operation
log_operation("shift_created", details={"shift_id": 42})

# Log with context
logger.info("Processing request", user_id="123", card_number="456789")

# Log error with context
from utils.unified_logging import log_error_with_context
log_error_with_context(error, context={"operation": "save_shift"})
```

## Common Patterns

### API Endpoint with Error Handling

```python
@app.route('/api/shift/create', methods=['POST'])
def create_shift():
    # Just raise exceptions - handlers will catch them
    data = request.get_json()
    
    if not data:
        raise ValidationError("Request body is required")
    
    if 'date' not in data:
        raise ValidationError("Date is required", field="date")
    
    # Process...
    shift_id = save_shift(data)
    
    log_operation("shift_created", details={"shift_id": shift_id})
    
    return jsonify({"success": True, "shift_id": shift_id})
```

### Database Operation with Error Handling

```python
def save_shift(data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO shifts ...", data)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        raise DatabaseError(
            f"Failed to save shift: {str(e)}",
            details={"data": data}
        )
    finally:
        if conn:
            conn.close()
```

### External Integration with Retry

```python
from utils.external_integration_wrapper import retry_on_failure

@retry_on_failure(max_attempts=3, delay=1.0)
def call_external_api():
    # This will automatically retry on failure
    response = requests.get("https://external-api.com/data")
    if response.status_code != 200:
        raise IntegrationError("API returned error")
    return response.json()
```

## Exception Types

| Exception | Use Case | HTTP Status |
|-----------|----------|-------------|
| `ValidationError` | Invalid user input | 400 |
| `DatabaseError` | Database operations fail | 500 |
| `IntegrationError` | External service issues | 503 |
| `ResourceNotFoundError` | Resource doesn't exist | 404 |
| `AuthenticationError` | Login/auth issues | 401 |
| `AuthorizationError` | Permission denied | 403 |
| `BusinessLogicError` | Business rule violation | 400 |

## Logging Best Practices

### DO ✅

```python
# Structured logging with context
logger.info("User logged in", 
    user_id=user.id, 
    username=user.name,
    ip=request.remote_addr
)

# Log operations
log_operation("quality_control_submitted", 
    details={"card_number": "123456", "defects": 5}
)
```

### DON'T ❌

```python
# String concatenation
logger.info(f"User {user.id} logged in from {request.remote_addr}")

# Missing context
logger.info("Submitted")
```

## Correlation IDs

Every request automatically gets a `correlation_id` and `request_id`:

- Find all logs for a request: `grep "CID:abc-123" logs/app.log`
- Users can pass `X-Correlation-ID` header to link requests
- All error responses include both IDs

## Sensitive Data Protection

These fields are automatically redacted:
- password
- token
- api_key
- secret
- credential

```python
# This is safe - password will be redacted
logger.info("User update", username="admin", password="secret123")
# Logged as: ... username=admin password=***REDACTED***
```

## Migration Guide

### Old Code
```python
try:
    result = do_something()
    return jsonify({'success': True, 'data': result})
except Exception as e:
    logger.error(f"Error: {e}")
    return jsonify({'error': str(e)}), 500
```

### New Code
```python
# Just let it raise - handlers catch it
result = do_something()
return jsonify({'success': True, 'data': result})
```

## Testing

```bash
# Test unified logging
python3 -c "from utils.unified_logging import get_logger; logger = get_logger('test'); logger.info('Test message', test_field='value')"

# Check logs for correlation IDs
tail -f logs/application.log | grep -o "CID:[^]]*"
```

## Troubleshooting

**Q: Logs don't show correlation IDs**  
A: Use `get_logger(__name__)` not `logging.getLogger(__name__)`

**Q: Error not caught by handlers**  
A: Make sure `register_error_handlers(app)` is called after app creation

**Q: Sensitive data in logs**  
A: Use field names with keywords: password, token, secret, key, credential
