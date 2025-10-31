"""
Tests for SQLAlchemy database layer.
Verifies key operations (shift creation/closure, defect logging, route-card updates).
"""
import pytest
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from app import create_app
from app.database import get_db, init_db
from app.models import Смена, Контролёр, ЗаписьКонтроля, ДефектЗаписи, КатегорияДефекта, ТипДефекта
from app.repositories import ShiftRepository, ControllerRepository, ControlRepository, DefectRepository


def get_unique_shift_date():
    """Generate a unique date for testing"""
    # Use a date in the past plus a random offset
    base_date = datetime(2025, 1, 1)
    offset_days = random.randint(0, 300)
    return (base_date + timedelta(days=offset_days)).strftime('%Y-%m-%d')


@pytest.fixture(scope='function')
def app():
    """Create and configure a test application instance"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def client(app):
    """Test client for the application"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Get a database session for testing"""
    with app.app_context():
        session = get_db()
        yield session
        # Don't rollback - tests use unique dates so data doesn't conflict


class TestControllerOperations:
    """Test controller CRUD operations"""
    
    def test_add_controller(self, app, db_session):
        """Test adding a new controller"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            
            controller = repo.add("Test Controller")
            db_session.commit()
            
            assert controller.id is not None
            assert controller.имя == "Test Controller"
            assert controller.активен is True
    
    def test_get_all_controllers(self, app, db_session):
        """Test getting all controllers"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            
            # Add test controllers
            repo.add("Controller 1")
            repo.add("Controller 2")
            db_session.commit()
            
            controllers = repo.get_all(active_only=True)
            assert len(controllers) >= 2
    
    def test_toggle_controller(self, app, db_session):
        """Test toggling controller active status"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            
            controller = repo.add("Toggle Test")
            db_session.commit()
            
            initial_status = controller.активен
            repo.toggle_active(controller.id)
            db_session.commit()
            
            updated = repo.get_by_id(controller.id)
            assert updated.активен != initial_status


class TestDefectOperations:
    """Test defect type operations"""
    
    def test_get_defect_types_grouped(self, app, db_session):
        """Test getting defect types grouped by category"""
        with app.app_context():
            repo = DefectRepository(db_session)
            
            grouped = repo.get_all_types_grouped()
            assert isinstance(grouped, list)
            
            # Should have categories from config
            assert len(grouped) > 0
            
            # Each group should have structure
            if grouped:
                group = grouped[0]
                assert 'id' in group
                assert 'name' in group
                assert 'types' in group


class TestShiftOperations:
    """Test shift CRUD operations"""
    
    def test_create_shift(self, app, db_session):
        """Test creating a new shift"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            
            date = get_unique_shift_date()
            controllers = ["Controller 1", "Controller 2"]
            
            shift = repo.create(date, 1, controllers)
            db_session.commit()
            
            assert shift.id is not None
            assert shift.дата == date
            assert shift.номер_смены == 1
            assert shift.статус == 'активна'
            assert json.loads(shift.контролеры) == controllers
    
    def test_duplicate_shift_prevention(self, app, db_session):
        """Test that duplicate shifts are prevented"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            
            date = get_unique_shift_date()
            controllers = ["Controller 1"]
            
            # Create first shift
            repo.create(date, 1, controllers)
            db_session.commit()
            
            # Try to create duplicate
            from app.helpers.error_handlers import ОшибкаБазыДанных
            with pytest.raises(ОшибкаБазыДанных):
                repo.create(date, 1, controllers)
    
    def test_close_shift(self, app, db_session):
        """Test closing a shift"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            
            date = get_unique_shift_date()
            controllers = ["Controller 1"]
            
            shift = repo.create(date, 2, controllers)
            db_session.commit()
            
            result = repo.close(shift.id)
            db_session.commit()
            
            assert result is True
            
            closed_shift = repo.get_by_id(shift.id)
            assert closed_shift.статус == 'закрыта'
            assert closed_shift.время_окончания is not None


