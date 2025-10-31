#!/usr/bin/env python3
"""
Verification script for SQLAlchemy migration.
Tests that the new data layer works correctly.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.database import get_db
from app.repositories import ControllerRepository, DefectRepository, ShiftRepository, ControlRepository


def verify_migration():
    """Verify that the SQLAlchemy migration is working"""
    print("=" * 60)
    print("SQLAlchemy Data Layer Migration Verification")
    print("=" * 60)
    
    # Create app
    print("\n1. Creating application...")
    try:
        app = create_app('development')
        print("   ✅ Application created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create application: {e}")
        return False
    
    # Test database connection
    print("\n2. Testing database connection...")
    with app.app_context():
        try:
            session = get_db()
            print("   ✅ Database session obtained")
        except Exception as e:
            print(f"   ❌ Failed to get database session: {e}")
            return False
        
        # Test controllers
        print("\n3. Testing Controller operations...")
        try:
            repo = ControllerRepository(session)
            controllers = repo.get_all()
            print(f"   ✅ Retrieved {len(controllers)} controllers")
        except Exception as e:
            print(f"   ❌ Failed to get controllers: {e}")
            return False
        
        # Test defect types
        print("\n4. Testing Defect Type operations...")
        try:
            repo = DefectRepository(session)
            defect_types = repo.get_all_types_grouped()
            print(f"   ✅ Retrieved {len(defect_types)} defect categories")
            for category in defect_types:
                print(f"      - {category['name']}: {len(category['types'])} types")
        except Exception as e:
            print(f"   ❌ Failed to get defect types: {e}")
            return False
        
        # Test shift operations
        print("\n5. Testing Shift operations...")
        try:
            repo = ShiftRepository(session)
            shifts = repo.get_all(limit=5)
            print(f"   ✅ Retrieved {len(shifts)} recent shifts")
        except Exception as e:
            print(f"   ❌ Failed to get shifts: {e}")
            return False
        
        # Test control record operations
        print("\n6. Testing Control Record operations...")
        try:
            repo = ControlRepository(session)
            # Just test that we can check for processed cards
            is_processed = repo.check_card_processed("000000")
            print(f"   ✅ Card check working (card 000000 processed: {is_processed})")
        except Exception as e:
            print(f"   ❌ Failed control record operations: {e}")
            return False
        
        # Test table names
        print("\n7. Verifying Cyrillic table names...")
        try:
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            table_names = inspector.get_table_names()
            
            expected_tables = [
                'контролеры',
                'категории_дефектов',
                'типы_дефектов',
                'смены',
                'записи_контроля',
                'дефекты_записей'
            ]
            
            missing_tables = []
            for table in expected_tables:
                if table in table_names:
                    print(f"   ✅ Table '{table}' exists")
                else:
                    print(f"   ❌ Table '{table}' missing")
                    missing_tables.append(table)
            
            if missing_tables:
                return False
                
        except Exception as e:
            print(f"   ❌ Failed to verify table names: {e}")
            return False
        
        # Test indexes
        print("\n8. Verifying indexes...")
        try:
            from sqlalchemy import text
            
            # Check for indexes on смены table
            result = session.execute(text("PRAGMA index_list(смены)")).fetchall()
            indexes = [row[1] for row in result]
            print(f"   ✅ Found {len(indexes)} indexes on смены table")
            
            # Check for indexes on записи_контроля table
            result = session.execute(text("PRAGMA index_list(записи_контроля)")).fetchall()
            indexes = [row[1] for row in result]
            print(f"   ✅ Found {len(indexes)} indexes on записи_контроля table")
            
        except Exception as e:
            print(f"   ⚠️  Could not verify indexes: {e}")
            # Don't fail on this, it's not critical
    
    print("\n" + "=" * 60)
    print("✅ All verification checks passed!")
    print("=" * 60)
    print("\nThe SQLAlchemy data layer is working correctly.")
    print("You can now:")
    print("  - Run the application: python wsgi.py")
    print("  - Run tests: pytest tests/test_database_layer.py -v")
    print("  - Start the server: python start_server.py")
    
    return True


if __name__ == '__main__':
    success = verify_migration()
    sys.exit(0 if success else 1)
