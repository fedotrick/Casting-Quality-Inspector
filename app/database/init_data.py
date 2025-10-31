"""
Initialize default data in the database.
"""
import logging
from flask import current_app

from .session import get_session
from ..models import КатегорияДефекта, ТипДефекта, Контролёр

logger = logging.getLogger(__name__)


def initialize_default_data():
    """Initialize default controllers and defect types if tables are empty"""
    session = get_session()
    
    try:
        # Check if data already exists
        controllers_count = session.query(Контролёр).count()
        categories_count = session.query(КатегорияДефекта).count()
        
        if controllers_count == 0:
            logger.info("Controllers table is empty, but not adding default ones")
        
        if categories_count == 0:
            _load_defect_types(session)
        
        session.commit()
        logger.info("Default data initialization completed")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error initializing default data: {e}")
        raise
    finally:
        session.close()


def _load_defect_types(session):
    """Load defect types and categories from config"""
    try:
        defect_types = current_app.config['DEFECT_TYPES']
        
        # Create defect categories
        categories = {}
        for category_key, data in defect_types.items():
            category = КатегорияДефекта(
                название=data['name'],
                описание=f'Категория дефектов: {data["name"]}'
            )
            session.add(category)
            session.flush()  # Get the ID
            categories[category_key] = category
            logger.info(f"Created defect category: {data['name']}")
        
        # Create defect types
        for category_key, data in defect_types.items():
            category = categories[category_key]
            for defect_type_name in data['types']:
                # Check if defect type already exists for this category
                existing = session.query(ТипДефекта).filter_by(
                    категория_id=category.id,
                    название=defect_type_name
                ).first()
                
                if not existing:
                    defect_type = ТипДефекта(
                        категория_id=category.id,
                        название=defect_type_name
                    )
                    session.add(defect_type)
        
        session.flush()
        logger.info("Loaded defect types successfully")
        
    except Exception as e:
        logger.error(f"Error loading defect types: {e}")
        raise
