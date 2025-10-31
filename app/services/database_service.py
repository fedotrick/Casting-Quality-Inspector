"""
Database service layer for all database operations.
Handles connections to main DB, foundry DB, and route cards DB.
"""
import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import current_app

from ..helpers.error_handlers import ОшибкаБазыДанных, handle_database_error, handle_integration_error, error_handler
from ..helpers.logging_config import log_operation

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get connection to main quality control database"""
    try:
        db_path = current_app.config['DATABASE_PATH']
        if not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory for database: {db_path.parent}")
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise ОшибкаБазыДанных(f"Failed to connect to database: {str(e)}")


def init_database(conn):
    """Initialize database with Cyrillic tables as in original"""
    try:
        cursor = conn.cursor()
        
        # Controllers table (as in original)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS контролеры (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                имя TEXT UNIQUE NOT NULL,
                активен INTEGER DEFAULT 1
            )
        ''')
        
        # Defect categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS категории_дефектов (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                название TEXT UNIQUE NOT NULL,
                описание TEXT,
                порядок_сортировки INTEGER DEFAULT 0,
                создана DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Defect types table (as in original)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS типы_дефектов (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                категория_id INTEGER NOT NULL,
                название TEXT NOT NULL,
                описание TEXT,
                активен INTEGER DEFAULT 1,
                порядок_сортировки INTEGER DEFAULT 0,
                создан DATETIME DEFAULT CURRENT_TIMESTAMP,
                обновлен DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (категория_id) REFERENCES категории_дефектов (id),
                UNIQUE(категория_id, название)
            )
        ''')
        
        # Shifts table (as in original)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS смены (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                дата TEXT NOT NULL,
                номер_смены INTEGER NOT NULL,
                старший TEXT DEFAULT 'Контролеры',
                контролеры TEXT NOT NULL,
                время_начала TEXT NOT NULL,
                время_окончания TEXT,
                статус TEXT DEFAULT 'активна'
            )
        ''')
        
        # Control records table (as in original)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS записи_контроля (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                смена_id INTEGER NOT NULL,
                номер_маршрутной_карты TEXT NOT NULL,
                всего_отлито INTEGER NOT NULL,
                всего_принято INTEGER NOT NULL,
                контролер TEXT NOT NULL,
                заметки TEXT,
                создана TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Record defects table (as in original)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS дефекты_записей (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                запись_контроля_id INTEGER NOT NULL,
                тип_дефекта_id INTEGER NOT NULL,
                количество INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        
        # Load controllers and defect types only if tables are empty
        cursor.execute("SELECT COUNT(*) FROM контролеры")
        controllers_count = cursor.fetchone()[0]
        
        if controllers_count == 0:
            load_controllers(conn)
        
        # Check unique defect types count
        cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT категория_id, название FROM типы_дефектов) AS unique_defects")
        unique_defects_count = cursor.fetchone()[0]
        
        if unique_defects_count == 0:
            load_defect_types(conn)
        
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise ОшибкаБазыДанных(f"Failed to initialize database: {str(e)}")


def load_controllers(conn):
    """Check for controllers in database"""
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM контролеры')
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} controllers in database")
        
        if count == 0:
            logger.info("No controllers in database, but not adding default ones")
    except Exception as e:
        logger.error(f"Error loading controllers: {e}")
        raise ОшибкаБазыДанных(f"Failed to load controllers: {str(e)}")


def load_defect_types(conn):
    """Load defect types with Russian categories"""
    try:
        cursor = conn.cursor()
        defect_types = current_app.config['DEFECT_TYPES']
        
        # First create defect categories if they don't exist
        for category, data in defect_types.items():
            cursor.execute('INSERT OR IGNORE INTO категории_дефектов (название, описание) VALUES (?, ?)',
                         (data['name'], f'Категория дефектов: {data["name"]}'))
        
        # Then load defect types
        for category, data in defect_types.items():
            cursor.execute('SELECT id FROM категории_дефектов WHERE название = ?', (data['name'],))
            category_row = cursor.fetchone()
            if category_row:
                category_id = category_row[0]
                for defect_type in data['types']:
                    cursor.execute('INSERT OR IGNORE INTO типы_дефектов (категория_id, название) VALUES (?, ?)',
                                 (category_id, defect_type))
        
        conn.commit()
        logger.info("Loaded defect types")
    except Exception as e:
        logger.error(f"Error loading defect types: {e}")
        raise ОшибкаБазыДанных(f"Failed to load defect types: {str(e)}")


@handle_integration_error(critical=False)
def get_foundry_db_connection():
    """Connection to foundry.db"""
    foundry_path = current_app.config['FOUNDRY_DB_PATH']
    if not foundry_path.exists():
        return None
    conn = sqlite3.connect(str(foundry_path))
    conn.row_factory = sqlite3.Row
    return conn


@handle_integration_error(critical=False)
def search_route_card_in_foundry(card_number: str):
    """Search route card with FULL information"""
    from ..helpers.validators import validate_route_card_number
    
    if not validate_route_card_number(card_number):
        logger.warning(f"Invalid route card number format: {card_number}")
        return None
    
    conn = get_foundry_db_connection()
    if not conn:
        logger.warning(f"Could not connect to foundry.db to search card {card_number}")
        return None
    
    cursor = conn.cursor()
    # CORRECT query with JOIN to get ALL information
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
    """Connection to маршрутные_карты.db"""
    route_cards_path = current_app.config['ROUTE_CARDS_DB_PATH']
    if not route_cards_path.exists():
        logger.warning(f"Route cards database not found: {route_cards_path}")
        return None
    conn = sqlite3.connect(str(route_cards_path))
    conn.row_factory = sqlite3.Row
    return conn


@handle_integration_error(critical=False)
def update_route_card_status(card_number: str):
    """Update route card status in маршрутные_карты.db to 'Завершена'"""
    conn = get_route_cards_db_connection()
    if not conn:
        logger.warning("Could not connect to маршрутные_карты.db to update status")
        return False
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Find appropriate table
    route_table = None
    for table in tables:
        if 'маршрут' in table.lower() or 'карт' in table.lower():
            route_table = table
            break
    
    if not route_table:
        logger.warning("Route cards table not found in маршрутные_карты.db")
        conn.close()
        return False
    
    # Check table structure
    cursor.execute(f"PRAGMA table_info({route_table})")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Find number and status fields
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
    """Get all controllers from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM контролеры WHERE активен = 1 ORDER BY имя')
        controllers = cursor.fetchall()
        conn.close()
        return [dict(c) for c in controllers]
    except Exception as e:
        logger.error(f"Error getting controllers: {e}")
        if conn:
            conn.close()
        return []


