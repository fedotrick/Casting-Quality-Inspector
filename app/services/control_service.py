"""
Quality control service layer.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .database_service import get_db_connection, update_route_card_status
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
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        
        # Insert control record
        cursor.execute('''
            INSERT INTO записи_контроля 
            (смена_id, номер_маршрутной_карты, всего_отлито, всего_принято, контролер, заметки, создана)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (shift_id, card_number, total_cast, total_accepted, controller, notes, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        record_id = cursor.lastrowid
        
        # Insert defects
        for defect_type_id, count in defects.items():
            if count > 0:  # Only insert non-zero defects
                cursor.execute('''
                    INSERT INTO дефекты_записей (запись_контроля_id, тип_дефекта_id, количество)
                    VALUES (?, ?, ?)
                ''', (record_id, defect_type_id, count))
        
        conn.commit()
        conn.close()
        
        # Try to update route card status in external DB
        update_route_card_status(card_number)
        
        logger.info(f"Saved control record {record_id} for card {card_number}")
        return record_id
        
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error saving control record: {e}")
        raise ОшибкаБазыДанных(f"Failed to save control record: {str(e)}")


def get_control_records_by_shift(shift_id: int) -> list:
    """Get all control records for a shift"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM записи_контроля
            WHERE смена_id = ?
            ORDER BY создана DESC
        ''', (shift_id,))
        records = cursor.fetchall()
        conn.close()
        
        result = []
        for record in records:
            result.append({
                'id': record[0],
                'shift_id': record[1],
                'card_number': record[2],
                'total_cast': record[3],
                'total_accepted': record[4],
                'controller': record[5],
                'notes': record[6],
                'created': record[7]
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting control records: {e}")
        if conn:
            conn.close()
        return []


def get_control_record_defects(record_id: int) -> list:
    """Get defects for a control record"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                dr.id,
                dr.количество,
                td.название as defect_name,
                kd.название as category_name
            FROM дефекты_записей dr
            JOIN типы_дефектов td ON dr.тип_дефекта_id = td.id
            JOIN категории_дефектов kd ON td.категория_id = kd.id
            WHERE dr.запись_контроля_id = ?
        ''', (record_id,))
        defects = cursor.fetchall()
        conn.close()
        
        result = []
        for defect in defects:
            result.append({
                'id': defect[0],
                'count': defect[1],
                'defect_name': defect[2],
                'category_name': defect[3]
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting record defects: {e}")
        if conn:
            conn.close()
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
