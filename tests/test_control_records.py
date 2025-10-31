"""
Tests for defect entry and control record workflows.
"""
import pytest
from app.services.control_service import (
    save_control_record, get_control_records_by_shift,
    get_control_record_defects, calculate_quality_metrics
)
from app.repositories import ControlRepository
from app.models import ЗаписьКонтроля, ДефектЗаписи
from app.helpers.validators import validate_control_data


class TestControlRecordCreation:
    """Test control record creation"""
    
    def test_save_control_record_success(self, app, db_session, sample_shift, 
                                         sample_defect_type, mock_update_route_card):
        """Test successful control record creation"""
        with app.app_context():
            card_number = '123456'
            total_cast = 100
            total_accepted = 95
            controller = 'Иванов И.И.'
            defects = {sample_defect_type.id: 5}
            notes = 'Тест'
            
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number=card_number,
                total_cast=total_cast,
                total_accepted=total_accepted,
                controller=controller,
                defects=defects,
                notes=notes
            )
            
            assert record_id is not None
            record = db_session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
            assert record is not None
            assert record.номер_маршрутной_карты == card_number
            assert record.всего_отлито == total_cast
            assert record.всего_принято == total_accepted
    
    def test_save_control_record_with_multiple_defects(self, app, db_session, sample_shift,
                                                        sample_defect_type, mock_update_route_card):
        """Test control record with multiple defect types"""
        with app.app_context():
            # Create another defect type
            from app.models import КатегорияДефекта, ТипДефекта
            category = db_session.query(КатегорияДефекта).first()
            defect_type_2 = ТипДефекта(
                категория_id=category.id,
                название='Недолив'
            )
            db_session.add(defect_type_2)
            db_session.commit()
            
            defects = {
                sample_defect_type.id: 3,
                defect_type_2.id: 2
            }
            
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='654321',
                total_cast=100,
                total_accepted=95,
                controller='Петров П.П.',
                defects=defects,
                notes=''
            )
            
            assert record_id is not None
            # Check defects were saved
            defect_records = db_session.query(ДефектЗаписи).filter_by(
                запись_id=record_id
            ).all()
            assert len(defect_records) == 2
    
    def test_save_control_record_no_defects(self, app, db_session, sample_shift,
                                            mock_update_route_card):
        """Test control record with no defects (all accepted)"""
        with app.app_context():
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=50,
                total_accepted=50,
                controller='Иванов И.И.',
                defects={},
                notes='Все приняты'
            )
            
            assert record_id is not None
            record = db_session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
            assert record.всего_отлито == record.всего_принято


class TestControlDataValidation:
    """Test control data validation"""
    
    def test_validate_control_data_valid(self, app):
        """Test validation with valid data"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 95, {'Раковины': 5})
            assert len(errors) == 0
    
    def test_validate_control_data_zero_cast(self, app):
        """Test validation with zero cast"""
        with app.app_context():
            errors, warnings = validate_control_data(0, 0, {})
            assert len(errors) > 0
            assert any('больше 0' in error for error in errors)
    
    def test_validate_control_data_negative_accepted(self, app):
        """Test validation with negative accepted"""
        with app.app_context():
            errors, warnings = validate_control_data(100, -5, {})
            assert len(errors) > 0
            assert any('отрицательным' in error for error in errors)
    
    def test_validate_control_data_accepted_exceeds_cast(self, app):
        """Test validation when accepted exceeds cast"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 150, {})
            assert len(errors) > 0
            assert any('не может превышать' in error for error in errors)
    
    def test_validate_control_data_mismatch_warning(self, app):
        """Test validation warning for mismatch"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 90, {'Раковины': 5})
            # 100 - 5 = 95, but accepted is 90, so warning
            assert len(warnings) > 0
            assert any('не совпадает' in warning for warning in warnings)
    
    def test_validate_control_data_high_reject_rate(self, app):
        """Test validation warning for high reject rate"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 40, {'Раковины': 60})
            assert len(warnings) > 0
            assert any('процент брака' in warning.lower() for warning in warnings)
    
    def test_validate_control_data_negative_defect_count(self, app):
        """Test validation with negative defect count"""
        with app.app_context():
            errors, warnings = validate_control_data(100, 95, {'Раковины': -5})
            assert len(errors) > 0
            assert any('отрицательным' in error for error in errors)


class TestControlRepository:
    """Test control repository operations"""
    
    def test_get_records_by_shift(self, app, db_session, sample_shift, sample_defect_type,
                                  mock_update_route_card):
        """Test getting records by shift"""
        with app.app_context():
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='123456',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            records = get_control_records_by_shift(sample_shift.id)
            assert len(records) > 0
            assert records[0]['card_number'] == '123456'
    
    def test_check_duplicate_card(self, app, db_session, sample_shift, sample_defect_type,
                                  mock_update_route_card):
        """Test duplicate card detection"""
        with app.app_context():
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='999999',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            is_duplicate = repo.check_duplicate_card('999999', sample_shift.id)
            assert is_duplicate is True
    
    def test_check_duplicate_card_different_shift(self, app, db_session, sample_shift,
                                                   sample_defect_type, mock_update_route_card):
        """Test card not duplicate in different shift"""
        with app.app_context():
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='888888',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            # Check with different shift_id
            is_duplicate = repo.check_duplicate_card('888888', sample_shift.id + 1)
            assert is_duplicate is False


class TestQualityMetrics:
    """Test quality metrics calculation"""
    
    def test_calculate_quality_metrics(self, app, db_session, sample_shift, sample_defect_type,
                                       mock_update_route_card):
        """Test quality metrics calculation"""
        with app.app_context():
            # Create several control records
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            save_control_record(
                shift_id=sample_shift.id,
                card_number='222222',
                total_cast=100,
                total_accepted=95,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 5},
                notes=''
            )
            
            metrics = calculate_quality_metrics(sample_shift.id)
            assert metrics is not None
            assert 'quality_rate' in metrics
            assert 'total_cast' in metrics
            assert metrics['total_cast'] == 200
            assert metrics['total_accepted'] == 185
