"""
Repository for shift operations.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, func

from ..models import Смена
from ..helpers.error_handlers import ОшибкаБазыДанных

logger = logging.getLogger(__name__)


class ShiftRepository:
    """Repository for shift CRUD operations"""
    
    def __init__(self, session):
        self.session = session
    
    def get_by_id(self, shift_id: int) -> Optional[Смена]:
        """Get shift by ID"""
        try:
            return self.session.query(Смена).filter_by(id=shift_id).first()
        except Exception as e:
            logger.error(f"Error getting shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to get shift: {str(e)}")
    
    def get_active_shift(self, shift_id: int) -> Optional[Смена]:
        """Get active shift by ID"""
        try:
            return self.session.query(Смена).filter_by(
                id=shift_id,
                статус='активна'
            ).first()
        except Exception as e:
            logger.error(f"Error getting active shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to get active shift: {str(e)}")
    
    def check_duplicate(self, date: str, shift_number: int) -> bool:
        """Check if active shift already exists for date and shift number"""
        try:
            count = self.session.query(func.count(Смена.id)).filter(
                and_(
                    Смена.дата == date,
                    Смена.номер_смены == shift_number,
                    Смена.статус == 'активна'
                )
            ).scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Error checking duplicate shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to check duplicate shift: {str(e)}")
    
    def create(self, date: str, shift_number: int, controllers: list, 
               supervisor: str = 'Контролеры') -> Смена:
        """Create new shift"""
        import json
        
        try:
            # Check for duplicate
            if self.check_duplicate(date, shift_number):
                raise ОшибкаБазыДанных(f"Смена {shift_number} на дату {date} уже активна")
            
            start_time = datetime.now().strftime('%H:%M')
            controllers_json = json.dumps(controllers, ensure_ascii=False)
            
            shift = Смена(
                дата=date,
                номер_смены=shift_number,
                старший=supervisor,
                контролеры=controllers_json,
                время_начала=start_time,
                статус='активна'
            )
            
            self.session.add(shift)
            self.session.flush()
            logger.info(f"Created shift {shift.id} for date {date}, shift number {shift_number}")
            return shift
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating shift: {e}")
            if "уже активна" in str(e):
                raise
            raise ОшибкаБазыДанных(f"Failed to create shift: {str(e)}")
    
    def close(self, shift_id: int) -> bool:
        """Close shift"""
        try:
            shift = self.get_by_id(shift_id)
            if shift:
                end_time = datetime.now().strftime('%H:%M')
                shift.время_окончания = end_time
                shift.статус = 'закрыта'
                self.session.flush()
                logger.info(f"Closed shift {shift_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error closing shift: {e}")
            raise ОшибкаБазыДанных(f"Failed to close shift: {str(e)}")
    
    def auto_close_expired(self, current_date: str, current_time: str):
        """Auto-close expired shifts"""
        from datetime import timedelta
        
        try:
            # Close shifts from previous days
            self.session.query(Смена).filter(
                and_(
                    Смена.дата < current_date,
                    Смена.статус == 'активна'
                )
            ).update({
                'статус': 'закрыта',
                'время_окончания': current_time
            }, synchronize_session=False)
            
            # Close shift 1 if time is after 19:00
            if current_time > '19:00':
                self.session.query(Смена).filter(
                    and_(
                        Смена.дата == current_date,
                        Смена.номер_смены == 1,
                        Смена.статус == 'активна'
                    )
                ).update({
                    'статус': 'закрыта',
                    'время_окончания': '19:00'
                }, synchronize_session=False)
            
            # Close shift 2 from previous day if time is between 07:00 and 19:00
            if '07:00' < current_time < '19:00':
                yesterday = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                self.session.query(Смена).filter(
                    and_(
                        Смена.дата == yesterday,
                        Смена.номер_смены == 2,
                        Смена.статус == 'активна'
                    )
                ).update({
                    'статус': 'закрыта',
                    'время_окончания': '07:00'
                }, synchronize_session=False)
            
            self.session.flush()
            logger.info("Auto-close expired shifts completed")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error auto-closing shifts: {e}")
            raise ОшибкаБазыДанных(f"Failed to auto-close shifts: {str(e)}")
    
    def get_all(self, limit: int = 50) -> List[Смена]:
        """Get all shifts"""
        try:
            return self.session.query(Смена).order_by(
                Смена.дата.desc(),
                Смена.номер_смены.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting all shifts: {e}")
            raise ОшибкаБазыДанных(f"Failed to get shifts: {str(e)}")
    
    def get_by_date_range(self, start_date: str, end_date: str, *, status: Optional[str] = None) -> List[Смена]:
        """Get shifts by date range and optionally filter by status"""
        try:
            query = self.session.query(Смена).filter(
                and_(
                    Смена.дата >= start_date,
                    Смена.дата <= end_date
                )
            )
            if status:
                query = query.filter_by(статус=status)
            return query.order_by(
                Смена.дата.desc(),
                Смена.номер_смены.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting shifts by date range: {e}")
            raise ОшибкаБазыДанных(f"Failed to get shifts by date range: {str(e)}")
    
    def get_recent(self, limit: int = 10) -> List[Смена]:
        """Get recent shifts ordered by date descending"""
        try:
            return self.session.query(Смена).order_by(
                Смена.дата.desc(),
                Смена.номер_смены.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent shifts: {e}")
            raise ОшибкаБазыДанных(f"Failed to get recent shifts: {str(e)}")
