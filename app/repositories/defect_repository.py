"""
Repository for defect operations.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import and_

from ..models import КатегорияДефекта, ТипДефекта
from ..helpers.error_handlers import ОшибкаБазыДанных

logger = logging.getLogger(__name__)


class DefectRepository:
    """Repository for defect CRUD operations"""
    
    def __init__(self, session):
        self.session = session
    
    def get_all_types_grouped(self) -> List[Dict[str, Any]]:
        """Get all defect types grouped by category"""
        try:
            # Query with join to get all data
            results = self.session.query(
                КатегорияДефекта.id.label('категория_id'),
                КатегорияДефекта.название.label('категория'),
                ТипДефекта.id.label('тип_id'),
                ТипДефекта.название.label('тип')
            ).join(
                ТипДефекта, 
                КатегорияДефекта.id == ТипДефекта.категория_id
            ).filter(
                ТипДефекта.активен == 1
            ).order_by(
                КатегорияДефекта.порядок_сортировки,
                КатегорияДефекта.название,
                ТипДефекта.порядок_сортировки,
                ТипДефекта.название
            ).all()
            
            # Group by category
            grouped = {}
            for row in results:
                category_id = row.категория_id
                if category_id not in grouped:
                    grouped[category_id] = {
                        'id': category_id,
                        'name': row.категория,
                        'types': []
                    }
                if row.тип_id:
                    grouped[category_id]['types'].append({
                        'id': row.тип_id,
                        'name': row.тип
                    })
            
            return list(grouped.values())
            
        except Exception as e:
            logger.error(f"Error getting defect types: {e}")
            raise ОшибкаБазыДанных(f"Failed to get defect types: {str(e)}")
    
    def get_category_by_id(self, category_id: int) -> Optional[КатегорияДефекта]:
        """Get category by ID"""
        try:
            return self.session.query(КатегорияДефекта).filter_by(id=category_id).first()
        except Exception as e:
            logger.error(f"Error getting category: {e}")
            raise ОшибкаБазыДанных(f"Failed to get category: {str(e)}")
    
    def get_type_by_id(self, type_id: int) -> Optional[ТипДефекта]:
        """Get defect type by ID"""
        try:
            return self.session.query(ТипДефекта).filter_by(id=type_id).first()
        except Exception as e:
            logger.error(f"Error getting defect type: {e}")
            raise ОшибкаБазыДанных(f"Failed to get defect type: {str(e)}")
    
    def get_types_by_category(self, category_id: int) -> List[ТипДефекта]:
        """Get all defect types for a category"""
        try:
            return self.session.query(ТипДефекта).filter_by(
                категория_id=category_id,
                активен=1
            ).order_by(
                ТипДефекта.порядок_сортировки,
                ТипДефекта.название
            ).all()
        except Exception as e:
            logger.error(f"Error getting defect types by category: {e}")
            raise ОшибкаБазыДанных(f"Failed to get defect types: {str(e)}")
    
    def get_all_categories(self) -> List[КатегорияДефекта]:
        """Get all defect categories ordered by sort column"""
        try:
            return self.session.query(КатегорияДефекта).order_by(
                КатегорияДефекта.порядок_сортировки,
                КатегорияДефекта.название
            ).all()
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            raise ОшибкаБазыДанных(f"Failed to get all categories: {str(e)}")
    
    def get_all_types(self, active_only: bool = True) -> List[ТипДефекта]:
        """Get all defect types ordered by sort column"""
        try:
            query = self.session.query(ТипДефекта)
            if active_only:
                query = query.filter_by(активен=1)
            return query.order_by(
                ТипДефекта.порядок_сортировки,
                ТипДефекта.название
            ).all()
        except Exception as e:
            logger.error(f"Error getting all types: {e}")
            raise ОшибкаБазыДанных(f"Failed to get all types: {str(e)}")
