"""
New quality control service layer using SQLAlchemy.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_db
from ..repositories import ControlRepository
from .database_service import update_route_card_status
from ..helpers.error_handlers import ОшибкаБазыДанных
from ..helpers.logging_config import log_operation

logger = logging.getLogger(__name__)


def save_control_record(shift_id: int, card_number: str, total_cast: int, 
                        total_accepted: int, controller: str, defects: Dict[int, int],
                        notes: str = "") -> int:
    """
    Save quality control record.
    
    Args:
        shift_id: Shift ID
        card_number: Route card number
        total_cast: Total cast parts
        total_accepted: Total accepted parts
        controller: Controller name
        defects: Dictionary mapping defect_type_id to count
        notes: Optional notes
        
    Returns:
        Record ID
    """
    db_session = get_db()
    repo = ControlRepository(db_session)
    
    try:
        record = repo.save_record(
            shift_id=shift_id,
            card_number=card_number,
            total_cast=total_cast,
            total_accepted=total_accepted,
            controller=controller,
            defects=defects,
            notes=notes
        )
        
        db_session.commit()
        
        # Try to update route card status in external DB
        update_route_card_status(card_number)
        
        logger.info(f"Saved control record {record.id} for card {card_number}")
        return record.id
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error saving control record: {e}")
        raise


def get_control_records_by_shift(shift_id: int) -> list:
    """Get all control records for a shift"""
    db_session = get_db()
    repo = ControlRepository(db_session)
    
    try:
        records = repo.get_records_by_shift(shift_id)
        
        result = []
        for record in records:
            result.append({
                'id': record.id,
                'shift_id': record.смена_id,
                'card_number': record.номер_маршрутной_карты,
                'total_cast': record.всего_отлито,
                'total_accepted': record.всего_принято,
                'controller': record.контролер,
                'notes': record.заметки,
                'created': record.создана.strftime('%Y-%m-%d %H:%M:%S') if record.создана else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting control records: {e}")
        return []


def get_control_record_defects(record_id: int) -> list:
    """Get defects for a control record"""
    db_session = get_db()
    repo = ControlRepository(db_session)
    
    try:
        defects = repo.get_record_defects(record_id)
        return defects
        
    except Exception as e:
        logger.error(f"Error getting record defects: {e}")
        return []


def calculate_quality_metrics(total_cast: int, total_accepted: int, defects_data: Dict[int, int]) -> Dict[str, Any]:
    """
    Calculate quality metrics.
    
    Args:
        total_cast: Total cast parts
        total_accepted: Total accepted parts
        defects_data: Dictionary mapping defect_type_id to count
        
    Returns:
        Dictionary with quality metrics
    """
    total_defects = sum(defects_data.values())
    reject_rate = (total_defects / total_cast * 100) if total_cast > 0 else 0
    acceptance_rate = (total_accepted / total_cast * 100) if total_cast > 0 else 0
    
    return {
        'total_cast': total_cast,
        'total_accepted': total_accepted,
        'total_defects': total_defects,
        'reject_rate': round(reject_rate, 2),
        'acceptance_rate': round(acceptance_rate, 2)
    }
