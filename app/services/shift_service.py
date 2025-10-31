"""
New shift management service layer using SQLAlchemy.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import session

from ..database import get_db
from ..repositories import ShiftRepository, ControlRepository
from ..helpers.error_handlers import ОшибкаБазыДанных
from ..helpers.logging_config import log_operation

logger = logging.getLogger(__name__)


def get_current_shift() -> Optional[Dict[str, Any]]:
    """Get current active shift from session"""
    # Auto-close expired shifts before checking
    auto_close_expired_shifts()
    
    shift_id = session.get('current_shift_id')
    if not shift_id:
        return None
    
    db_session = get_db()
    repo = ShiftRepository(db_session)
    
    try:
        shift = repo.get_active_shift(shift_id)
        
        if not shift:
            # If shift is not active, clear session
            session.pop('current_shift_id', None)
            return None
        
        # Format shift object
        result = {
            'id': shift.id,
            'date': shift.дата,
            'shift_number': shift.номер_смены,
            'supervisor': shift.старший,
            'controllers': json.loads(shift.контролеры) if shift.контролеры else [],
            'start_time': shift.время_начала,
            'end_time': shift.время_окончания,
            'status': 'active' if shift.статус == 'активна' else 'closed'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting shift: {e}")
        return None


def create_shift(date: str, shift_number: int, controllers: list, supervisor: str = 'Контролеры') -> int:
    """Create new shift"""
    db_session = get_db()
    repo = ShiftRepository(db_session)
    
    try:
        shift = repo.create(date, shift_number, controllers, supervisor)
        db_session.commit()
        
        logger.info(f"Created shift {shift.id} for date {date}, shift number {shift_number}")
        return shift.id
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error creating shift: {e}")
        raise


def close_shift(shift_id: int) -> bool:
    """Close shift"""
    db_session = get_db()
    repo = ShiftRepository(db_session)
    
    try:
        result = repo.close(shift_id)
        db_session.commit()
        
        logger.info(f"Closed shift {shift_id}")
        return result
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error closing shift: {e}")
        raise


def auto_close_expired_shifts():
    """Auto-close expired shifts"""
    db_session = get_db()
    repo = ShiftRepository(db_session)
    
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        repo.auto_close_expired(current_date, current_time)
        db_session.commit()
        
        logger.info("Auto-close expired shifts completed")
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error auto-closing shifts: {e}")


def get_shift_statistics(shift_id: int) -> Optional[Dict[str, Any]]:
    """Get shift statistics"""
    db_session = get_db()
    repo = ControlRepository(db_session)
    
    try:
        stats = repo.get_shift_statistics(shift_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting shift statistics: {e}")
        return None


def get_all_shifts(limit: int = 50) -> list:
    """Get all shifts"""
    db_session = get_db()
    repo = ShiftRepository(db_session)
    
    try:
        shifts = repo.get_all(limit)
        
        result = []
        for shift in shifts:
            result.append({
                'id': shift.id,
                'date': shift.дата,
                'shift_number': shift.номер_смены,
                'supervisor': shift.старший,
                'controllers': json.loads(shift.контролеры) if shift.контролеры else [],
                'start_time': shift.время_начала,
                'end_time': shift.время_окончания,
                'status': shift.статус
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all shifts: {e}")
        return []
