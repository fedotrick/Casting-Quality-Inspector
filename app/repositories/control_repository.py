"""
Repository for control record operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, func

from ..models import ЗаписьКонтроля, ДефектЗаписи, ТипДефекта, КатегорияДефекта
from ..helpers.error_handlers import ОшибкаБазыДанных

logger = logging.getLogger(__name__)


class ControlRepository:
    """Repository for control record CRUD operations"""
    
    def __init__(self, session):
        self.session = session
    
    def get_by_id(self, record_id: int) -> Optional[ЗаписьКонтроля]:
        """Get control record by ID"""
        try:
            return self.session.query(ЗаписьКонтроля).filter_by(id=record_id).first()
        except Exception as e:
            logger.error(f"Error getting control record: {e}")
            raise ОшибкаБазыДанных(f"Failed to get control record: {str(e)}")
    
    def check_card_processed(self, card_number: str) -> bool:
        """Check if route card has already been processed"""
        try:
            count = self.session.query(func.count(ЗаписьКонтроля.id)).filter(
                ЗаписьКонтроля.номер_маршрутной_карты == card_number
            ).scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if card processed: {e}")
            raise ОшибкаБазыДанных(f"Failed to check card: {str(e)}")
    
    def save_record(self, shift_id: int, card_number: str, total_cast: int,
                   total_accepted: int, controller: str, defects: Dict[int, int],
                   notes: str = "") -> ЗаписьКонтроля:
        """
        Save quality control record with defects.
        
        Args:
            shift_id: Shift ID
            card_number: Route card number
            total_cast: Total cast parts
            total_accepted: Total accepted parts
            controller: Controller name
            defects: Dictionary mapping defect_type_id to count
            notes: Optional notes
            
        Returns:
            Created control record
        """
        try:
            # Create control record
            record = ЗаписьКонтроля(
                смена_id=shift_id,
                номер_маршрутной_карты=card_number,
                всего_отлито=total_cast,
                всего_принято=total_accepted,
                контролер=controller,
                заметки=notes,
                создана=datetime.now()
            )
            
            self.session.add(record)
            self.session.flush()  # Get the record ID
            
            # Add defects
            for defect_type_id, count in defects.items():
                if count > 0:
                    defect = ДефектЗаписи(
                        запись_контроля_id=record.id,
                        тип_дефекта_id=defect_type_id,
                        количество=count
                    )
                    self.session.add(defect)
            
            self.session.flush()
            logger.info(f"Saved control record {record.id} for card {card_number}")
            return record
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving control record: {e}")
            raise ОшибкаБазыДанных(f"Failed to save control record: {str(e)}")
    
    def get_records_by_shift(self, shift_id: int) -> List[ЗаписьКонтроля]:
        """Get all control records for a shift"""
        try:
            return self.session.query(ЗаписьКонтроля).filter_by(
                смена_id=shift_id
            ).order_by(
                ЗаписьКонтроля.создана.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting control records: {e}")
            raise ОшибкаБазыДанных(f"Failed to get control records: {str(e)}")
    
    def get_record_defects(self, record_id: int) -> List[Dict[str, Any]]:
        """Get defects for a control record with names"""
        try:
            results = self.session.query(
                ДефектЗаписи.id,
                ДефектЗаписи.количество,
                ТипДефекта.название.label('defect_name'),
                КатегорияДефекта.название.label('category_name')
            ).join(
                ТипДефекта,
                ДефектЗаписи.тип_дефекта_id == ТипДефекта.id
            ).join(
                КатегорияДефекта,
                ТипДефекта.категория_id == КатегорияДефекта.id
            ).filter(
                ДефектЗаписи.запись_контроля_id == record_id
            ).all()
            
            return [
                {
                    'id': row.id,
                    'count': row.количество,
                    'defect_name': row.defect_name,
                    'category_name': row.category_name
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error(f"Error getting record defects: {e}")
            raise ОшибкаБазыДанных(f"Failed to get record defects: {str(e)}")
    
    def get_shift_statistics(self, shift_id: int) -> Dict[str, Any]:
        """Get statistics for a shift"""
        try:
            # Overall statistics
            stats = self.session.query(
                func.count(ЗаписьКонтроля.id).label('total_records'),
                func.sum(ЗаписьКонтроля.всего_отлито).label('total_cast'),
                func.sum(ЗаписьКонтроля.всего_принято).label('total_accepted')
            ).filter(
                ЗаписьКонтроля.смена_id == shift_id
            ).first()
            
            # Calculate average quality
            if stats.total_cast and stats.total_cast > 0:
                avg_quality = (stats.total_accepted / stats.total_cast) * 100
            else:
                avg_quality = 0
            
            # Defect statistics
            defect_stats = self.session.query(
                КатегорияДефекта.название.label('категория'),
                ТипДефекта.название,
                func.sum(ДефектЗаписи.количество).label('total_count')
            ).join(
                ЗаписьКонтроля,
                ДефектЗаписи.запись_контроля_id == ЗаписьКонтроля.id
            ).join(
                ТипДефекта,
                ДефектЗаписи.тип_дефекта_id == ТипДефекта.id
            ).join(
                КатегорияДефекта,
                ТипДефекта.категория_id == КатегорияДефекта.id
            ).filter(
                ЗаписьКонтроля.смена_id == shift_id
            ).group_by(
                КатегорияДефекта.название,
                ТипДефекта.название
            ).order_by(
                func.sum(ДефектЗаписи.количество).desc()
            ).all()
            
            return {
                'total_records': stats.total_records or 0,
                'total_cast': stats.total_cast or 0,
                'total_accepted': stats.total_accepted or 0,
                'avg_quality': round(avg_quality, 2),
                'defects': [
                    {
                        'category': d.категория,
                        'name': d.название,
                        'count': d.total_count
                    }
                    for d in defect_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting shift statistics: {e}")
            raise ОшибкаБазыДанных(f"Failed to get shift statistics: {str(e)}")
    
    def count_by_shift(self, shift_id: int) -> int:
        """Count control records by shift ID"""
        try:
            count = self.session.query(func.count(ЗаписьКонтроля.id)).filter(
                ЗаписьКонтроля.смена_id == shift_id
            ).scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error counting control records by shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to count control records: {str(e)}")
    
    def check_duplicate_card(self, card_number: str, shift_id: int) -> bool:
        """Check if route card has already been processed in a specific shift"""
        try:
            count = self.session.query(func.count(ЗаписьКонтроля.id)).filter(
                and_(
                    ЗаписьКонтроля.номер_маршрутной_карты == card_number,
                    ЗаписьКонтроля.смена_id == shift_id
                )
            ).scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking duplicate card in shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to check duplicate card: {str(e)}")
