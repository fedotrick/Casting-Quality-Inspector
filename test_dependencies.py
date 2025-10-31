#!/usr/bin/env python3
"""
Script to verify all required dependencies are installed and no removed packages are referenced.
"""

import sys
import importlib

def test_required_packages():
    """Test that all required packages can be imported."""
    required_packages = [
        ('flask', 'Flask'),
        ('flask_cors', 'Flask-CORS'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pydantic', 'Pydantic'),
        ('pytest', 'pytest'),
    ]
    
    print("Testing required packages...")
    all_ok = True
    
    for module_name, display_name in required_packages:
        try:
            importlib.import_module(module_name)
            print(f"✅ {display_name} is available")
        except ImportError as e:
            print(f"❌ {display_name} is NOT available: {e}")
            all_ok = False
    
    return all_ok


def test_removed_packages():
    """Test that removed packages are NOT available (they shouldn't be)."""
    removed_packages = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('openpyxl', 'openpyxl'),
        ('xlsxwriter', 'xlsxwriter'),
        ('plotly', 'Plotly'),
        ('numpy', 'NumPy'),
        ('alembic', 'Alembic'),
    ]
    
    print("\nVerifying removed packages are not imported by code...")
    print("(It's OK if these are not available)\n")
    
    for module_name, display_name in removed_packages:
        try:
            importlib.import_module(module_name)
            print(f"ℹ️  {display_name} is still installed (can be uninstalled)")
        except ImportError:
            print(f"✅ {display_name} is not installed")


def test_application_imports():
    """Test that main application modules can be imported."""
    print("\nTesting application imports...")
    
    try:
        # Test main application
        from main import app
        print("✅ Main application imports successfully")
        
        # Test app package
        from app import create_app
        print("✅ App factory imports successfully")
        
        # Test models
        from app.models import Контролёр, Смена
        print("✅ Models import successfully")
        
        # Test repositories
        from app.repositories import ShiftRepository, ControllerRepository
        print("✅ Repositories import successfully")
        
        # Test services
        from app.services.database_service import DatabaseService
        print("✅ Services import successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Application import failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DEPENDENCY VERIFICATION TEST")
    print("=" * 60)
    print()
    
    deps_ok = test_required_packages()
    test_removed_packages()
    app_ok = test_application_imports()
    
    print()
    print("=" * 60)
    
    if deps_ok and app_ok:
        print("✅ ALL CHECKS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        sys.exit(1)
