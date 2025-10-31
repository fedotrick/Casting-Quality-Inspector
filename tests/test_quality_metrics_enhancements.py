"""
Tests for enhanced quality metrics functionality.

This module tests the improvements to calculate_quality_metrics:
- Support for shift_id parameter to pull statistics directly
- Backwards compatibility with aggregate totals
- quality_rate and reject_rate in return payload
- Cascade delete for control records and defects
"""
import pytest
from app.services.control_service import save_control_record, calculate_quality_metrics
from app.services.shift_service import create_shift
from app.repositories import ControlRepository
from app.models import ЗаписьКонтроля, ДефектЗаписи


class TestQualityMetricsWithShiftId:
    """Test calculate_quality_metrics with shift_id parameter"""
    
    def test_calculate_metrics_from_shift_id(self, app, db_session, sample_shift,
                                             sample_defect_type, mock_update_route_card):
        """Test calculating metrics using shift_id"""
        with app.app_context():
            # Create control records
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
            
            # Calculate metrics using shift_id
            metrics = calculate_quality_metrics(shift_id=sample_shift.id)
            
            # Verify results
            assert metrics['total_cast'] == 200
            assert metrics['total_accepted'] == 185
            assert metrics['total_defects'] == 15
            assert metrics['quality_rate'] == 92.5
            assert metrics['reject_rate'] == 7.5
            assert metrics['acceptance_rate'] == 92.5  # Backwards compatibility
    
    def test_calculate_metrics_backwards_compatible(self, app, sample_defect_type):
        """Test calculating metrics using traditional aggregate totals"""
        with app.app_context():
            # Use traditional signature
            metrics = calculate_quality_metrics(
                total_cast=100,
                total_accepted=95,
                defects_data={sample_defect_type.id: 5}
            )
            
            # Verify results
            assert metrics['total_cast'] == 100
            assert metrics['total_accepted'] == 95
            assert metrics['total_defects'] == 5
            assert metrics['quality_rate'] == 95.0
            assert metrics['reject_rate'] == 5.0
            assert metrics['acceptance_rate'] == 95.0
    
    def test_calculate_metrics_empty_shift(self, app, sample_shift):
        """Test calculating metrics for shift with no records"""
        with app.app_context():
            metrics = calculate_quality_metrics(shift_id=sample_shift.id)
            
            # Should return zeros for empty shift
            assert metrics['total_cast'] == 0
            assert metrics['total_accepted'] == 0
            assert metrics['total_defects'] == 0
            assert metrics['quality_rate'] == 0.0
            assert metrics['reject_rate'] == 0.0


class TestRepositoryStatisticsEnhancements:
    """Test enhanced get_shift_statistics in ControlRepository"""
    
    def test_shift_statistics_includes_quality_rate(self, app, db_session, sample_shift,
                                                     sample_defect_type, mock_update_route_card):
        """Test that shift statistics include quality_rate"""
        with app.app_context():
            # Create a control record
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            stats = repo.get_shift_statistics(sample_shift.id)
            
            # Verify new fields exist
            assert 'quality_rate' in stats
            assert 'reject_rate' in stats
            assert 'total_defects' in stats
            # Verify backwards compatibility
            assert 'avg_quality' in stats
            
            # Verify values
            assert stats['quality_rate'] == 90.0
            assert stats['reject_rate'] == 10.0
            assert stats['avg_quality'] == 90.0
    
    def test_shift_statistics_with_multiple_records(self, app, db_session, sample_shift,
                                                    sample_defect_type, mock_update_route_card):
        """Test shift statistics with multiple control records"""
        with app.app_context():
            # Create multiple records
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=85,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 15},
                notes=''
            )
            save_control_record(
                shift_id=sample_shift.id,
                card_number='222222',
                total_cast=100,
                total_accepted=90,
                controller='Петров П.П.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            
            repo = ControlRepository(db_session)
            stats = repo.get_shift_statistics(sample_shift.id)
            
            # Verify aggregated statistics
            assert stats['total_cast'] == 200
            assert stats['total_accepted'] == 175
            assert stats['total_defects'] == 25
            assert stats['quality_rate'] == 87.5
            assert stats['reject_rate'] == 12.5


class TestCascadeDelete:
    """Test cascade delete for control records and defects"""
    
    def test_defects_cascade_deleted_with_record(self, app, db_session, sample_shift,
                                                 sample_defect_type, mock_update_route_card):
        """Test that defects are cascade deleted when control record is deleted"""
        with app.app_context():
            # Create control record with defects
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            
            # Verify defects exist
            defects_count = db_session.query(ДефектЗаписи).filter_by(
                запись_контроля_id=record_id
            ).count()
            assert defects_count > 0
            
            # Delete control record
            record = db_session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
            db_session.delete(record)
            db_session.commit()
            
            # Verify defects were cascade deleted
            defects_count_after = db_session.query(ДефектЗаписи).filter_by(
                запись_контроля_id=record_id
            ).count()
            assert defects_count_after == 0
    
    def test_multiple_defects_cascade_deleted(self, app, db_session, sample_shift,
                                              sample_defect_type, mock_update_route_card):
        """Test cascade delete with multiple defect types"""
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
            
            # Create control record with multiple defects
            record_id = save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={
                    sample_defect_type.id: 5,
                    defect_type_2.id: 5
                },
                notes=''
            )
            
            # Verify multiple defects exist
            defects_count = db_session.query(ДефектЗаписи).filter_by(
                запись_контроля_id=record_id
            ).count()
            assert defects_count == 2
            
            # Delete control record
            record = db_session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
            db_session.delete(record)
            db_session.commit()
            
            # Verify all defects were cascade deleted
            defects_count_after = db_session.query(ДефектЗаписи).filter_by(
                запись_контроля_id=record_id
            ).count()
            assert defects_count_after == 0


class TestAPIEndpointEnhancements:
    """Test API endpoint enhancements for quality metrics"""
    
    def test_api_calculate_with_shift_id(self, client, app, sample_shift,
                                        sample_defect_type, mock_update_route_card):
        """Test API endpoint with shift_id parameter"""
        with app.app_context():
            # Create control records
            save_control_record(
                shift_id=sample_shift.id,
                card_number='111111',
                total_cast=100,
                total_accepted=90,
                controller='Иванов И.И.',
                defects={sample_defect_type.id: 10},
                notes=''
            )
            
            # Call API with shift_id
            response = client.post('/api/control/calculate',
                                  json={'shift_id': sample_shift.id},
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'metrics' in data
            assert data['metrics']['quality_rate'] == 90.0
            assert data['metrics']['reject_rate'] == 10.0
    
    def test_api_calculate_backwards_compatible(self, client, app, sample_defect_type):
        """Test API endpoint with traditional parameters"""
        with app.app_context():
            # Call API with traditional parameters
            response = client.post('/api/control/calculate',
                                  json={
                                      'total_cast': 100,
                                      'total_accepted': 95,
                                      'defects': {str(sample_defect_type.id): 5}
                                  },
                                  content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['metrics']['quality_rate'] == 95.0
            assert data['metrics']['reject_rate'] == 5.0