class TestControlRecordOperations:
    """Test control record operations"""
    
    def test_save_control_record(self, app, db_session):
        """Test saving a control record with defects"""
        with app.app_context():
            # Create test shift
            shift_repo = ShiftRepository(db_session)
            date = get_unique_shift_date()
            shift = shift_repo.create(date, 1, ["Test Controller"])
            db_session.commit()
            
            # Get defect type
            defect_repo = DefectRepository(db_session)
            types_grouped = defect_repo.get_all_types_grouped()
            assert len(types_grouped) > 0
            defect_type_id = types_grouped[0]['types'][0]['id']
            
            # Save control record
            control_repo = ControlRepository(db_session)
            record = control_repo.save_record(
                shift_id=shift.id,
                card_number="123456",
                total_cast=100,
                total_accepted=90,
                controller="Test Controller",
                defects={defect_type_id: 10},
                notes="Test record"
            )
            db_session.commit()
            
            assert record.id is not None
            assert record.номер_маршрутной_карты == "123456"
            assert record.всего_отлито == 100
            assert record.всего_принято == 90
    
    def test_check_card_processed(self, app, db_session):
        """Test checking if card already processed"""
        with app.app_context():
            # Create test shift
            shift_repo = ShiftRepository(db_session)
            date = get_unique_shift_date()
            shift = shift_repo.create(date, 1, ["Test Controller"])
            db_session.commit()
            
            control_repo = ControlRepository(db_session)
            
            # Should not be processed yet
            assert control_repo.check_card_processed("999999") is False
            
            # Save a record
            control_repo.save_record(
                shift_id=shift.id,
                card_number="999999",
                total_cast=50,
                total_accepted=45,
                controller="Test Controller",
                defects={},
                notes=""
            )
            db_session.commit()
            
            # Now should be processed
            assert control_repo.check_card_processed("999999") is True
    
    def test_get_shift_statistics(self, app, db_session):
        """Test getting shift statistics"""
        with app.app_context():
            # Create test shift
            shift_repo = ShiftRepository(db_session)
            date = get_unique_shift_date()
            shift = shift_repo.create(date, 1, ["Test Controller"])
            db_session.commit()
            
            # Get defect type
            defect_repo = DefectRepository(db_session)
            types_grouped = defect_repo.get_all_types_grouped()
            defect_type_id = types_grouped[0]['types'][0]['id']
            
            # Add some records
            control_repo = ControlRepository(db_session)
            control_repo.save_record(
                shift_id=shift.id,
                card_number="111111",
                total_cast=100,
                total_accepted=90,
                controller="Test Controller",
                defects={defect_type_id: 10}
            )
            control_repo.save_record(
                shift_id=shift.id,
                card_number="222222",
                total_cast=50,
                total_accepted=48,
                controller="Test Controller",
                defects={defect_type_id: 2}
            )
            db_session.commit()
            
            # Get statistics
            stats = control_repo.get_shift_statistics(shift.id)
            
            assert stats['total_records'] == 2
            assert stats['total_cast'] == 150
            assert stats['total_accepted'] == 138
            assert 'avg_quality' in stats
            assert 'defects' in stats


class TestDatabaseIntegrity:
    """Test database integrity and constraints"""
    
    def test_foreign_key_constraints(self, app, db_session):
        """Test that foreign key constraints are enforced"""
        with app.app_context():
            # Try to create a control record with invalid shift_id
            record = ЗаписьКонтроля(
                смена_id=99999,  # Non-existent shift
                номер_маршрутной_карты="123456",
                всего_отлито=100,
                всего_принято=90,
                контролер="Test"
            )
            db_session.add(record)
            
            # This should fail due to foreign key constraint
            from sqlalchemy.exc import IntegrityError
            with pytest.raises(IntegrityError):
                db_session.commit()
            
            db_session.rollback()
    
    def test_unique_constraints(self, app, db_session):
        """Test unique constraints"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            
            # Add first controller
            repo.add("Unique Test")
            db_session.commit()
            
            # Try to add duplicate
            from app.helpers.error_handlers import ОшибкаБазыДанных
            with pytest.raises(ОшибкаБазыДанных):
                repo.add("Unique Test")


class TestCyrillicTableNames:
    """Test that Cyrillic table names are preserved"""
    
    def test_table_names_are_cyrillic(self, app, db_session):
        """Verify that table names use Cyrillic characters"""
        with app.app_context():
            from sqlalchemy import inspect
            
            inspector = inspect(db_session.bind)
            table_names = inspector.get_table_names()
            
            # Check for expected Cyrillic table names
            expected_tables = [
                'контролеры',
                'категории_дефектов',
                'типы_дефектов',
                'смены',
                'записи_контроля',
                'дефекты_записей'
            ]
            
            for table in expected_tables:
                assert table in table_names, f"Table '{table}' not found in database"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
