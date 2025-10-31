"""
Tests for data layer repositories.
"""
import pytest
import json
from datetime import datetime
from app.repositories import (
    ShiftRepository, ControlRepository, 
    ControllerRepository, DefectRepository
)
from app.models import Контролёр, КатегорияДефекта, ТипДефекта, Смена, ЗаписьКонтроля


class TestControllerRepository:
    """Test controller repository operations"""
    
    def test_get_all_controllers(self, app, db_session):
        """Test getting all controllers"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            controllers = repo.get_all()
            
            assert isinstance(controllers, list)
            assert len(controllers) > 0
    
    def test_get_active_controllers(self, app, db_session):
        """Test getting only active controllers"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            controllers = repo.get_active()
            
            assert isinstance(controllers, list)
            # All returned controllers should be active
            for controller in controllers:
                assert controller.активен is True
    
    def test_create_controller(self, app, db_session):
        """Test creating a new controller"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            controller = repo.create('Тестов Т.Т.')
            db_session.commit()
            
            assert controller is not None
            assert controller.имя == 'Тестов Т.Т.'
            assert controller.активен is True
    
    def test_toggle_controller(self, app, db_session, sample_controller):
        """Test toggling controller active status"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            original_status = sample_controller.активен
            
            result = repo.toggle(sample_controller.id)
            db_session.commit()
            
            assert result is True
            assert sample_controller.активен != original_status
    
    def test_get_controller_by_id(self, app, db_session, sample_controller):
        """Test getting controller by ID"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            controller = repo.get_by_id(sample_controller.id)
            
            assert controller is not None
            assert controller.id == sample_controller.id


class TestDefectRepository:
    """Test defect repository operations"""
    
    def test_get_all_categories(self, app, db_session):
        """Test getting all defect categories"""
        with app.app_context():
            repo = DefectRepository(db_session)
            categories = repo.get_all_categories()
            
            assert isinstance(categories, list)
            assert len(categories) > 0
    
    def test_get_all_defect_types(self, app, db_session):
        """Test getting all defect types"""
        with app.app_context():
            repo = DefectRepository(db_session)
            defect_types = repo.get_all_types()
            
            assert isinstance(defect_types, list)
            assert len(defect_types) > 0
    
    def test_get_types_by_category(self, app, db_session):
        """Test getting defect types by category"""
        with app.app_context():
            repo = DefectRepository(db_session)
            category = db_session.query(КатегорияДефекта).first()
            
            if category:
                types = repo.get_types_by_category(category.id)
                assert isinstance(types, list)
    
    def test_get_defect_type_by_id(self, app, db_session, sample_defect_type):
        """Test getting defect type by ID"""
        with app.app_context():
            repo = DefectRepository(db_session)
            defect_type = repo.get_type_by_id(sample_defect_type.id)
            
            assert defect_type is not None
            assert defect_type.id == sample_defect_type.id


class TestShiftRepositoryAdvanced:
    """Test advanced shift repository operations"""
    
    def test_get_shifts_by_date_range(self, app, db_session, sample_shift):
        """Test getting shifts by date range"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            date_from = sample_shift.дата
            date_to = sample_shift.дата
            
            shifts = repo.get_by_date_range(date_from, date_to)
            
            assert isinstance(shifts, list)
            assert len(shifts) > 0
    
    def test_get_shift_by_id(self, app, db_session, sample_shift):
        """Test getting shift by ID"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            shift = repo.get_by_id(sample_shift.id)
            
            assert shift is not None
            assert shift.id == sample_shift.id
    
    def test_get_recent_shifts(self, app, db_session, sample_shift):
        """Test getting recent shifts"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            shifts = repo.get_recent(limit=10)
            
            assert isinstance(shifts, list)
            # Should be ordered by date/time descending


class TestControlRepositoryAdvanced:
    """Test advanced control repository operations"""
    
    def test_save_record_with_validation(self, app, db_session, sample_shift, 
                                        sample_defect_type):
        """Test saving record with proper validation"""
        with app.app_context():
            repo = ControlRepository(db_session)
            
            record = repo.save_record(
                shift_id=sample_shift.id,
                card_number='555555',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes='Test record'
            )
            db_session.commit()
            
            assert record is not None
            assert record.номер_маршрутной_карты == '555555'
    
    def test_get_record_by_id(self, app, db_session, sample_shift, sample_defect_type,
                             mock_update_route_card):
        """Test getting control record by ID"""
        with app.app_context():
            from app.services.control_service import save_control_record
            
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='444444',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            record = repo.get_by_id(record_id)
            
            assert record is not None
            assert record.id == record_id
    
    def test_get_records_count(self, app, db_session, sample_shift, sample_defect_type,
                              mock_update_route_card):
        """Test getting count of control records"""
        with app.app_context():
            from app.services.control_service import save_control_record
            
            # Create records
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            count = repo.count_by_shift(sample_shift.id)
            
            assert count > 0
    
    def test_get_records_with_defects(self, app, db_session, sample_shift, 
                                     sample_defect_type, mock_update_route_card):
        """Test getting records with their defects"""
        with app.app_context():
            from app.services.control_service import save_control_record
            
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='333333',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            defects = repo.get_record_defects(record_id)
            
            assert isinstance(defects, list)
            assert len(defects) > 0


class TestRepositoryErrorHandling:
    """Test repository error handling"""
    
    def test_get_nonexistent_controller(self, app, db_session):
        """Test getting non-existent controller"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            controller = repo.get_by_id(99999)
            
            assert controller is None
    
    def test_get_nonexistent_shift(self, app, db_session):
        """Test getting non-existent shift"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            shift = repo.get_by_id(99999)
            
            assert shift is None
    
    def test_toggle_nonexistent_controller(self, app, db_session):
        """Test toggling non-existent controller"""
        with app.app_context():
            repo = ControllerRepository(db_session)
            result = repo.toggle(99999)
            
            assert result is False
