"""
New database service layer using SQLAlchemy.
This replaces the old sqlite3-based database_service.py
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from flask import current_app
import sqlite3

from ..database import get_db, init_db as initialize_db
from ..repositories import ControllerRepository, DefectRepository
from ..helpers.error_handlers import ОшибкаБазыДанных, handle_integration_error
from ..helpers.logging_config import log_operation

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Get database session (SQLAlchemy).
    For backward compatibility, returns session instead of raw connection.
    """
    return get_db()


def init_database(session=None):
    """Initialize database with SQLAlchemy"""
    try:
        initialize_db()
        logger.info("Database initialized with SQLAlchemy")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise ОшибкаБазыДанных(f"Failed to initialize database: {str(e)}")


def load_controllers(session=None):
    """Compatibility function - controllers are now managed via repository"""
    logger.info("Controllers are managed via ControllerRepository")


def load_defect_types(session=None):
    """Compatibility function - defect types are now loaded automatically"""
    logger.info("Defect types are loaded automatically during database initialization")


@handle_integration_error(critical=False)
def get_foundry_db_connection():
    """Connection to foundry.db (still using sqlite3 for external DB)"""
    foundry_path = current_app.config['FOUNDRY_DB_PATH']
    if not foundry_path.exists():
        return None
    conn = sqlite3.connect(str(foundry_path))
    conn.row_factory = sqlite3.Row
    return conn


@handle_integration_error(critical=False)
def search_route_card_in_foundry(card_number: str):
    """Search route card with FULL information (still uses external DB)"""
    from ..helpers.validators import validate_route_card_number
    
    if not validate_route_card_number(card_number):
        logger.warning(f"Invalid route card number format: {card_number}")
        return None
    
    conn = get_foundry_db_connection()
    if not conn:
        logger.warning(f"Could not connect to foundry.db to search card {card_number}")
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            п.Маршрутная_карта,
            п.Номер_кластера,
            п.Учетный_номер,
            п.Температура,
            о.Название as Наименование_отливки,
            л.Название as Тип_литниковой_системы
        FROM Плавки п
        LEFT JOIN Наименование_отливок о ON п.ID_отливки = о.ID
        LEFT JOIN Тип_литниковой_системы л ON п.ID_литниковой_системы = л.ID
        WHERE п.Маршрутная_карта = ?
    """, (card_number,))
    
    result = cursor.fetchone()
    
    if result:
        logger.info(f"Found route card {card_number}")
        card_data = dict(result)
        conn.close()
        return card_data
    else:
        logger.info(f"Route card {card_number} not found in foundry.db")
        conn.close()
        return None


@handle_integration_error(critical=False)
def get_route_cards_db_connection():
    """Connection to маршрутные_карты.db (still using sqlite3 for external DB)"""
    route_cards_path = current_app.config['ROUTE_CARDS_DB_PATH']
    if not route_cards_path.exists():
        logger.warning(f"Route cards database not found: {route_cards_path}")
        return None
    conn = sqlite3.connect(str(route_cards_path))
    conn.row_factory = sqlite3.Row
    return conn


@handle_integration_error(critical=False)
def update_route_card_status(card_number: str):
    """Update route card status in маршрутные_карты.db to 'Завершена' (external DB)"""
    conn = get_route_cards_db_connection()
    if not conn:
        logger.warning("Could not connect to маршрутные_карты.db to update status")
        return False
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    route_table = None
    for table in tables:
        if 'маршрут' in table.lower() or 'карт' in table.lower():
            route_table = table
            break
    
    if not route_table:
        logger.warning("Route cards table not found in маршрутные_карты.db")
        conn.close()
        return False
    
    cursor.execute(f"PRAGMA table_info({route_table})")
    columns = [column[1] for column in cursor.fetchall()]
    
    number_field = None
    status_field = None
    
    for col in columns:
        if 'номер' in col.lower() or 'карт' in col.lower():
            number_field = col
        if 'статус' in col.lower() or 'состояние' in col.lower():
            status_field = col
    
    if number_field and status_field:
        cursor.execute(f"SELECT {status_field} FROM {route_table} WHERE {number_field} = ?", (card_number,))
        existing_record = cursor.fetchone()
        
        if existing_record:
            cursor.execute(f"""
                UPDATE {route_table}
                SET {status_field} = 'Завершена'
                WHERE {number_field} = ?
            """, (card_number,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Card {card_number} status updated to 'Завершена' in {route_table}")
                conn.close()
                return True
            else:
                current_status = existing_record[0] if existing_record[0] else 'Not defined'
                logger.info(f"Card {card_number} already has status '{current_status}' in {route_table}")
                conn.close()
                return True
        else:
            logger.warning(f"Card {card_number} not found in table {route_table}")
    else:
        logger.warning(f"Number or status fields not found in table {route_table}")
    
    conn.close()
    return False


def get_all_controllers():
    """Get all controllers using repository"""
    session = get_db()
    repo = ControllerRepository(session)
    try:
        controllers = repo.get_active()
        return [c.to_dict() for c in controllers]
    except Exception as e:
        logger.error(f"Error getting controllers: {e}")
        return []


def add_controller(name: str):
    """Add new controller using repository"""
    session = get_db()
    repo = ControllerRepository(session)
    try:
        controller = repo.create(name)
        session.commit()
        logger.info(f"Added controller: {name}")
        return controller.id
    except Exception as e:
        session.rollback()
        raise


def toggle_controller(controller_id: int):
    """Toggle controller active status using repository"""
    session = get_db()
    repo = ControllerRepository(session)
    try:
        result = repo.toggle(controller_id)
        session.commit()
        logger.info(f"Toggled controller {controller_id} status")
        return result
    except Exception as e:
        session.rollback()
        raise


def delete_controller(controller_id: int):
    """Delete controller using repository"""
    session = get_db()
    repo = ControllerRepository(session)
    try:
        result = repo.delete(controller_id)
        session.commit()
        logger.info(f"Deleted controller {controller_id}")
        return result
    except Exception as e:
        session.rollback()
        raise


def get_all_defect_types():
    """Get all defect types grouped by category using repository"""
    session = get_db()
    repo = DefectRepository(session)
    try:
        return repo.get_all_types_grouped()
    except Exception as e:
        logger.error(f"Error getting defect types: {e}")
        return []


def check_card_already_processed(card_number: str) -> bool:
    """Check if route card has already been processed"""
    from ..repositories import ControlRepository
    
    session = get_db()
    repo = ControlRepository(session)
    try:
        return repo.check_card_processed(card_number)
    except Exception as e:
        logger.error(f"Error checking if card already processed: {e}")
        return False
