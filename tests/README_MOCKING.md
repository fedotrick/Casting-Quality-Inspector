# Test Mocking Strategy for External DB

## Overview

After the service refactor, the `search_route_card_in_foundry` and `update_route_card_status` functions are now centralized in `app.services.database_service`. However, due to Python's import mechanism, these functions are imported into multiple modules' namespaces.

## Call Sites Requiring Patches

### search_route_card_in_foundry
This function is imported and used in:
1. `app.services.database_service` (original definition)
2. `app.blueprints.api` (imported on line 9)
3. `app.blueprints.ui` (imported on line 8)
4. `tests.test_route_cards` (imported on line 5-7)

### update_route_card_status
This function is imported and used in:
1. `app.services.database_service` (original definition)
2. `app.services.control_service` (imported on line 10)

## Mock Fixtures in conftest.py

### mock_external_db
- **Purpose**: Mock successful route card searches
- **Behavior**: 
  - Returns realistic dictionary with card data based on card number
  - Validates card number format (must be 6 digits)
  - Returns None for invalid formats
- **Patches**: All 4 call sites listed above
- **Usage**: Tests that expect to find a card in external DB

### mock_external_db_not_found
- **Purpose**: Mock card not found scenario
- **Behavior**: Always returns None
- **Patches**: All 4 call sites listed above
- **Usage**: Tests that expect card to not be found in external DB

### mock_update_route_card
- **Purpose**: Mock route card status updates
- **Behavior**: Always returns True (success)
- **Patches**: Both call sites for update function
- **Usage**: Tests that save control records (which trigger status updates)

## Verification

All tests pass without requiring actual external DB files:
- `data/foundry.db` - not needed
- `data/маршрутные_карты.db` - not needed

The mocks provide realistic data without making actual SQLite connections to external databases.

## Assertions

Tests can assert that mocks are called with expected card numbers:
```python
mock_external_db.assert_called_once_with('123456')
```

This verifies:
1. The function was called
2. It was called with the correct card number
3. It was called exactly once
