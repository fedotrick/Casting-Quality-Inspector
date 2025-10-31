"""
Shift management service layer.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import session

from .database_service import get_db_connection
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
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM смены WHERE id = ? AND статус = "активна"', (shift_id,))
        shift_row = cursor.fetchone()
        
        if not shift_row:
            # If shift is not active, clear session
            session.pop('current_shift_id', None)
            conn.close()
            return None
        
        # Format shift object as in original
        result = {
            'id': shift_row[0],
            'date': shift_row[1],
            'shift_number': shift_row[2],
            'supervisor': shift_row[3],
            'controllers': json.loads(shift_row[4]) if shift_row[4] else [],
            'start_time': shift_row[5],
            'end_time': shift_row[6],
            'status': 'active' if shift_row[7] == 'активна' else 'closed'
        }
        conn.close()
        
        if result:
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting shift: {e}")
        if conn:
            conn.close()
        return None


def create_shift(date: str, shift_number: int, controllers: list, supervisor: str = 'Контролеры') -> int:
    """Create new shift"""
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        
        # Check for duplicate active shift
        cursor.execute('''
            SELECT COUNT(*) FROM смены
            WHERE дата = ? AND номер_смены = ? AND статус = 'активна'
        ''', (date, shift_number))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise ОшибкаБазыДанных(f"Смена {shift_number} на дату {date} уже активна")
        
        # Create shift
        start_time = datetime.now().strftime('%H:%M')
        controllers_json = json.dumps(controllers, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO смены (дата, номер_смены, старший, контролеры, время_начала, статус)
            VALUES (?, ?, ?, ?, ?, 'активна')
        ''', (date, shift_number, supervisor, controllers_json, start_time))
        
        shift_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Created shift {shift_id} for date {date}, shift number {shift_number}")
        return shift_id
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error creating shift: {e}")
        raise ОшибкаБазыДанных(f"Failed to create shift: {str(e)}")


def close_shift(shift_id: int) -> bool:
    """Close shift"""
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        end_time = datetime.now().strftime('%H:%M')
        
        cursor.execute('''
            UPDATE смены
            SET время_окончания = ?, статус = 'закрыта'
            WHERE id = ?
        ''', (end_time, shift_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Closed shift {shift_id}")
        return True
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error closing shift: {e}")
        raise ОшибкаБазыДанных(f"Failed to close shift: {str(e)}")


def auto_close_expired_shifts():
    """Auto-close expired shifts"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        # Close shifts from previous days
        cursor.execute('''
            UPDATE смены 
            SET статус = 'закрыта', время_окончания = ?
            WHERE дата < ? AND статус = 'активна'
        ''', (current_time, current_date))
        
        # Close shifts of current day that should have ended
        # Shift 1: 07:00 - 19:00
        # Shift 2: 19:00 - 07:00 (next day)
        
        if current_time > '19:00':
            # Close shift 1 if time is after 19:00
            cursor.execute('''
                UPDATE смены 
                SET статус = 'закрыта', время_окончания = '19:00'
                WHERE дата = ? AND номер_смены = 1 AND статус = 'активна'
            ''', (current_date,))
        
        if current_time > '07:00' and current_time < '19:00':
            # Close shift 2 from previous day if time is between 07:00 and 19:00
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE смены 
                SET статус = 'закрыта', время_окончания = '07:00'
                WHERE дата = ? AND номер_смены = 2 AND статус = 'активна'
            ''', (yesterday,))
        
        conn.commit()
        conn.close()
        
        logger.info("Auto-close expired shifts completed")
        
    except Exception as e:
        logger.error(f"Error auto-closing shifts: {e}")
        if conn:
            conn.close()


def get_shift_statistics(shift_id: int) -> Optional[Dict[str, Any]]:
    """Get shift statistics"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Get overall shift statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_records,
                SUM(всего_отлито) as total_cast,
                SUM(всего_принято) as total_accepted,
                AVG(CAST(всего_принято AS FLOAT) / CAST(всего_отлито AS FLOAT) * 100) as avg_quality
            FROM записи_контроля 
            WHERE смена_id = ?
        ''', (shift_id,))
        
        stats = cursor.fetchone()
        
        # Get defect statistics
        cursor.execute('''
            SELECT
                cd.название as категория,
                td.название,
                SUM(dr.количество) as total_count
            FROM дефекты_записей dr
            JOIN записи_контроля zk ON dr.запись_контроля_id = zk.id
            JOIN типы_дефектов td ON dr.тип_дефекта_id = td.id
            JOIN категории_дефектов cd ON td.категория_id = cd.id
            WHERE zk.смена_id = ?
            GROUP BY cd.название, td.название
            ORDER BY total_count DESC
        ''', (shift_id,))
        
        defects = cursor.fetchall()
        conn.close()
        
        return {
            'total_records': stats[0] or 0,
            'total_cast': stats[1] or 0,
            'total_accepted': stats[2] or 0,
            'avg_quality': round(stats[3] or 0, 2),
            'defects': [{'category': d[0], 'name': d[1], 'count': d[2]} for d in defects]
        }
        
    except Exception as e:
        logger.error(f"Error getting shift statistics: {e}")
        if conn:
            conn.close()
        return None


def get_all_shifts(limit: int = 50) -> list:
    """Get all shifts"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM смены
            ORDER BY дата DESC, номер_смены DESC
            LIMIT ?
        ''', (limit,))
        shifts = cursor.fetchall()
        conn.close()
        
        result = []
        for shift_row in shifts:
            result.append({
                'id': shift_row[0],
                'date': shift_row[1],
                'shift_number': shift_row[2],
                'supervisor': shift_row[3],
                'controllers': json.loads(shift_row[4]) if shift_row[4] else [],
                'start_time': shift_row[5],
                'end_time': shift_row[6],
                'status': shift_row[7]
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting all shifts: {e}")
        if conn:
            conn.close()
        return []
