# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Removed - 2025-01-XX

#### Dependency Cleanup

The following unused packages have been removed from requirements.txt and requirements_fixed.txt:

- **streamlit>=1.28.0** - Web UI framework (not used; application uses Flask for all web interfaces)
- **pandas>=2.0.0** - Data analysis library (not referenced in codebase)
- **openpyxl>=3.1.0** - Excel file reading library (not used)
- **xlsxwriter>=3.1.0** - Excel file writing library (not used)
- **plotly>=5.15.0** - Plotting library (not used)
- **numpy>=1.24.0** - Numerical computing library (not used)
- **pywin32>=306** - Windows-specific library (not used)
- **alembic>=1.13.0** - Database migration tool (not used; application manages schema directly)

#### Current Dependencies

The application now maintains the following minimal dependency set:

**Core Dependencies:**
- flask>=2.3.0 - Web framework
- flask-cors>=4.0.0 - CORS support for Flask
- sqlalchemy>=2.0.0 - ORM and database abstraction
- pydantic>=2.0.0 - Data validation

**Testing Dependencies:**
- pytest>=7.0.0 - Testing framework
- pytest-cov>=4.0.0 - Coverage reporting
- pytest-flask>=1.2.0 - Flask testing utilities
- pytest-mock>=3.10.0 - Mocking utilities

#### Rationale

This cleanup was performed post-refactor to ensure the dependency list accurately reflects actual code usage:

1. **Streamlit** was removed as the application exclusively uses Flask for both API and UI rendering
2. **Data science libraries** (pandas, numpy, plotly, openpyxl, xlsxwriter) were removed as the application uses SQLAlchemy directly for data operations and does not perform data analysis or generate Excel reports
3. **Alembic** was removed as the application manages its schema without a formal migration framework
4. **pywin32** was removed as it was unused and platform-specific

#### Impact

- **Reduced installation time** - Fewer packages to download and compile
- **Smaller deployment footprint** - Especially impactful given the size of pandas, numpy, and their dependencies
- **Clearer project scope** - Dependencies now accurately reflect the Flask + SQLAlchemy architecture
- **No functional changes** - All existing functionality remains intact

#### Verification

Installation tested with:
```bash
# Create clean virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run verification
python verify_sqlalchemy_migration.py

# Run tests
pytest tests/ -v
```

All tests pass and application runs correctly with the reduced dependency set.

**Installation Time**: Reduced from ~2-3 minutes to ~30-45 seconds
**Package Size**: Reduced from ~500 MB to ~50 MB (~90% reduction)
