#!/usr/bin/env python
"""
Verification script for control metrics enhancements.
This script demonstrates all the new features in action.
"""
from app import create_app
from app.database import get_db
from app.services.control_service import save_control_record, calculate_quality_metrics
from app.services.shift_service import create_shift
from app.repositories import ControlRepository
from app.models import ЗаписьКонтроля, ДефектЗаписи, ТипДефекта
import json

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def main():
    """Run verification tests"""
    app = create_app('testing')
    
    with app.app_context():
        db_session = get_db()
        
        print_section("Setting up test data")
        
        # Create a shift
        shift_id = create_shift('2025-10-31', 1, ['Test Controller'], 'Test Supervisor')
        print(f"✓ Created shift: {shift_id}")
        
        # Get defect types
        defect_type = db_session.query(ТипДефекта).first()
        if not defect_type:
            print("✗ No defect types found")
            return
        
        # Create control records
        save_control_record(shift_id, '111111', 100, 90, 'Test Controller', {defect_type.id: 10}, '')
        save_control_record(shift_id, '222222', 100, 95, 'Test Controller', {defect_type.id: 5}, '')
        save_control_record(shift_id, '333333', 100, 85, 'Test Controller', {defect_type.id: 15}, '')
        print("✓ Created 3 control records")
        
        print_section("Test 1: Calculate metrics using shift_id (NEW)")
        metrics = calculate_quality_metrics(shift_id=shift_id)
        print(json.dumps(metrics, indent=2))
        
        assert metrics['total_cast'] == 300
        assert metrics['total_accepted'] == 270
        assert metrics['total_defects'] == 30
        assert metrics['quality_rate'] == 90.0
        assert metrics['reject_rate'] == 10.0
        print("✓ All assertions passed for shift_id calculation")
        
        print_section("Test 2: Calculate metrics using aggregate totals (BACKWARD COMPATIBLE)")
        metrics2 = calculate_quality_metrics(
            total_cast=100,
            total_accepted=95,
            defects_data={defect_type.id: 5}
        )
        print(json.dumps(metrics2, indent=2))
        
        assert metrics2['total_cast'] == 100
        assert metrics2['quality_rate'] == 95.0
        assert metrics2['reject_rate'] == 5.0
        print("✓ Backward compatibility maintained")
        
        print_section("Test 3: Enhanced repository statistics")
        repo = ControlRepository(db_session)
        stats = repo.get_shift_statistics(shift_id)
        
        print(f"Total records: {stats['total_records']}")
        print(f"Total cast: {stats['total_cast']}")
        print(f"Total accepted: {stats['total_accepted']}")
        print(f"Total defects: {stats['total_defects']}")
        print(f"Quality rate: {stats['quality_rate']}%")
        print(f"Reject rate: {stats['reject_rate']}%")
        print(f"Avg quality (legacy): {stats['avg_quality']}%")
        
        assert 'quality_rate' in stats
        assert 'reject_rate' in stats
        assert 'avg_quality' in stats  # Legacy field maintained
        print("✓ Repository statistics enhanced")
        
        print_section("Test 4: Cascade delete")
        # Create a new record for deletion
        record_id = save_control_record(shift_id, '999999', 50, 45, 'Test Controller', {defect_type.id: 5}, '')
        
        # Count defects before delete
        defects_before = db_session.query(ДефектЗаписи).filter_by(
            запись_контроля_id=record_id
        ).count()
        print(f"Defects before delete: {defects_before}")
        
        # Delete the control record
        record = db_session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
        db_session.delete(record)
        db_session.commit()
        
        # Count defects after delete
        defects_after = db_session.query(ДефектЗаписи).filter_by(
            запись_контроля_id=record_id
        ).count()
        print(f"Defects after delete: {defects_after}")
        
        assert defects_after == 0
        print("✓ Cascade delete working correctly")
        
        print_section("Test 5: API endpoint with shift_id (NEW)")
        with app.test_client() as client:
            response = client.post('/api/control/calculate',
                                  json={'shift_id': shift_id},
                                  content_type='application/json')
            
            data = response.get_json()
            print(json.dumps(data, indent=2))
            
            assert response.status_code == 200
            assert data['success'] is True
            assert data['metrics']['quality_rate'] == 90.0
            print("✓ API endpoint with shift_id works")
        
        print_section("Test 6: API endpoint backwards compatible (EXISTING)")
        with app.test_client() as client:
            response = client.post('/api/control/calculate',
                                  json={
                                      'total_cast': 100,
                                      'total_accepted': 95,
                                      'defects': {str(defect_type.id): 5}
                                  },
                                  content_type='application/json')
            
            data = response.get_json()
            print(json.dumps(data, indent=2))
            
            assert response.status_code == 200
            assert data['success'] is True
            assert data['metrics']['quality_rate'] == 95.0
            print("✓ API endpoint backwards compatibility maintained")
        
        print_section("Summary")
        print("✓ All enhancements working correctly!")
        print("✓ Backward compatibility maintained!")
        print("✓ No breaking changes!")
        print("\nFeatures verified:")
        print("  1. Calculate metrics from shift_id")
        print("  2. Calculate metrics from aggregate totals (backward compatible)")
        print("  3. Enhanced repository statistics with quality_rate and reject_rate")
        print("  4. Cascade delete for control records and defects")
        print("  5. API endpoint with shift_id parameter")
        print("  6. API endpoint backward compatibility")

if __name__ == '__main__':
    main()
