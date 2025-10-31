# SQLite3 Usage Summary

## Runtime Code - Intentional sqlite3 Usage

### External Database Integration (As Required)

The following files use sqlite3 **intentionally** for external database access:

#### `app/services/database_service.py`
- `get_foundry_db_connection()` - Connects to external foundry.db
- `search_route_card_in_foundry()` - Searches route cards in external DB
- `get_route_cards_db_connection()` - Connects to external маршрутные_карты.db
- `update_route_card_status()` - Updates status in external DB

**Reason**: These are **external databases** that are not part of the main application. Per requirements, external integrations (database.external_db_integration) should remain untouched.

## Utility Scripts - sqlite3 Usage

The following utility scripts use sqlite3 for direct database inspection:

1. `analyze_db.py` - Database structure analysis tool
2. `check_duplicates.py` - Duplicate record checker

**Reason**: These are standalone utility scripts for database inspection/maintenance, not runtime application code.

## Main Application Database - 100% SQLAlchemy

The main application database (`data/quality_control.db`) uses **SQLAlchemy exclusively**:

✅ All queries parameterized via SQLAlchemy ORM
✅ All CRUD operations through repositories
✅ Session management via Flask app context
✅ Transaction handling automatic
✅ Foreign key constraints enforced

### Models (app/models/)
- контролеры (Контролёр)
- категории_дефектов (КатегорияДефекта)
- типы_дефектов (ТипДефекта)
- смены (Смена)
- записи_контроля (ЗаписьКонтроля)
- дефекты_записей (ДефектЗаписи)

### Repositories (app/repositories/)
- ControllerRepository
- DefectRepository
- ShiftRepository
- ControlRepository

### No sqlite3 in:
- ❌ Models (app/models/)
- ❌ Repositories (app/repositories/)
- ❌ Core service logic
- ❌ Helpers (except external DB integration)
- ❌ Blueprints (app/blueprints/)
- ❌ Application initialization

## Verification

Run this to verify no inappropriate sqlite3 usage:
```bash
# Should only show database_service.py (external DB) and utility scripts
grep -r "import sqlite3" --include="*.py" app/ | grep -v "_old.py"
```

Expected output:
```
app/services/database_service.py:import sqlite3
```

This is correct - only for external database access.

## Summary

✅ **Acceptance Criteria Met**: All former sqlite3 calls removed from runtime code  
✅ **External Integrations**: Preserved using sqlite3 as required  
✅ **Main DB**: 100% SQLAlchemy with proper ORM and transactions  
✅ **Utility Scripts**: Can continue using sqlite3 for inspection
