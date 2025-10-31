"""
Pytest configuration and fixtures for the Quality Control application.
Provides app fixture with temporary SQLite database and sample data.
"""
import pytest
import tempfile
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app import create_app
from app.database import get_db, init_db
from app.models import Смена, Контролёр, КатегорияДефекта, ТипДефекта, ЗаписьКонтроля


@pytest.fixture(scope='function')
def app():
    """
    Create and configure a test application instance with temporary database.
    Uses :memory: SQLite database with Cyrillic table names.
    """
    # Reset global database engine and session factory for clean test isolation
    import app.database.session as session_module
    session_module._engine = None
    session_module._session_factory = None
    
    app = create_app('testing')
    
    # Ensure testing configuration
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = Path(':memory:')
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize database with tables and sample data
    with app.app_context():
        init_db()
        _populate_sample_data()
    
    yield app
    
    # Cleanup happens automatically with :memory: database
    # Reset globals again to ensure clean state
    session_module._engine = None
    session_module._session_factory = None


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
        # Rollback any uncommitted changes
        session.rollback()


@pytest.fixture(scope='function')
def sample_controller(db_session):
    """Create a sample controller"""
    import uuid
    # Use unique name to avoid UNIQUE constraint violations
    unique_name = f'Тестовый Контролёр {uuid.uuid4().hex[:8]}'
    controller = Контролёр(
        имя=unique_name,
        активен=True
    )
    db_session.add(controller)
    db_session.commit()
    return controller


@pytest.fixture(scope='function')
def sample_shift(db_session, sample_controller):
    """Create a sample active shift"""
    shift = Смена(
        дата=datetime.now().strftime('%Y-%m-%d'),
        номер_смены=1,
        контролеры=json.dumps([sample_controller.имя]),
        старший='Контролеры',
        статус='активна',
        время_начала=datetime.now().strftime('%H:%M')
    )
    db_session.add(shift)
    db_session.commit()
    return shift


@pytest.fixture(scope='function')
def sample_defect_type(db_session):
    """Create a sample defect type"""
    # Get or create category
    category = db_session.query(КатегорияДефекта).filter_by(название='Окончательный брак').first()
    if not category:
        category = КатегорияДефекта(
            название='Окончательный брак',
            описание='Категория дефектов: Окончательный брак'
        )
        db_session.add(category)
        db_session.flush()
    
    # Get or create defect type
    defect_type = db_session.query(ТипДефекта).filter_by(
        категория_id=category.id,
        название='Раковины'
    ).first()
    
    if not defect_type:
        defect_type = ТипДефекта(
            категория_id=category.id,
            название='Раковины'
        )
        db_session.add(defect_type)
        db_session.commit()
    
    return defect_type


@pytest.fixture
def mock_external_db():
    """
    Mock external database integration across all call sites.
    Patches search_route_card_in_foundry in service, api, ui blueprints, and test modules.
    Returns realistic card data based on the card number passed.
    Validates card number format before returning data.
    """
    def create_card_data(card_number):
        """Create realistic card data for the given card number with validation"""
        # Validate card number format (must be 6 digits)
        if not card_number or not re.match(r'^\d{6}$', card_number):
            return None
        
        return {
            'Маршрутная_карта': card_number,
            'Номер_кластера': f'K{card_number[:3]}',
            'Учетный_номер': f'U{card_number[:3]}',
            'Температура': '1500',
            'Наименование_отливки': 'Тестовая отливка',
            'Тип_литниковой_системы': 'Тип 1'
        }
    
    # Patch all call sites after service refactor including test imports
    with patch('app.services.database_service.search_route_card_in_foundry') as mock_service, \
         patch('app.blueprints.api.search_route_card_in_foundry') as mock_api, \
         patch('app.blueprints.ui.search_route_card_in_foundry') as mock_ui, \
         patch('tests.test_route_cards.search_route_card_in_foundry') as mock_test:
        
        # Configure all mocks with side_effect to return card-specific data
        mock_service.side_effect = create_card_data
        mock_api.side_effect = create_card_data
        mock_ui.side_effect = create_card_data
        mock_test.side_effect = create_card_data
        
        # Return the test mock as the primary one for assertions (since tests import it)
        yield mock_test


@pytest.fixture
def mock_external_db_not_found():
    """
    Mock external database integration - card not found.
    Patches search_route_card_in_foundry in service, api, ui blueprints, and test modules.
    """
    # Patch all call sites after service refactor including test imports
    with patch('app.services.database_service.search_route_card_in_foundry') as mock_service, \
         patch('app.blueprints.api.search_route_card_in_foundry') as mock_api, \
         patch('app.blueprints.ui.search_route_card_in_foundry') as mock_ui, \
         patch('tests.test_route_cards.search_route_card_in_foundry') as mock_test:
        
        # Configure all mocks to return None (not found)
        mock_service.return_value = None
        mock_api.return_value = None
        mock_ui.return_value = None
        mock_test.return_value = None
        
        # Return the test mock as the primary one for assertions (since tests import it)
        yield mock_test


@pytest.fixture
def mock_update_route_card():
    """
    Mock external DB update function across all call sites.
    Patches update_route_card_status in service and control service.
    """
    # Patch all potential call sites
    with patch('app.services.database_service.update_route_card_status') as mock_service, \
         patch('app.services.control_service.update_route_card_status') as mock_control:
        
        # Configure all mocks to return True (success)
        mock_service.return_value = True
        mock_control.return_value = True
        
        # Return the service mock as the primary one for assertions
        yield mock_service


def _populate_sample_data():
    """Populate database with sample data for testing"""
    session = get_db()
    
    try:
        # Check if data already exists
        controllers_count = session.query(Контролёр).count()
        if controllers_count == 0:
            # Add sample controllers
            controllers = [
                Контролёр(имя='Иванов И.И.', активен=True),
                Контролёр(имя='Петров П.П.', активен=True),
                Контролёр(имя='Сидоров С.С.', активен=False),
            ]
            for controller in controllers:
                session.add(controller)
        
        # Defect categories and types should already be initialized by init_db
        # but let's ensure they exist
        categories_count = session.query(КатегорияДефекта).count()
        if categories_count == 0:
            # This shouldn't happen as init_db should create them
            # but as a safety net, we do nothing - init_db handles this
            pass
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        raise


@pytest.fixture
def auth_headers():
    """Return authentication headers for testing protected endpoints"""
    return {
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_control_data():
    """Sample control record data for testing"""
    return {
        'card_number': '123456',
        'total_cast': 100,
        'total_accepted': 90,
        'controller': 'Иванов И.И.',
        'defects': {},
        'notes': 'Тестовая запись'
    }
