# Unified Error Handling and Logging Strategy

This document describes the unified error handling and logging strategy implemented in the quality control system.

## Overview

The system implements a comprehensive error handling and logging infrastructure with the following key features:

- **Structured logging** with correlation IDs and request IDs for request tracing
- **Custom exception hierarchy** for different error types
- **Centralized Flask error handlers** that return consistent JSON/HTML responses
- **Sensitive data sanitization** to prevent leaking credentials in logs
- **Retry logic** for external integrations
- **Standardized error responses** for both API and UI

## Architecture

### Core Modules

#### 1. `utils/unified_logging.py`

Provides structured logging with correlation tracking:

- **Correlation IDs**: Unique IDs that track a request through the entire system
- **Request IDs**: Unique IDs for each HTTP request
- **Structured context**: All logs include relevant context (user, IP, request path, etc.)
- **Sensitive data sanitization**: Automatically redacts passwords, tokens, and API keys
- **Multiple formatters**: Human-readable and JSON formats

**Key Functions:**
```python
from utils.unified_logging import setup_logging, get_logger, log_operation, log_user_action

# Setup logging (do this once at app startup)
setup_logging(log_level="INFO", log_file=Path("logs/app.log"))

# Get a logger
logger = get_logger(__name__)

# Log with structured context
logger.info("User logged in", user_id="123", username="admin")

# Log operations
log_operation("create_shift", details={"shift_id": 42, "date": "2024-01-01"})

# Log user actions
log_user_action("submit_quality_control", user_id="123", details={"card_number": "123456"})
```

#### 2. `utils/unified_error_handlers.py`

Provides custom exceptions and Flask error handlers:

**Custom Exception Hierarchy:**

```
QualityControlError (base)
├── DatabaseError - Database operation errors
├── IntegrationError - External system integration errors
├── ValidationError - Input validation errors
├── AuthenticationError - Authentication errors
├── AuthorizationError - Authorization/permission errors
├── ResourceNotFoundError - Resource not found errors
└── BusinessLogicError - Business rule violation errors
```

**Creating Custom Errors:**
```python
from utils.unified_error_handlers import DatabaseError, ValidationError

# Raise a validation error
raise ValidationError(
    "Invalid route card number",
    field="card_number",
    user_message="Номер маршрутной карты должен состоять из 6 цифр"
)

# Raise a database error
raise DatabaseError(
    f"Failed to insert record: {str(e)}",
    details={"table": "shifts", "operation": "insert"},
    user_message="Ошибка при сохранении данных смены"
)
```

**Registering Error Handlers:**
```python
from utils.unified_error_handlers import register_error_handlers

# In your Flask app initialization
register_error_handlers(app)
```

This automatically handles:
- HTTP errors (404, 403, 401, 500)
- All custom exceptions
- Unexpected exceptions
- Returns appropriate JSON for API routes or HTML for web pages

#### 3. `utils/external_integration_wrapper.py`

Provides retry logic for external integrations:

**Key Features:**
- Automatic retry with exponential backoff
- Proper error handling and logging
- Context managers for database connections

**Usage:**
```python
from utils.external_integration_wrapper import (
    EnhancedExternalDBIntegration,
    retry_on_failure
)

# Use the enhanced integration
integration = EnhancedExternalDBIntegration(
    foundry_db_path=Path("data/foundry.db"),
    route_cards_db_path=Path("data/route_cards.db")
)

# Search with automatic retries
result = integration.search_route_card("123456")

# Update with automatic retries
success = integration.update_route_card_status("123456", "completed")

# Add retry to your own functions
@retry_on_failure(max_attempts=3, delay=1.0, backoff=2.0)
def my_integration_function():
    # Your code here
    pass
```

## Best Practices

### 1. Use Structured Logging

**DO:**
```python
logger.info("Quality control submitted", 
    card_number=card_number,
    total_cast=100,
    total_accepted=95
)
```

**DON'T:**
```python
logger.info(f"Quality control submitted: {card_number}, cast={total_cast}, accepted={total_accepted}")
```

### 2. Use Custom Exceptions

**DO:**
```python
if not card_number:
    raise ValidationError("Card number is required", field="card_number")
```

**DON'T:**
```python
if not card_number:
    return jsonify({'error': 'Card number is required'}), 400
```

### 3. Let Error Handlers Handle Errors

**DO:**
```python
@app.route('/api/route-card/<card_number>')
def get_route_card(card_number):
    # Just raise exceptions - error handlers will catch them
    card = search_route_card(card_number)
    if not card:
        raise ResourceNotFoundError("Route card", card_number)
    return jsonify(card)
```

**DON'T:**
```python
@app.route('/api/route-card/<card_number>')
def get_route_card(card_number):
    try:
        card = search_route_card(card_number)
        if not card:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(card)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 4. Use Error Boundaries for Background Tasks

**DO:**
```python
from utils.unified_error_handlers import error_boundary

@error_boundary(default_return=None, log_level='error')
def background_cleanup_task():
    # This will catch and log all errors
    # and return None on failure
    cleanup_old_sessions()
