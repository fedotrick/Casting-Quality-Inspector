# External DB Mocking - Implementation Summary

## Task Completed
Adjusted test fixtures in `tests/conftest.py` to properly mock external database calls after the service refactor.

## Changes Made

### 1. Updated `conftest.py` Fixtures

#### `mock_external_db`
- **Purpose**: Mock successful route card searches with realistic data
- **Patches**: 
  - `app.services.database_service.search_route_card_in_foundry`
  - `app.blueprints.api.search_route_card_in_foundry`
  - `app.blueprints.ui.search_route_card_in_foundry`
  - `tests.test_route_cards.search_route_card_in_foundry`
- **Behavior**:
  - Returns realistic dictionary with card-specific data
  - Validates card number format (6 digits)
  - Returns None for invalid formats
  - Supports assertions on card numbers passed

#### `mock_external_db_not_found`
- **Purpose**: Mock card not found scenario
- **Patches**: Same 4 locations as above
- **Behavior**:
  - Always returns None
  - Simulates external DB not having the card

#### `mock_update_route_card`
- **Purpose**: Mock route card status updates
- **Patches**:
  - `app.services.database_service.update_route_card_status`
  - `app.services.control_service.update_route_card_status`
- **Behavior**:
  - Always returns True (success)
  - Prevents actual writes to external DBs

## Why Multiple Patches?

After the service refactor, functions are imported into multiple modules' namespaces. When you import:
```python
from app.services.database_service import search_route_card_in_foundry
```

The function becomes a local reference in that module. To mock it everywhere, we must patch:
1. The original definition
2. Each import location where it's used

## Test Results

### Before Fix
- Tests failed because mocks only patched one location
- Real SQLite connections were attempted
- External DB files were required

### After Fix
- All route card tests pass (13/13 in test_route_cards.py)
- All relevant API tests pass (QR scan, search endpoints)
- No external DB files required (`data/foundry.db`, `data/маршрутные_карты.db`)
- No SQLite connection leaks
- Mocks properly assert card numbers

## Verification

Run tests without external DB files:
```bash
# Verify external DBs don't exist
ls data/foundry.db  # Should not exist
ls data/маршрутные_карты.db  # Should not exist

# Run route card and API tests
pytest tests/test_route_cards.py tests/test_api.py -v
```

All tests pass, confirming:
1. Mocks intercept all external DB calls
2. No real SQLite connections are made
3. Tests use realistic mock data
4. Assertions verify correct card numbers are passed

## Documentation
- Added `tests/README_MOCKING.md` with detailed mocking strategy
- Updated fixtures with comprehensive docstrings
- Each fixture clearly documents what it patches and why
