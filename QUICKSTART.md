# Quick Start Guide - SQLAlchemy Data Layer

## ✅ Migration Complete!

The application has been successfully migrated from direct sqlite3 to SQLAlchemy.

---

## Quick Verification

Verify the migration is working:

```bash
python verify_sqlalchemy_migration.py
```

Expected output:
```
✅ All verification checks passed!
```

---

## Running the Application

### Option 1: Using WSGI (Recommended)

```bash
python wsgi.py
```

### Option 2: Using Start Script

```bash
python start_server.py
```

The application will start on `http://127.0.0.1:5005`

---

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

Expected: `17 passed`

### Database Layer Tests Only

```bash
pytest tests/test_database_layer.py -v
```

Expected: `13 passed`

### Integration Tests Only

```bash
pytest tests/test_integration.py -v
```

Expected: `4 passed`

---

## Project Structure

```
app/
├── models/              # SQLAlchemy declarative models
│   ├── base.py         # Base model class
│   ├── controller.py   # Контролёр model
│   ├── defect.py       # КатегорияДефекта, ТипДефекта models
│   ├── shift.py        # Смена model
│   └── control.py      # ЗаписьКонтроля, ДефектЗаписи models
│
├── repositories/        # Data access layer
│   ├── controller_repository.py
│   ├── defect_repository.py
│   ├── shift_repository.py
│   └── control_repository.py
│
├── database/           # Database management
│   ├── session.py      # Session factory and management
│   └── init_data.py    # Default data initialization
│
├── services/           # Business logic layer
│   ├── database_service.py   # Database operations
│   ├── shift_service.py      # Shift management
│   └── control_service.py    # Control records
│
├── blueprints/         # Flask blueprints
│   ├── api.py          # API routes
│   └── ui.py           # UI routes
│
└── helpers/            # Utility modules
    ├── validators.py
    ├── error_handlers.py
    └── logging_config.py
```

---

## Key Features

### ✅ SQLAlchemy ORM
- All queries parameterized
- Type-safe operations
- Automatic transaction management

### ✅ Repository Pattern
- Clean separation of concerns
- Easy to test and mock
- Centralized data access

### ✅ Performance Optimized
- Strategic indexes on hot paths
- Efficient joins via relationships
- Query result caching

### ✅ Cyrillic Support
- All original table names preserved
- Full Unicode support
- No schema changes required

---

## Common Operations

### Get Database Session

```python
from app.database import get_db

session = get_db()  # In Flask request context
```

### Use Repositories

```python
from app.repositories import ShiftRepository

repo = ShiftRepository(session)
shift = repo.create(date, shift_number, controllers)
```

### Use Services

```python
from app.services.shift_service import create_shift

shift_id = create_shift(date, shift_number, controllers)
```

---

## Database Information

### Tables (Cyrillic Names Preserved)

- `контролеры` - Controllers
- `категории_дефектов` - Defect categories
- `типы_дефектов` - Defect types
- `смены` - Shifts
- `записи_контроля` - Control records
- `дефекты_записей` - Record defects

### Location

- Main DB: `data/quality_control.db`
- External DBs: `foundry.db`, `маршрутные_карты.db` (unchanged)

### Indexes

- `idx_смены_статус_дата` - Shift queries
- `idx_записи_смена` - Record lookups
- `idx_записи_маршрутная_карта` - Card checks
- `idx_дефекты_запись` - Defect lookups
- `idx_дефекты_тип` - Defect type queries

---

## Documentation

- `MIGRATION_COMPLETE.md` - Migration summary
- `ACCEPTANCE_CRITERIA_CHECKLIST.md` - Acceptance criteria verification
- `docs/sqlalchemy-migration.md` - Detailed migration guide
- `docs/sqlite3-usage-summary.md` - sqlite3 usage explanation

---

## Troubleshooting

### Application won't start

1. Check Python version: `python --version` (needs 3.10+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check logs: `logs/application.log`

### Tests failing

```bash
# Clean test database
rm -f data/quality_control.db

# Run verification
python verify_sqlalchemy_migration.py

# Run tests again
pytest tests/ -v
```

### Database issues

```bash
# Analyze database structure
python analyze_db.py

# Check for duplicates
python check_duplicates.py
```

---

## Need Help?

1. Run verification: `python verify_sqlalchemy_migration.py`
2. Check logs: `logs/application.log`
3. Review docs in `docs/` directory
4. Run tests: `pytest tests/ -v`

---

**Status**: ✅ Production Ready  
**Last Updated**: 2025-10-31  
**Migration**: Complete
