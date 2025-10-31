"""
Tests for shift creation, validation, and management workflows.
"""
import pytest
import json
from datetime import datetime, timedelta
from app.services.shift_service import (
    create_shift, get_current_shift, close_shift, 
    auto_close_expired_shifts, get_shift_statistics
)
from app.repositories import ShiftRepository
from app.models import Смена
from app.helpers.validators import validate_shift_data_extended


class TestShiftCreation:
    """Test shift creation workflows"""
    
    def test_create_shift_success(self, app, db_session, sample_controller):
        """Test successful shift creation"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            shift_number = 1
            controllers = [sample_controller.имя]
            
            shift_id = create_shift(date, shift_number, controllers)
            
            assert shift_id is not None
            shift = db_session.query(Смена).filter_by(id=shift_id).first()
            assert shift is not None
            assert shift.дата == date
            assert shift.номер_смены == shift_number
            assert shift.статус == 'активна'
    
    def test_create_shift_with_multiple_controllers(self, app, db_session):
        """Test shift creation with multiple controllers"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            shift_number = 2
            controllers = ['Иванов И.И.', 'Петров П.П.']
            
            shift_id = create_shift(date, shift_number, controllers)
            
            assert shift_id is not None
            shift = db_session.query(Смена).filter_by(id=shift_id).first()
            assert shift is not None
            controllers_list = json.loads(shift.контролеры)
            assert len(controllers_list) == 2
            assert 'Иванов И.И.' in controllers_list
    
    def test_create_shift_future_date(self, app, db_session):
        """Test shift creation for tomorrow (should be allowed)"""
        with app.app_context():
            date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            shift_number = 1
            controllers = ['Иванов И.И.']
            
            shift_id = create_shift(date, shift_number, controllers)
            assert shift_id is not None


class TestShiftValidation:
    """Test shift validation logic"""
    
    def test_validate_shift_data_valid(self, app, db_session):
        """Test validation with valid shift data"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            shift_number = 1
            controllers = ['Иванов И.И.']
            
            errors = validate_shift_data_extended(date, shift_number, controllers)
            assert len(errors) == 0
    
    def test_validate_shift_data_missing_date(self, app, db_session):
        """Test validation with missing date"""
        with app.app_context():
            errors = validate_shift_data_extended(None, 1, ['Иванов И.И.'])
            assert len(errors) > 0
            assert any('Дата смены обязательна' in error for error in errors)
    
    def test_validate_shift_data_invalid_shift_number(self, app, db_session):
        """Test validation with invalid shift number"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            errors = validate_shift_data_extended(date, 3, ['Иванов И.И.'])
            assert len(errors) > 0
            assert any('Номер смены должен быть 1 или 2' in error for error in errors)
    
    def test_validate_shift_data_no_controllers(self, app, db_session):
        """Test validation with no controllers"""
        with app.app_context():
            date = datetime.now().strftime('%Y-%m-%d')
            errors = validate_shift_data_extended(date, 1, [])
            assert len(errors) > 0
            assert any('Необходимо выбрать хотя бы одного контролера' in error for error in errors)
    
    def test_validate_shift_data_duplicate_shift(self, app, db_session, sample_shift):
        """Test validation detects duplicate active shift"""
        with app.app_context():
            date = sample_shift.дата
            shift_number = sample_shift.номер_смены
            controllers = ['Иванов И.И.']
            
            errors = validate_shift_data_extended(date, shift_number, controllers)
            assert len(errors) > 0
            assert any('уже активна' in error for error in errors)
    
    def test_validate_shift_data_far_future(self, app, db_session):
        """Test validation rejects date too far in future"""
        with app.app_context():
            date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            errors = validate_shift_data_extended(date, 1, ['Иванов И.И.'])
            assert len(errors) > 0
            assert any('не может быть в будущем' in error for error in errors)


class TestShiftClosure:
    """Test shift closure workflows"""
    
    def test_close_shift_success(self, app, db_session, sample_shift):
        """Test successful shift closure"""
        with app.app_context():
            result = close_shift(sample_shift.id)
            assert result is True
            
            # Check shift status
            shift = db_session.query(Смена).filter_by(id=sample_shift.id).first()
            assert shift.статус == 'закрыта'
            assert shift.время_окончания is not None
    
    def test_close_nonexistent_shift(self, app, db_session):
        """Test closing non-existent shift"""
        with app.app_context():
            result = close_shift(99999)
            assert result is False


class TestShiftRepository:
    """Test shift repository operations"""
    
    def test_get_active_shift(self, app, db_session, sample_shift):
        """Test getting active shift"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            shift = repo.get_active_shift(sample_shift.id)
            assert shift is not None
            assert shift.id == sample_shift.id
            assert shift.статус == 'активна'
    
    def test_check_duplicate(self, app, db_session, sample_shift):
        """Test duplicate shift detection"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            is_duplicate = repo.check_duplicate(sample_shift.дата, sample_shift.номер_смены)
            assert is_duplicate is True
    
    def test_check_duplicate_no_conflict(self, app, db_session, sample_shift):
        """Test no duplicate for different shift number"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            # sample_shift is shift 1, check for shift 2
            is_duplicate = repo.check_duplicate(sample_shift.дата, 2)
            assert is_duplicate is False
    
    def test_get_all_shifts(self, app, db_session, sample_shift):
        """Test getting all shifts"""
        with app.app_context():
            repo = ShiftRepository(db_session)
            shifts = repo.get_all()
            assert len(shifts) > 0


class TestAutoCloseShifts:
    """Test automatic shift closing"""
    
    def test_auto_close_expired_shifts(self, app, db_session):
        """Test auto-closing of expired shifts"""
        with app.app_context():
            # Create a shift from yesterday
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            shift_id = create_shift(yesterday, 1, ['Иванов И.И.'])
            
            # Run auto-close
            auto_close_expired_shifts()
            
            # Check shift was closed
            shift = db_session.query(Смена).filter_by(id=shift_id).first()
            assert shift.статус == 'закрыта'


class TestShiftStatistics:
    """Test shift statistics calculation"""
    
    def test_get_shift_statistics(self, app, db_session, sample_shift):
        """Test getting shift statistics"""
        with app.app_context():
            stats = get_shift_statistics(sample_shift.id)
            assert stats is not None
            assert 'total_records' in stats
            assert 'total_cast' in stats
            assert 'total_accepted' in stats
