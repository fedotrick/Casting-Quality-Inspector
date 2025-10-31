"""
Integration tests for the complete application flow.
Tests key operations end-to-end through the service layer.
"""
import pytest
import json
from datetime import datetime

from app import create_app
from app.services.shift_service import create_shift, close_shift, get_current_shift
from app.services.control_service import save_control_record, get_control_records_by_shift
from app.services.database_service import get_all_controllers, add_controller, get_all_defect_types


@pytest.fixture(scope='function')
def app():
    """Create test application"""
    return create_app('testing')


class TestApplicationFlow:
    """Test complete application workflows"""
    
    def test_controller_workflow(self, app):
        """Test controller management workflow"""
        with app.app_context():
            # Add controller
            initial_count = len(get_all_controllers())
            controller_id = add_controller("Test Controller Integration")
            
            # Verify added
            controllers = get_all_controllers()
            assert len(controllers) == initial_count + 1
            assert any(c['имя'] == "Test Controller Integration" for c in controllers)
    
    def test_defect_types_loaded(self, app):
        """Test that defect types are loaded correctly"""
        with app.app_context():
            defect_types = get_all_defect_types()
            
            # Should have 3 categories
            assert len(defect_types) == 3
            
            # Verify category names
            category_names = {dt['name'] for dt in defect_types}
            expected_names = {'Второй сорт', 'Доработка', 'Окончательный брак'}
            assert category_names == expected_names
            
            # Verify each has types
            for category in defect_types:
                assert len(category['types']) > 0
    
    def test_complete_shift_workflow(self, app):
        """Test complete shift creation and closure workflow"""
        with app.app_context():
            # Create shift
            date = datetime(2025, 3, 15).strftime('%Y-%m-%d')
            shift_id = create_shift(date, 1, ["Controller A", "Controller B"])
            
            assert shift_id is not None
            
            # Close shift
            result = close_shift(shift_id)
            assert result is True
    
    def test_control_record_workflow(self, app):
        """Test complete control record workflow"""
        with app.app_context():
            # Create shift first
            date = datetime(2025, 4, 20).strftime('%Y-%m-%d')
            shift_id = create_shift(date, 1, ["Test Controller"])
            
            # Get defect types
            defect_types = get_all_defect_types()
            defect_type_id = defect_types[0]['types'][0]['id']
            
            # Save control record
            record_id = save_control_record(
                shift_id=shift_id,
                card_number="123456",
                total_cast=100,
                total_accepted=90,
                controller="Test Controller",
                defects={defect_type_id: 10},
                notes="Integration test record"
            )
            
            assert record_id is not None
            
            # Retrieve records
            records = get_control_records_by_shift(shift_id)
            assert len(records) == 1
            assert records[0]['card_number'] == "123456"
            assert records[0]['total_cast'] == 100
            assert records[0]['total_accepted'] == 90


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