```

### 5. Log Operations, Not Just Errors

```python
# Log important operations
log_operation("shift_created", details={
    "shift_id": shift.id,
    "date": shift.date,
    "controllers": [c.id for c in controllers]
})

# Log user actions
log_user_action("quality_control_submitted", details={
    "card_number": card_number,
    "defects_count": len(defects)
})
```

## Correlation ID Usage

Correlation IDs help track a request through the entire system:

1. **Automatic generation**: Each request gets a correlation ID automatically
2. **Header support**: Clients can pass `X-Correlation-ID` header to link requests
3. **Response inclusion**: All error responses include `correlation_id` and `request_id`
4. **Log inclusion**: All logs include both IDs

Example log output:
```
2024-01-15T10:30:45Z - app.routes - INFO - [CID:abc-123-def] [RID:xyz-456-uvw] - OPERATION: shift_created
```

Example error response:
```json
{
  "success": false,
  "error": "Маршрутная карта не найдена",
  "correlation_id": "abc-123-def",
  "request_id": "xyz-456-uvw"
}
```

## Sensitive Data Protection

The logging system automatically sanitizes:

- Password fields
- Token fields
- API keys
- Secret fields
- Any field with these keywords in the name

Example:
```python
# This data
logger.info("User login", username="admin", password="secret123", api_key="key_abc")

# Is logged as
# User login username=admin password=***REDACTED*** api_key=***REDACTED***
```

## Error Response Format

### API Responses (JSON)

All error responses follow this format:

```json
{
  "success": false,
  "error": "User-friendly error message in Russian",
  "correlation_id": "unique-correlation-id",
  "request_id": "unique-request-id",
  "details": {
    // Optional: Additional context (only in debug mode)
  }
}
```

### Web Responses (HTML)

Error pages include:
- User-friendly error message
- Appropriate icon and styling
- Correlation ID and Request ID for support
- "Home" and "Back" buttons

## Migration from Old Code

### Old Error Handling
```python
try:
    result = do_something()
    return jsonify({'success': True, 'data': result})
except Exception as e:
    logger.error(f"Error: {e}")
    return jsonify({'success': False, 'error': str(e)}), 500
```

### New Error Handling
```python
# Just let it raise - error handlers will catch it
result = do_something()
return jsonify({'success': True, 'data': result})
```

### Old Logging
```python
logger.info(f"User {user_id} created shift {shift_id}")
```

### New Logging
```python
log_operation("shift_created", details={
    "user_id": user_id,
    "shift_id": shift_id
})
```

## Testing Error Handling

### Test Different Error Types

```python
# Test validation error
raise ValidationError("Test validation")

# Test database error
raise DatabaseError("Test database error")

# Test integration error
raise IntegrationError("Test integration error")

# Test 404
raise ResourceNotFoundError("Test resource", "123")
```

### Verify Error Responses

Check that:
1. JSON responses include `correlation_id` and `request_id`
2. HTML error pages are user-friendly
3. Logs contain structured context
4. Sensitive data is redacted

## Configuration

### Logging Configuration

```python
from utils.unified_logging import setup_logging
from pathlib import Path

# Basic setup
setup_logging(log_level="INFO", log_file=Path("logs/app.log"))

# JSON format for production
setup_logging(
    log_level="INFO",
    log_file=Path("logs/app.log"),
    use_json_format=True  # Structured JSON logs
)

# Debug mode
setup_logging(log_level="DEBUG", log_file=Path("logs/debug.log"))
```

### External Integration Configuration

```python
from utils.external_integration_wrapper import configure_external_integration
from pathlib import Path

configure_external_integration(
    foundry_db_path=Path("data/foundry.db"),
    route_cards_db_path=Path("data/route_cards.db")
)
```

## Backward Compatibility

For backward compatibility, the old exception names are still available:

```python
# Old names (Cyrillic)
from utils.unified_error_handlers import (
    ОшибкаБазыДанных,  # = DatabaseError
    ОшибкаИнтеграции,  # = IntegrationError
    ОшибкаВалидации,   # = ValidationError
)
```

## Troubleshooting

### Finding Request in Logs

Use correlation ID to find all logs related to a request:

```bash
grep "CID:abc-123-def" logs/app.log
```

### Understanding Error Chain

Logs show the complete error context:
1. Initial operation logged
2. Any retries attempted
3. Final error with full context

### Common Issues

**Issue**: Logs don't show correlation IDs
**Solution**: Make sure you're using `get_logger(__name__)` not `logging.getLogger(__name__)`

**Issue**: Sensitive data appears in logs
**Solution**: Check that field names contain keywords like "password", "token", "secret", or "key"

**Issue**: Error not caught by handlers
**Solution**: Make sure you've called `register_error_handlers(app)` during app initialization

## Summary

The unified error handling and logging strategy provides:

✅ Consistent error responses across the application
✅ Request tracing with correlation IDs
✅ Automatic retry for external integrations
✅ Sensitive data protection
✅ Structured logging for easy debugging
✅ User-friendly error messages
✅ Comprehensive error context for troubleshooting

By following this strategy, the application maintains high code quality, improves debuggability, and provides a better user experience.