def add_controller(name: str):
    """Add new controller"""
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO контролеры (имя, активен) VALUES (?, 1)', (name,))
        conn.commit()
        controller_id = cursor.lastrowid
        conn.close()
        logger.info(f"Added controller: {name}")
        return controller_id
    except sqlite3.IntegrityError:
        if conn:
            conn.close()
        raise ОшибкаБазыДанных(f"Контролер '{name}' уже существует")
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error adding controller: {e}")
        raise ОшибкаБазыДанных(f"Failed to add controller: {str(e)}")


def toggle_controller(controller_id: int):
    """Toggle controller active status"""
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE контролеры SET активен = NOT активен WHERE id = ?', (controller_id,))
        conn.commit()
        conn.close()
        logger.info(f"Toggled controller {controller_id} status")
        return True
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error toggling controller: {e}")
        raise ОшибкаБазыДанных(f"Failed to toggle controller: {str(e)}")


def delete_controller(controller_id: int):
    """Delete controller"""
    conn = get_db_connection()
    if not conn:
        raise ОшибкаБазыДанных("Could not connect to database")
    
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM контролеры WHERE id = ?', (controller_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted controller {controller_id}")
        return True
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Error deleting controller: {e}")
        raise ОшибкаБазыДанных(f"Failed to delete controller: {str(e)}")


def get_all_defect_types():
    """Get all defect types grouped by category"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                kd.id as категория_id,
                kd.название as категория,
                td.id as тип_id,
                td.название as тип
            FROM категории_дефектов kd
            LEFT JOIN типы_дефектов td ON kd.id = td.категория_id
            WHERE td.активен = 1
            ORDER BY kd.порядок_сортировки, kd.название, td.порядок_сортировки, td.название
        ''')
        defects = cursor.fetchall()
        conn.close()
        
        # Group by category
        result = {}
        for row in defects:
            category_id = row[0]
            category_name = row[1]
            if category_id not in result:
                result[category_id] = {
                    'id': category_id,
                    'name': category_name,
                    'types': []
                }
            if row[2]:  # If defect type exists
                result[category_id]['types'].append({
                    'id': row[2],
                    'name': row[3]
                })
        
        return list(result.values())
    except Exception as e:
        logger.error(f"Error getting defect types: {e}")
        if conn:
            conn.close()
        return []


def check_card_already_processed(card_number: str) -> bool:
    """Check if route card has already been processed"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM записи_контроля
            WHERE номер_маршрутной_карты = ?
        ''', (card_number,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"Error checking if card already processed: {e}")
        if conn:
            conn.close()
        return False
