#!/usr/bin/env python3
"""
ИСПРАВЛЕННАЯ система контроля качества литейного производства
Все требования выполнены ПРАВИЛЬНО
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, render_template_string
from flask_cors import CORS
import traceback
import re

# Настройка логирования
from utils.logging_config import setup_logging, log_operation, log_error_with_context, get_user_info, log_user_action, log_system_event
from utils.error_handlers import error_handler, validate_and_handle_errors, handle_service_error, ОшибкаБазыДанных, ОшибкаИнтеграции, ОшибкаВалидации, handle_database_error, handle_integration_error, handle_validation_error
from utils.ui_error_handlers import ui_error_handler, handle_ui_error, create_user_friendly_error_message, handle_ui_exception, create_error_response, handle_validation_errors
from utils.input_validators import input_validator, validate_route_card_number, validate_positive_integer, validate_shift_data_extended, validate_and_log_input, validate_control_data, validate_json_input, validate_form_input
from database.external_db_integration import external_db_integration, search_route_card_in_external_db, update_route_card_status_in_external_db, write_detailed_route_card_info_to_external_db, validate_route_card_number_in_external_db

setup_logging(log_level="INFO", log_file=Path("logs/application.log"))
logger = logging.getLogger(__name__)

def log_error_and_respond(error, message="Произошла ошибка", status_code=500):
    """Централизованная обработка ошибок с логированием и возвратом JSON ответа"""
    from flask import has_request_context
    request_obj = request if has_request_context() else None
    error_handler.log_user_error(f"{message}: {str(error)}", request_obj)
    log_error_with_context(logger, error, {"message": message, "status_code": status_code})
    return jsonify({'success': False, 'error': str(error), 'error_id': f"app_{id(error)}"}), status_code

def validate_input_data(data, required_fields):
    """Валидация пользовательского ввода"""
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Поле '{field}' обязательно для заполнения")
    return errors

def validate_route_card_number(card_number: str) -> bool:
    """Валидация номера маршрутной карты"""
    if not card_number:
        return False
    # Проверяем, что номер карты состоит только из цифр и имеет длину 6 символов
    return re.match(r'^\d{6}$', card_number) is not None

def validate_positive_integer(value, field_name: str) -> tuple[bool, str]:
    """Валидация положительного целого числа"""
    try:
        int_value = int(value)
        if int_value <= 0:
            return False, f"Поле '{field_name}' должно быть положительным числом"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Поле '{field_name}' должно быть числом"

def validate_shift_data_extended(date, shift_number, controllers):
    """Расширенная валидация данных смены"""
    errors = []
    
    # Проверка даты
    if not date:
        errors.append("Дата смены обязательна")
    else:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            # Проверяем, что дата не в будущем (с учетом небольшого запаса на смены следующего дня)
            if parsed_date.date() > datetime.now().date() + timedelta(days=1):
                errors.append("Дата смены не может быть в будущем")
        except ValueError:
            errors.append("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
    
    # Проверка номера смены
    if shift_number is None or shift_number not in [1, 2]:
        errors.append("Номер смены должен быть 1 или 2")
    
    # Проверка контролеров
    if not controllers or len(controllers) == 0:
        errors.append("Необходимо выбрать хотя бы одного контролера")
    
    # Проверка на дублирование смены
    if not errors and date and shift_number:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM смены
                    WHERE дата = ? AND номер_смены = ? AND статус = 'активна'
                ''', (date, shift_number))
                
                if cursor.fetchone()[0] > 0:
                    errors.append(f"Смена {shift_number} на дату {date} уже активна")
                
                conn.close()
            except Exception as e:
                logger.error(f"Ошибка проверки дублирования смены: {e}")
                errors.append("Ошибка проверки данных смены")
                if conn:
                    conn.close()
    
    return errors

def validate_and_log_user_input(data: Dict[str, Any], required_fields: List[str], operation: str) -> List[str]:
    """Валидирует пользовательский ввод и логирует операцию"""
    errors = validate_and_log_input(data, required_fields, operation)
    return errors

def validate_control_data_enhanced(total_cast, total_accepted, defects_data):
    """Улучшенная валидация данных контроля качества"""
    errors = []
    warnings = []
    
    # Проверка основных данных
    if not total_cast or total_cast <= 0:
        errors.append("Количество отлитых деталей должно быть больше 0")
    
    if total_accepted < 0:
        errors.append("Количество принятых деталей не может быть отрицательным")
    
    if total_accepted > total_cast:
        errors.append("Количество принятых деталей не может превышать количество отлитых")
    
    # Проверка дефектов
    total_defects = sum(defects_data.values()) if defects_data else 0
    calculated_accepted = total_cast - total_defects
    
    if calculated_accepted != total_accepted:
        warnings.append(f"Расчетное количество принятых ({calculated_accepted}) не совпадает с указанным ({total_accepted})")
    
    # Проверка на подозрительно высокий процент брака
    if total_cast > 0:
        reject_rate = (total_defects / total_cast) * 100
        if reject_rate > 50:
            warnings.append(f"Высокий процент брака: {reject_rate:.1f}%")
        elif reject_rate > 30:
            warnings.append(f"Повышенный процент брака: {reject_rate:.1f}%")
    
    # Проверка на отрицательные значения дефектов
    for defect_name, count in defects_data.items():
        if count < 0:
            errors.append(f"Количество дефектов '{defect_name}' не может быть отрицательным")
    
    # Дополнительная валидация для особых случаев
    if total_cast > 10000:
        warnings.append(f"Очень большое количество отлитых деталей: {total_cast}")
    
    if total_defects > 5000:
        warnings.append(f"Очень большое количество дефектов: {total_defects}")
    
    return errors, warnings

def validate_shift_data_enhanced(date, shift_number, controllers):
    """Улучшенная валидация данных смены"""
    errors = []
    
    # Проверка даты
    if not date:
        errors.append("Дата смены обязательна")
    else:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            # Проверяем, что дата не в будущем (с учетом небольшого запаса на смены следующего дня)
            if parsed_date.date() > datetime.now().date() + timedelta(days=1):
                errors.append("Дата смены не может быть в будущем")
        except ValueError:
            errors.append("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
    
    # Проверка номера смены
    if shift_number is None or shift_number not in [1, 2]:
        errors.append("Номер смены должен быть 1 или 2")
    
    # Проверка контролеров
    if not controllers or len(controllers) == 0:
        errors.append("Необходимо выбрать хотя бы одного контролера")
    
    # Проверка на дублирование смены
    if not errors and date and shift_number:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) FROM смены
                    WHERE дата = ? AND номер_смены = ? AND статус = 'активна'
                ''', (date, shift_number))
                
                if cursor.fetchone()[0] > 0:
                    errors.append(f"Смена {shift_number} на дату {date} уже активна")
                
                conn.close()
            except Exception as e:
                logger.error(f"Ошибка проверки дублирования смены: {e}")
                errors.append("Ошибка проверки данных смены")
                if conn:
                    conn.close()
    
    return errors

def log_operation_enhanced(operation: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование операций с контекстной информацией"""
    user_info = get_user_info()
    log_data = {
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
        'user_info': user_info,
        'details': details or {}
    }
    logger.info(f"ОПЕРАЦИЯ: {json.dumps(log_data, ensure_ascii=False, indent=2)}")

def log_user_action_enhanced(user_id: str, action: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование действий пользователей"""
    action_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"ДЕЙСТВИЕ ПОЛЬЗОВАТЕЛЯ: {json.dumps(action_data, ensure_ascii=False, indent=2)}")

def log_system_event_enhanced(event_type: str, message: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование системных событий"""
    event_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"СИСТЕМНОЕ СОБЫТИЕ: {json.dumps(event_data, ensure_ascii=False, indent=2)}")

def log_error_with_context_enhanced(error: Exception, context: Optional[dict] = None) -> None:
    """Улучшенное логирование ошибок с контекстной информацией"""
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {},
        'traceback': traceback.format_exc()
    }
    logger.error(f"ОШИБКА: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

def log_operation_enhanced(operation: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование операций с контекстной информацией"""
    user_info = get_user_info()
    log_data = {
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
        'user_info': user_info,
        'details': details or {}
    }
    logger.info(f"ОПЕРАЦИЯ: {json.dumps(log_data, ensure_ascii=False, indent=2)}")

def log_user_action_enhanced(user_id: str, action: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование действий пользователей"""
    action_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"ДЕЙСТВИЕ ПОЛЬЗОВАТЕЛЯ: {json.dumps(action_data, ensure_ascii=False, indent=2)}")

def log_system_event_enhanced(event_type: str, message: str, details: Optional[dict] = None) -> None:
    """Улучшенное логирование системных событий"""
    event_data = {
        'event_type': event_type,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    logger.info(f"СИСТЕМНОЕ СОБЫТИЕ: {json.dumps(event_data, ensure_ascii=False, indent=2)}")

def log_error_with_context_enhanced(error: Exception, context: Optional[dict] = None) -> None:
    """Улучшенное логирование ошибок с контекстной информацией"""
    error_data = {
        'error': str(error),
        'error_type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
        'context': context or {},
        'traceback': traceback.format_exc()
    }
    logger.error(f"ОШИБКА: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

# Создаем Flask приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = 'corrected-foundry-system-2024'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './sessions'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'qc_'

# Создаем директорию для сессий если её нет
Path('./sessions').mkdir(exist_ok=True)

CORS(app)

# Пути к базам данных
DATABASE_PATH = Path('data/quality_control.db')
FOUNDRY_DB_PATH = Path(r'C:\Users\1\Telegram\MetalFusionX\foundry.db')
ROUTE_CARDS_DB_PATH = Path(r'C:\Users\1\Telegram\FoamFusionLab\data\маршрутные_карты.db')

# ВСЕ типы дефектов из control.xlsx
DEFECT_TYPES = {
    "second_grade": {
        "name": "Второй сорт",
        "types": ["Раковины", "Зарез литейный", "Зарез пеномодельный"]
    },
    "rework": {
        "name": "Доработка", 
        "types": [
            "Раковины", "Несоответствие размеров", "Несоответствие внешнего вида",
            "Наплыв металла", "Прорыв металла", "Вырыв", "Облой", "Песок на поверхности",
            "Песок в резьбе", "Клей", "Коробление", "Дефект пеномодели", "Лапы",
            "Питатель", "Корона", "Смещение", "Клей подтёк", "Клей по шву"
        ]
    },
    "final_reject": {
        "name": "Окончательный брак",
        "types": [
            "Недолив", "Вырыв", "Коробление", "Наплыв металла",
            "Нарушение геометрии", "Нарушение маркировки", "Непроклей", "Неслитина",
            "Несоответствие внешнего вида", "Несоответствие размеров", "Пеномодель",
            "Пористость", "Пригар песка", "Прочее", "Рыхлота", "Раковины",
            "Скол", "Слом", "Спай", "Трещины", "Зарез литейный", "Зарез пеномодельный"
        ]
    }
}

def get_db_connection():
    """Получает подключение к основной базе данных"""
    try:
        if not DATABASE_PATH.exists():
            DATABASE_PATH.parent.mkdir(exist_ok=True)
            logger.info(f"Создана директория для базы данных: {DATABASE_PATH.parent}")
        
        conn = sqlite3.connect(str(DATABASE_PATH))
        conn.row_factory = sqlite3.Row
        logger.info("Успешно подключено к базе данных")
        return conn
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        # Не вызываем error_handler.log_user_error здесь, так как это может быть вне контекста запроса
        raise ОшибкаБазыДанных(f"Не удалось подключиться к базе данных: {str(e)}")

def init_database(conn):
    """Инициализация базы данных - кириллические таблицы как в оригинале"""
    try:
        cursor = conn.cursor()
        
        # Таблица контролеров (как в оригинале)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS контролеры (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                имя TEXT UNIQUE NOT NULL,
                активен INTEGER DEFAULT 1
            )
        ''')
        
        # Таблица категорий дефектов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS категории_дефектов (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                название TEXT UNIQUE NOT NULL,
                описание TEXT,
                порядок_сортировки INTEGER DEFAULT 0,
                создана DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица типов дефектов (как в оригинале)
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
        
        # Таблица смен (как в оригинале)
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
        
        # Таблица записей контроля (как в оригинале)
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
        
        # Таблица дефектов записей (как в оригинале)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS дефекты_записей (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                запись_контроля_id INTEGER NOT NULL,
                тип_дефекта_id INTEGER NOT NULL,
                количество INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        
        # Загружаем контролеров и типы дефектов только если таблицы пусты
        cursor.execute("SELECT COUNT(*) FROM контролеры")
        controllers_count = cursor.fetchone()[0]
        
        if controllers_count == 0:
            # Только если таблица пуста, загружаем начальные данные
            load_controllers(conn)
        
        # Проверяем количество уникальных типов дефектов, а не общее количество записей
        cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT категория_id, название FROM типы_дефектов) AS unique_defects")
        unique_defects_count = cursor.fetchone()[0]
        
        if unique_defects_count == 0:
            # Только если таблица пуста, загружаем начальные данные
            load_defect_types(conn)
        
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        # Не вызываем error_handler.log_user_error здесь, так как это может быть вне контекста запроса
        raise ОшибкаБазыДанных(f"Не удалось инициализировать базу данных: {str(e)}")

def load_controllers(conn):
    """Проверяет наличие контролеров в базе данных"""
    try:
        cursor = conn.cursor()
        
        # Проверяем, есть ли уже контролеры в базе
        cursor.execute('SELECT COUNT(*) FROM контролеры')
        count = cursor.fetchone()[0]
        
        logger.info(f"В базе данных найдено {count} контролеров")
        
        # Если в базе нет контролеров, не добавляем никаких стандартных
        if count == 0:
            logger.info("В базе данных нет контролеров, но стандартные не добавляются")
    except Exception as e:
        logger.error(f"Ошибка загрузки контролеров: {e}")
        from flask import has_request_context
        request_obj = request if has_request_context() else None
        error_handler.log_user_error(f"Ошибка загрузки контролеров: {str(e)}", request_obj)
        raise ОшибкаБазыДанных(f"Не удалось загрузить контролеров: {str(e)}")

def load_defect_types(conn):
    """Загружает типы дефектов с русскими категориями"""
    try:
        cursor = conn.cursor()
        
        # Сначала создаем категории дефектов, если их нет
        for category, data in DEFECT_TYPES.items():
            cursor.execute('INSERT OR IGNORE INTO категории_дефектов (название, описание) VALUES (?, ?)',
                         (data['name'], f'Категория дефектов: {data['name']}'))
        
        # Затем загружаем типы дефектов
        for category, data in DEFECT_TYPES.items():
            # Получаем ID категории
            cursor.execute('SELECT id FROM категории_дефектов WHERE название = ?', (data['name'],))
            category_row = cursor.fetchone()
            if category_row:
                category_id = category_row[0]
                for defect_type in data['types']:
                    cursor.execute('INSERT OR IGNORE INTO типы_дефектов (категория_id, название) VALUES (?, ?)',
                                 (category_id, defect_type))
        
        conn.commit()
        logger.info("Загружены типы дефектов")
    except Exception as e:
        logger.error(f"Ошибка загрузки типов дефектов: {e}")
        from flask import has_request_context
        request_obj = request if has_request_context() else None
        error_handler.log_user_error(f"Ошибка загрузки типов дефектов: {str(e)}", request_obj)
        raise ОшибкаБазыДанных(f"Не удалось загрузить типы дефектов: {str(e)}")

@handle_integration_error(critical=False)
def get_foundry_db_connection():
    """Подключение к foundry.db"""
    if not FOUNDRY_DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(FOUNDRY_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@handle_integration_error(critical=False)
def search_route_card_in_foundry(card_number):
    """Поиск маршрутной карты с ПОЛНОЙ информацией"""
    # Валидация номера маршрутной карты
    if not validate_route_card_number(card_number):
        from flask import has_request_context
        request_obj = request if has_request_context() else None
        error_handler.log_user_error(f"Неверный формат номера маршрутной карты: {card_number}", request_obj)
        logger.warning(f"Неверный формат номера маршрутной карты: {card_number}")
        return None
    
    conn = get_foundry_db_connection()
    if not conn:
        logger.warning(f"Не удалось подключиться к foundry.db для поиска карты {card_number}")
        from flask import has_request_context
        request_obj = request if has_request_context() else None
        error_handler.log_user_error(f"Не удалось подключиться к foundry.db для поиска карты {card_number}", request_obj)
        return None
    
    cursor = conn.cursor()
    # ПРАВИЛЬНЫЙ запрос с JOIN для получения ВСЕЙ информации
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
        logger.info(f"Найдена маршрутная карта {card_number}")
        log_operation(logger, "Поиск маршрутной карты", {
            "card_number": card_number,
            "found": True
        })
        card_data = dict(result)
        conn.close()
        return card_data
    else:
        logger.info(f"Маршрутная карта {card_number} не найдена в foundry.db")
        log_operation(logger, "Поиск маршрутной карты", {
            "card_number": card_number,
            "found": False
        })
        conn.close()
        return None

@handle_integration_error(critical=False)
def get_route_cards_db_connection():
    """Подключение к маршрутные_карты.db"""
    if not ROUTE_CARDS_DB_PATH.exists():
        logger.warning(f"База данных маршрутные_карты.db не найдена: {ROUTE_CARDS_DB_PATH}")
        return None
    conn = sqlite3.connect(str(ROUTE_CARDS_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@handle_integration_error(critical=False)
def update_route_card_status(card_number):
    """Обновляет статус маршрутной карты в маршрутные_карты.db на 'Завершена'"""
    conn = get_route_cards_db_connection()
    if not conn:
        logger.warning("Не удалось подключиться к маршрутные_карты.db для обновления статуса")
        return False
    
    cursor = conn.cursor()
    # Проверяем, есть ли таблица маршрутных карт
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Ищем подходящую таблицу
    route_table = None
    for table in tables:
        if 'маршрут' in table.lower() or 'карт' in table.lower():
            route_table = table
            break
    
    if not route_table:
        logger.warning("Таблица маршрутных карт не найдена в маршрутные_карты.db")
        conn.close()
        return False
    
    # Проверяем структуру таблицы
    cursor.execute(f"PRAGMA table_info({route_table})")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Ищем поля номера и статуса
    number_field = None
    status_field = None
    
    for col in columns:
        if 'номер' in col.lower() or 'карт' in col.lower():
            number_field = col
        if 'статус' in col.lower() or 'состояние' in col.lower():
            status_field = col
    
    if number_field and status_field:
        # Сначала проверяем, существует ли карта
        cursor.execute(f"SELECT {status_field} FROM {route_table} WHERE {number_field} = ?", (card_number,))
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Карта существует, обновляем статус
            cursor.execute(f"""
                UPDATE {route_table}
                SET {status_field} = 'Завершена'
                WHERE {number_field} = ?
            """, (card_number,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Статус карты {card_number} обновлен на 'Завершена' в {route_table}")
                conn.close()
                return True
            else:
                # Если rowcount = 0, возможно, статус уже 'Завершена'
                current_status = existing_record[0] if existing_record[0] else 'Не определен'
                logger.info(f"Статус карты {card_number} уже '{current_status}' в {route_table}, обновление не требуется")
                conn.close()
                return True  # Возвращаем True, так как карта существует и, возможно, уже имеет нужный статус
        else:
            logger.warning(f"Карта {card_number} не найдена в таблице {route_table}")
    else:
        logger.warning(f"Не найдены поля номера или статуса в таблице {route_table}")
    
    conn.close()
    return False

@app.route('/')
def index():
    """Главная страница с приветственной заставкой"""
    current_shift = get_current_shift()
    if current_shift:
        # Если есть активная смена - сразу в рабочее меню
        return redirect(url_for('work_menu'))
    else:
        # Показываем приветственную заставку
        return get_welcome_screen()

@app.route('/create-shift', methods=['GET', 'POST'])
def create_shift():
    """Создание смены БЕЗ старшего"""
    # Проверяем, есть ли уже активная смена
    current_shift = get_current_shift()
    if current_shift:
        flash(f'Смена {current_shift["shift_number"]} на дату {current_shift["date"]} уже активна. Закройте текущую смену перед созданием новой.', 'error')
        return redirect(url_for('work_menu'))
    
    # Дополнительная проверка: есть ли какие-либо активные смены в базе данных
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM смены WHERE статус = "активна" LIMIT 1')
            active_shift = cursor.fetchone()
            conn.close()
            
            if active_shift:
                # Есть активные смены в базе данных, но их нет в сессии - восстанавливаем сессию
                session['current_shift_id'] = active_shift[0]
                # Не перенаправляем, а просто возвращаемся к основной логике
                # Пользователь будет перенаправлен в work_menu через основную проверку
        except Exception as e:
            logger.error(f"Ошибка проверки активных смен в базе данных: {e}")
            if conn:
                conn.close()
    
    if request.method == 'POST':
        date = request.form.get('date')
        shift_number = request.form.get('shift_number')
        controllers = request.form.getlist('controllers')
        
        # Валидация данных
        errors = []
        if not date:
            errors.append("Дата смены обязательна")
        if not shift_number:
            errors.append("Номер смены обязателен")
        if not controllers:
            errors.append("Необходимо выбрать хотя бы одного контролера")
        
        # Проверяем формат даты
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            errors.append("Неверный формат даты")
        
        # Проверяем номер смены
        try:
            shift_number = int(shift_number)
            if shift_number not in [1, 2]:
                errors.append("Номер смены должен быть 1 или 2")
        except ValueError:
            errors.append("Неверный номер смены")
        
        # Проверяем, что дата не в будущем
        if parsed_date.date() > datetime.now().date() + timedelta(days=1):
            errors.append("Дата смены не может быть в будущем")
        
        # Проверяем на дублирование смены
        if not errors:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT COUNT(*) FROM смены
                        WHERE дата = ? AND номер_смены = ? AND статус = 'активна'
                    ''', (date, shift_number))
                    
                    if cursor.fetchone()[0] > 0:
                        errors.append(f"Смена {shift_number} на дату {date} уже активна")
                    
                    conn.close()
                except Exception as e:
                    logger.error(f"Ошибка проверки дублирования смены: {e}")
                    errors.append("Ошибка проверки данных смены")
                    if conn:
                        conn.close()
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('create_shift'))
        
        # Автоматически закрываем просроченные смены
        auto_close_expired_shifts()
        
        # Создаем смену БЕЗ старшего
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Создаем смену как в оригинале
                cursor.execute('''
                    INSERT INTO смены (дата, номер_смены, старший, контролеры, время_начала, статус)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date, shift_number, 'Контролеры', json.dumps(controllers), datetime.now().strftime('%H:%M'), 'активна'))
                
                shift_id = cursor.lastrowid
                session['current_shift_id'] = shift_id
                conn.commit()
                conn.close()
                
                flash('Смена создана успешно!', 'success')
                return redirect(url_for('work_menu'))
            except Exception as e:
                logger.error(f"Ошибка создания смены: {e}")
                conn.close()
                flash('Ошибка создания смены', 'error')
    
    # Получаем контролеров для формы
    conn = get_db_connection()
    controllers = []
    if conn:
        cursor = conn.cursor()
        # Получаем контролеров из новой таблицы контролеры
        cursor.execute('SELECT имя FROM контролеры WHERE активен = 1 ORDER BY имя')
        controllers = [row[0] for row in cursor.fetchall()]
        conn.close()
    
    return get_create_shift_page(controllers)

def get_welcome_screen():
    """Приветственная заставка с анимацией логотипа"""
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Система контроля качества литейного производства</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                overflow: hidden;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .welcome-container {
                text-align: center;
                z-index: 10;
                position: relative;
            }
            
            .logo-container {
                margin-bottom: 30px;
                position: relative;
            }
            
            .logo {
                width: 200px;
                height: 200px;
                border-radius: 50%;
                border: 4px solid #fff;
                box-shadow: 0 0 30px rgba(255,255,255,0.3);
                animation: logoFloat 3s ease-in-out infinite, logoGlow 2s ease-in-out infinite alternate;
                background: white;
                object-fit: contain;
                padding: 10px;
                box-sizing: border-box;
            }
            
            @keyframes logoFloat {
                0%, 100% { transform: translateY(0px) rotate(0deg); }
                50% { transform: translateY(-20px) rotate(5deg); }
            }
            
            @keyframes logoGlow {
                0% { box-shadow: 0 0 30px rgba(255,255,255,0.3); }
                100% { box-shadow: 0 0 50px rgba(255,255,255,0.8), 0 0 80px rgba(255,165,0,0.4); }
            }
            
            .title {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 20px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                animation: titleSlide 1s ease-out;
            }
            
            @keyframes titleSlide {
                0% { opacity: 0; transform: translateY(50px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            .subtitle {
                font-size: 1.2em;
                margin-bottom: 40px;
                opacity: 0.9;
                animation: subtitleFade 1.5s ease-out 0.5s both;
            }
            
            @keyframes subtitleFade {
                0% { opacity: 0; }
                100% { opacity: 0.9; }
            }
            
            .start-btn {
                background: linear-gradient(45deg, #ff6b35, #f7931e);
                color: white;
                border: none;
                padding: 15px 40px;
                font-size: 1.1em;
                border-radius: 50px;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                animation: btnPulse 2s ease-in-out infinite;
                text-decoration: none;
                display: inline-block;
            }
            
            .start-btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                background: linear-gradient(45deg, #f7931e, #ff6b35);
            }
            
            @keyframes btnPulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .particles {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                z-index: 1;
            }
            
            .particle {
                position: absolute;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
                animation: particleFloat 15s linear infinite;
            }
            
            @keyframes particleFloat {
                0% {
                    transform: translateY(100vh) rotate(0deg);
                    opacity: 0;
                }
                10% {
                    opacity: 1;
                }
                90% {
                    opacity: 1;
                }
                100% {
                    transform: translateY(-100px) rotate(360deg);
                    opacity: 0;
                }
            }
            
            .foundry-icons {
                position: absolute;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }
            
            .foundry-icon {
                position: absolute;
                font-size: 2em;
                opacity: 0.1;
                animation: iconFloat 20s linear infinite;
            }
            
            @keyframes iconFloat {
                0% { transform: translateX(-100px) translateY(100vh) rotate(0deg); }
                100% { transform: translateX(100vw) translateY(-100px) rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="particles" id="particles"></div>
        <div class="foundry-icons" id="foundryIcons"></div>
        
        <div class="welcome-container">
            <div class="logo-container">
                <img src="/static/logo.png" alt="СОЭЗ" class="logo" onerror="this.style.display='none'">
            </div>
            
            <h1 class="title">🏭 СИСТЕМА КОНТРОЛЯ КАЧЕСТВА</h1>
            <p class="subtitle">Литейное производство • Металлургическое предприятие СОЭЗ</p>
            
            <a href="/create-shift" class="start-btn">
                🚀 НАЧАТЬ РАБОТУ
            </a>
        </div>
        
        <script>
            // Создание частиц
            function createParticles() {
                const particlesContainer = document.getElementById('particles');
                for (let i = 0; i < 50; i++) {
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.width = particle.style.height = (Math.random() * 4 + 2) + 'px';
                    particle.style.animationDelay = Math.random() * 15 + 's';
                    particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
                    particlesContainer.appendChild(particle);
                }
            }
            
            // Создание иконок литейного производства
            function createFoundryIcons() {
                const iconsContainer = document.getElementById('foundryIcons');
                const icons = ['⚙️', '🔥', '⚒️', '🏭', '⚡', '🔧', '⚖️', '📊'];
                
                for (let i = 0; i < 15; i++) {
                    const icon = document.createElement('div');
                    icon.className = 'foundry-icon';
                    icon.textContent = icons[Math.floor(Math.random() * icons.length)];
                    icon.style.top = Math.random() * 100 + '%';
                    icon.style.animationDelay = Math.random() * 20 + 's';
                    icon.style.animationDuration = (Math.random() * 10 + 15) + 's';
                    iconsContainer.appendChild(icon);
                }
            }
            
            // Инициализация анимаций
            createParticles();
            createFoundryIcons();
            
            // Автоматический переход через 8 секунд для демонстрации анимации
            setTimeout(() => {
                window.location.href = '/create-shift';
            }, 8000);
        </script>
    </body>
    </html>
    '''

def get_create_shift_page(controllers):
    """Страница создания смены БЕЗ старшего"""
    controllers_html = ""
    for controller in controllers:
        safe_id = controller.replace(' ', '_').replace('.', '')
        controllers_html += f'''
        <div style="margin: 5px 0;">
            <input type="checkbox" name="controllers" value="{controller}" id="{safe_id}">
            <label for="{safe_id}">{controller}</label>
        </div>
        '''
    
    # Получаем flash-сообщения
    flash_messages = ""
    with app.app_context():
        messages = session.get('_flashes', [])
        for category, message in messages:
            color = '#d4edda' if category == 'success' else '#f8d7da'
            flash_messages += f'<div style="background: {color}; padding: 10px; margin: 10px 0; border-radius: 5px;">{message}</div>'
        session.pop('_flashes', None)
    
    # Если нет контролеров, показываем сообщение
    if not controllers:
        controllers_html = '<p style="color: #6c757d; font-style: italic;">Нет доступных контролеров. Добавьте контролеров в разделе "Управление контролерами".</p>'
    
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Создание смены</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .form-group {{ margin: 20px 0; }}
            .form-group label {{ display: block; margin-bottom: 8px; font-weight: bold; }}
            .form-group input, .form-group select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .btn {{ padding: 15px 30px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .controllers-group {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; max-height: 200px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏭 Создание смены</h1>
            {flash_messages}
            
            <form method="POST">
                <div class="form-group">
                    <label>📅 Дата смены:</label>
                    <input type="date" name="date" value="{datetime.now().strftime('%Y-%m-%d')}" required>
                </div>
                
                <div class="form-group">
                    <label>🕐 Номер смены:</label>
                    <select name="shift_number" required>
                        <option value="">Выберите смену</option>
                        <option value="1">1 смена (07:00 - 19:00)</option>
                        <option value="2">2 смена (19:00 - 07:00)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>👥 Контролеры смены:</label>
                    <div class="controllers-group">
                        {controllers_html}
                    </div>
                </div>
                
                <button type="submit" class="btn">🚀 Создать смену</button>
            </form>
        </div>
    </body>
    </html>
    '''

def get_current_shift():
    """Получение текущей смены"""
    # Автоматически закрываем просроченные смены перед проверкой
    auto_close_expired_shifts()
    
    shift_id = session.get('current_shift_id')
    if not shift_id:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        # Получаем смену как в оригинале
        cursor.execute('SELECT * FROM смены WHERE id = ? AND статус = "активна"', (shift_id,))
        shift_row = cursor.fetchone()
        
        if not shift_row:
            # Если смена не активна, очищаем сессию
            session.pop('current_shift_id', None)
            conn.close()
            return None
        
        # Формируем объект смены как в оригинале
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
        logger.error(f"Ошибка получения смены: {e}")
        if conn:
            conn.close()
        return None

@app.route('/work-menu')
def work_menu():
    """Рабочее меню"""
    # Автоматически закрываем просроченные смены
    auto_close_expired_shifts()
    
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены. Создайте новую смену для продолжения работы.', 'info')
        return redirect(url_for('create_shift'))
    
    # Получаем статистику по смене
    stats = get_shift_statistics(current_shift['id'])
    current_shift['statistics'] = stats
    
    return get_work_menu_page(current_shift)

def get_statistics_html(stats):
    """Генерирует HTML для отображения статистики смены"""
    if not stats:
        return '''
        <div class="statistics-section">
            <h3>📊 Статистика смены</h3>
            <p>Данные пока отсутствуют</p>
        </div>
        '''
    
    # Топ-3 дефекта
    top_defects = ""
    if stats.get('defects'):
        top_3 = stats['defects'][:3]
        for defect in top_3:
            top_defects += f"<p>• {defect['category']}: {defect['name']} ({defect['count']})</p>"
    else:
        top_defects = "<p>Дефекты не зарегистрированы</p>"
    
    return f'''
    <div class="statistics-section">
        <h3>📊 Статистика смены</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <h4>📝 Записей</h4>
                <p style="font-size: 24px; font-weight: bold; color: #007bff;">{stats.get('total_records', 0)}</p>
            </div>
            <div class="stat-card">
                <h4>🏭 Отлито</h4>
                <p style="font-size: 24px; font-weight: bold; color: #28a745;">{stats.get('total_cast', 0)}</p>
            </div>
            <div class="stat-card">
                <h4>✅ Принято</h4>
                <p style="font-size: 24px; font-weight: bold; color: #17a2b8;">{stats.get('total_accepted', 0)}</p>
            </div>
            <div class="stat-card">
                <h4>📈 Качество</h4>
                <p style="font-size: 24px; font-weight: bold; color: #ffc107;">{stats.get('avg_quality', 0)}%</p>
            </div>
        </div>
        <div style="margin-top: 15px;">
            <h4>🔍 Основные дефекты:</h4>
            {top_defects}
        </div>
    </div>
    '''

def get_work_menu_page(shift):
    """Страница рабочего меню"""
    controllers_list = ', '.join(shift['controllers'])
    
    # Получаем flash-сообщения
    flash_messages = ""
    with app.app_context():
        messages = session.get('_flashes', [])
        for category, message in messages:
            color = '#d4edda' if category == 'success' else '#f8d7da'
            flash_messages += f'<div style="background: {color}; padding: 10px; margin: 10px 0; border-radius: 5px;">{message}</div>'
        session.pop('_flashes', None)
    
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Рабочее меню</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .shift-info {{ background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .statistics-section {{ background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
            .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .search-section {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .btn {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }}
            .card-info {{ background: #d4edda; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            input {{ padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏭 Рабочее меню</h1>
            {flash_messages}
            
            <div class="shift-info">
                <h3>📋 Информация о смене</h3>
                <p><strong>Дата:</strong> {shift['date']}</p>
                <p><strong>Смена:</strong> {shift['shift_number']} ({shift['start_time']} - активна)</p>
                <p><strong>Контролеры:</strong> {controllers_list}</p>
            </div>
            
            {get_statistics_html(shift.get('statistics'))}
            
            <div class="search-section">
                <h3>🔍 Поиск маршрутной карты</h3>
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <input type="text" id="cardNumber" placeholder="000295" maxlength="6" style="flex: 1;">
                    <button class="btn" onclick="searchCard()">🔍 Найти карту</button>
                    <button class="btn" onclick="startQRScan()" style="background: #17a2b8;">📱 Сканировать QR</button>
                </div>
                <div id="qrReader" style="display: none; margin: 10px 0;"></div>
                <div id="cardResult"></div>
            </div>
            
            <a href="/reports" class="btn" style="background: #17a2b8; text-decoration: none;">📊 Отчеты</a>
            <a href="/manage-controllers" class="btn" style="background: #6c757d; text-decoration: none;">👥 Контролеры</a>
            <button class="btn" onclick="closeShift()" style="background: #dc3545;">🔚 Закрыть смену</button>
        </div>
        
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
        <script>
        let html5QrcodeScanner = null;
        
        async function searchCard() {{
            const cardNumber = document.getElementById('cardNumber').value;
            if (!cardNumber) {{
                alert('Введите номер карты');
                return;
            }}
            
            try {{
                const response = await fetch(`/api/search-card/${{cardNumber}}`);
                const data = await response.json();
                
                const resultDiv = document.getElementById('cardResult');
                if (data.success) {{
                    const card = data.card;
                    resultDiv.innerHTML = `
                        <div class="card-info">
                            <h4>✅ Маршрутная карта найдена</h4>
                            <p><strong>Номер:</strong> ${{card.Маршрутная_карта}}</p>
                            <p><strong>Учетный номер:</strong> ${{card.Учетный_номер || 'Не указан'}}</p>
                            <p><strong>Номер кластера:</strong> ${{card.Номер_кластера || 'Не указан'}}</p>
                            <p><strong>Наименование отливки:</strong> ${{card.Наименование_отливки || 'Не указано'}}</p>
                            <p><strong>Тип литниковой системы:</strong> ${{card.Тип_литниковой_системы || 'Не указан'}}</p>
                            <button class="btn" onclick="proceedToInput('${{cardNumber}}')">➡️ Перейти к вводу контроля</button>
                        </div>
                    `;
                }} else {{
                    if (data.already_processed) {{
                        resultDiv.innerHTML = '<div style="background: #fff3cd; padding: 15px; border-radius: 5px; color: #856404;">⚠️ ' + data.error + '</div>';
                    }} else {{
                        resultDiv.innerHTML = '<div style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24;">❌ Карта не найдена</div>';
                    }}
                }}
            }} catch (error) {{
                alert('Ошибка поиска: ' + error.message);
            }}
        }}
        
        function startQRScan() {{
            const qrReaderDiv = document.getElementById('qrReader');
            
            if (html5QrcodeScanner) {{
                // Останавливаем сканирование
                html5QrcodeScanner.clear();
                html5QrcodeScanner = null;
                qrReaderDiv.style.display = 'none';
                return;
            }}
            
            qrReaderDiv.style.display = 'block';
            qrReaderDiv.innerHTML = '<div id="qr-reader" style="width: 100%;"></div><button onclick="stopQRScan()" class="btn" style="background: #dc3545; margin-top: 10px;">Остановить сканирование</button>';
            
            html5QrcodeScanner = new Html5Qrcode("qr-reader");
            
            const config = {{
                fps: 10,
                qrbox: {{ width: 250, height: 250 }}
            }};
            
            html5QrcodeScanner.start(
                {{ facingMode: "environment" }}, // Задняя камера
                config,
                (decodedText, decodedResult) => {{
                    // Успешное сканирование
                    document.getElementById('cardNumber').value = decodedText;
                    stopQRScan();
                    searchCard(); // Автоматически ищем карту
                }},
                (errorMessage) => {{
                    // Ошибка сканирования (можно игнорировать)
                }}
            ).catch(err => {{
                console.error('Ошибка запуска камеры:', err);
                alert('Не удалось запустить камеру. Проверьте разрешения.');
                qrReaderDiv.style.display = 'none';
            }});
        }}
        
        function stopQRScan() {{
            if (html5QrcodeScanner) {{
                html5QrcodeScanner.stop().then(() => {{
                    html5QrcodeScanner.clear();
                    html5QrcodeScanner = null;
                    document.getElementById('qrReader').style.display = 'none';
                }}).catch(err => {{
                    console.error('Ошибка остановки сканера:', err);
                }});
            }}
        }}
        
        function proceedToInput(cardNumber) {{
            window.location.href = `/control-input/${{cardNumber}}`;
        }}
        
        async function closeShift() {{
            if (confirm('Закрыть смену?')) {{
                try {{
                    const response = await fetch('/api/close-shift', {{ 
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }}
                    }});
                    const data = await response.json();
                    if (data.success) {{
                        alert('Смена закрыта успешно!');
                        window.location.href = '/';
                    }} else {{
                        alert('Ошибка закрытия смены: ' + (data.error || 'Неизвестная ошибка'));
                    }}
                }} catch (error) {{
                    alert('Ошибка: ' + error.message);
                }}
            }}
        }}
        
        // Автоматическое обновление статистики каждые 30 секунд
        async function updateStatistics() {{
            try {{
                const response = await fetch('/api/shifts/current');
                const data = await response.json();
                if (data.success && data.shift.statistics) {{
                    const stats = data.shift.statistics;
                    // Обновляем статистику на странице
                    const statCards = document.querySelectorAll('.stat-card p');
                    if (statCards.length >= 4) {{
                        statCards[0].textContent = stats.total_records || 0;
                        statCards[1].textContent = stats.total_cast || 0;
                        statCards[2].textContent = stats.total_accepted || 0;
                        statCards[3].textContent = (stats.avg_quality || 0) + '%';
                    }}
                }}
            }} catch (error) {{
                console.log('Ошибка обновления статистики:', error);
            }}
        }}
        
        // Запускаем обновление статистики каждые 30 секунд
        setInterval(updateStatistics, 30000);
        </script>
    </body>
    </html>
    '''

def check_card_already_processed(card_number):
    """Проверяет, была ли карта уже обработана ГЛОБАЛЬНО во всей системе"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # ГЛОБАЛЬНАЯ проверка - ищем карту во ВСЕХ записях, не только в текущей смене
        # ГЛОБАЛЬНАЯ проверка в кириллических таблицах
        cursor.execute('''
            SELECT COUNT(*) FROM записи_контроля 
            WHERE номер_маршрутной_карты = ?
        ''', (card_number,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"Ошибка проверки карты: {e}")
        if conn:
            conn.close()
        return False

@app.route('/api/search-card/<card_number>')
def api_search_card(card_number):
    """API поиска карты с проверкой на повторный ввод"""
    try:
        # Валидация номера маршрутной карты
        if not validate_route_card_number(card_number):
            from flask import has_request_context
            request_obj = request if has_request_context() else None
            error_handler.log_user_error(f"Неверный формат номера маршрутной карты в API: {card_number}", request_obj)
            return jsonify({
                'success': False,
                'error': 'Неверный формат номера маршрутной карты. Ожидается 6 цифр.',
                'error_id': f"val_{id(card_number)}"
            }), 400
        
        # Проверяем, не была ли карта уже обработана
        if check_card_already_processed(card_number):
            return jsonify({
                'success': False,
                'error': 'Данная маршрутная карта уже была обработана в системе!',
                'already_processed': True
            }), 400
        
        card_data = search_route_card_in_foundry(card_number)
        
        if card_data:
            log_operation(logger, "Успешный поиск маршрутной карты через API", {
                "card_number": card_number,
                "user": request.remote_addr
            })
            return jsonify({'success': True, 'card': card_data})
        else:
            log_operation(logger, "Неудачный поиск маршрутной карты через API", {
                "card_number": card_number,
                "user": request.remote_addr
            })
            return jsonify({'success': False, 'error': 'Карта не найдена'}), 404
    
    except Exception as e:
        error_id = f"api_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        log_error_with_context(logger, e, {"card_number": card_number, "error_id": error_id})
        from flask import has_request_context
        request_obj = request if has_request_context() else None
        error_handler.log_user_error(f"Ошибка API поиска маршрутной карты {card_number}: {str(e)}", request_obj)
        return jsonify({
            'success': False,
            'error': 'Ошибка поиска маршрутной карты',
            'error_id': error_id
        }), 500

@app.route('/input-control')
def input_control():
    """Страница ввода контроля с ДЕТАЛИЗИРОВАННЫМИ дефектами"""
    current_shift = get_current_shift()
    if not current_shift:
        return redirect(url_for('create_shift'))
    
    route_card = request.args.get('card')
    foundry_data = None
    
    if route_card:
        foundry_data = search_route_card_in_foundry(route_card)
    
    return get_input_control_page(current_shift, route_card, foundry_data)

def get_input_control_page(shift, route_card, foundry_data):
    """Страница ввода с ДЕТАЛИЗИРОВАННЫМИ дефектами"""
    
    # Информация из foundry.db
    foundry_info = ""
    if foundry_data:
        foundry_info = f'''
        <div class="card-info">
            <h4>✅ Данные из foundry.db</h4>
            <p><strong>Номер маршрутной карты:</strong> {foundry_data.get('Маршрутная_карта', 'Не указан')}</p>
            <p><strong>Учетный номер:</strong> {foundry_data.get('Учетный_номер', 'Не указан')}</p>
            <p><strong>Номер кластера:</strong> {foundry_data.get('Номер_кластера', 'Не указан')}</p>
            <p><strong>Наименование отливки:</strong> {foundry_data.get('Наименование_отливки', 'Не указано')}</p>
            <p><strong>Тип литниковой системы:</strong> {foundry_data.get('Тип_литниковой_системы', 'Не указан')}</p>
        </div>
        '''
    

    
    # ДЕТАЛИЗИРОВАННЫЕ дефекты из кириллической БД
    defects_html = ""
    
    # Получаем типы дефектов из кириллической схемы
    conn = get_db_connection()
    defects_by_category = {}
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT td.id, td.название, cd.название as категория
                FROM типы_дефектов td
                JOIN категории_дефектов cd ON td.категория_id = cd.id
                WHERE td.активен = 1
                ORDER BY
                    CASE cd.название
                        WHEN 'Второй сорт' THEN 1
                        WHEN 'Доработка' THEN 2
                        WHEN 'Окончательный брак' THEN 3
                        ELSE 4
                    END,
                    td.название
            ''')
            
            for row in cursor.fetchall():
                category = row[2]
                if category not in defects_by_category:
                    defects_by_category[category] = []
                # Проверяем, что дефект не дублируется в этой категории
                defect_data = {'id': row[0], 'name': row[1]}
                if defect_data not in defects_by_category[category]:
                    defects_by_category[category].append(defect_data)
            
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка получения дефектов: {e}")
            if conn:
                conn.close()
    
    # Генерируем HTML для дефектов
    for category, defects in defects_by_category.items():
        # Теперь категории уже на русском, просто используем их
        category_title = category
        
        defects_html += f'''
            <div class="defect-category">
                <h4>{category_title}</h4>
                <div class="defect-types">
        '''
        
        for defect in defects:
            safe_defect_name = defect['name'].replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
            safe_id = f"{category.replace(' ', '_')}_{safe_defect_name}"
            defects_html += f'''
                    <div class="defect-item">
                        <label>{defect['name']}:</label>
                        <input type="number" name="defect_{safe_id}" min="0" placeholder="0" onchange="calculateAccepted()" class="defect-input">
                    </div>
            '''
        
        # Добавляем поля для новых дефектов
        safe_category_name = category.replace(' ', '_').replace('-', '_')
        defects_html += f'''
                    <div class="defect-item" style="border-top: 1px solid #ddd; padding-top: 8px; margin-top: 8px;">
                        <label>➕ Новый дефект:</label>
                        <input type="text" name="new_defect_{safe_category_name}" placeholder="Название нового дефекта" style="margin-bottom: 4px;">
                        <input type="number" name="new_defect_{safe_category_name}_qty" min="0" placeholder="Количество" onchange="calculateAccepted()">
                    </div>
                </div>
            </div>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Ввод данных контроля</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 10px; background: #f5f5f5; font-size: 14px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 15px; border-radius: 8px; }}
            .form-group {{ margin: 10px 0; }}
            .form-group label {{ display: block; margin-bottom: 4px; font-weight: bold; font-size: 13px; }}
            .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; font-size: 13px; }}
            .btn {{ padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }}
            .card-info {{ background: #d4edda; padding: 10px; border-radius: 5px; margin: 8px 0; font-size: 12px; }}
            .defects-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 15px 0; }}
            .defect-category {{ background: #f8f9fa; padding: 8px; border-radius: 5px; border-left: 3px solid #007bff; }}
            .defect-types {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; max-height: 250px; overflow-y: auto; }}
            .defect-item {{ margin: 2px 0; display: flex; flex-direction: column; }}
            .defect-item label {{ font-size: 10px; margin-bottom: 1px; font-weight: 500; }}
            .defect-item input {{ padding: 3px; font-size: 11px; width: 100%; box-sizing: border-box; }}
            .defect-category h4 {{ margin: 0 0 6px 0; color: #007bff; font-size: 12px; text-align: center; }}
            .main-inputs {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .header h1 {{ margin: 0; font-size: 18px; }}
            .card-number {{ background: #007bff; color: white; padding: 5px 10px; border-radius: 4px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Ввод данных контроля</h1>
                <div class="card-number">Карта: {route_card or 'Не указана'}</div>
            </div>
            
            {foundry_info}
            
            <form method="POST" action="/save-control" onsubmit="return validateForm()">
                <input type="hidden" name="route_card" id="route_card" value="{route_card or ''}">
                
                <div class="main-inputs">
                    <div class="form-group">
                        <label>🏭 Всего отлито:</label>
                        <input type="number" id="total_cast" name="total_cast" required min="1" onchange="calculateAccepted()">
                    </div>
                    
                    <div class="form-group">
                        <label>✅ Всего принято:</label>
                        <input type="number" id="total_accepted" name="total_accepted" readonly style="background: #f8f9fa; color: #6c757d;">
                        <small style="color: #6c757d;">Автоматический расчет</small>
                    </div>
                </div>
                
                <h3 style="text-align: center; margin: 20px 0 10px 0;">🔍 ДЕФЕКТЫ ПО КАТЕГОРИЯМ</h3>
                <div class="defects-container">
                    {defects_html}
                </div>
                
                <input type="hidden" name="controller" value="{shift['controllers'][0] if shift['controllers'] else 'Контролер'}">
                
                <div class="form-group">
                    <label>📝 Примечания:</label>
                    <textarea name="notes" rows="3"></textarea>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="btn">💾 Сохранить запись</button>
                    <a href="/work-menu" class="btn" style="background: #6c757d; text-decoration: none; margin-left: 10px;">🔙 Назад</a>
                </div>
            </form>
        </div>
        
        <script>
        function calculateAccepted() {{
            const totalCast = parseInt(document.getElementById('total_cast').value) || 0;
            const defectInputs = document.querySelectorAll('.defect-input, input[name*="new_defect_"][name*="_qty"]');
            
            let totalDefects = 0;
            defectInputs.forEach(input => {{
                const value = parseInt(input.value) || 0;
                if (value < 0) {{
                    input.value = 0;
                    showWarning('Количество дефектов не может быть отрицательным');
                }}
                totalDefects += Math.max(0, value);
            }});
            
            const totalAccepted = Math.max(0, totalCast - totalDefects);
            document.getElementById('total_accepted').value = totalAccepted;
            
            // Показываем предупреждения
            if (totalCast > 0) {{
                const rejectRate = (totalDefects / totalCast) * 100;
                const qualityRate = (totalAccepted / totalCast) * 100;
                
                updateQualityIndicator(qualityRate, rejectRate);
                
                if (rejectRate > 50) {{
                    showWarning(`Очень высокий процент брака: ${{rejectRate.toFixed(1)}}%`);
                }} else if (rejectRate > 30) {{
                    showWarning(`Высокий процент брака: ${{rejectRate.toFixed(1)}}%`);
                }}
                
                if (totalDefects > totalCast) {{
                    showError('Количество дефектов превышает количество отлитых деталей!');
                }}
            }}
        }}
        
        function updateQualityIndicator(qualityRate, rejectRate) {{
            let indicator = document.getElementById('quality-indicator');
            if (!indicator) {{
                // Создаем индикатор качества если его нет
                indicator = document.createElement('div');
                indicator.id = 'quality-indicator';
                indicator.style.cssText = `
                    position: fixed; top: 10px; right: 10px;
                    background: white; padding: 10px; border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000;
                    min-width: 200px; font-size: 14px;
                `;
                document.body.appendChild(indicator);
            }}
            
            let color = '#28a745'; // зеленый
            if (qualityRate < 70) color = '#dc3545'; // красный
            else if (qualityRate < 85) color = '#ffc107'; // желтый
            
            indicator.innerHTML = `
                <div style="text-align: center;">
                    <div style="font-weight: bold; color: ${{color}};">
                        📊 Качество: ${{qualityRate.toFixed(1)}}%
                    </div>
                    <div style="font-size: 12px; color: #666;">
                        Брак: ${{rejectRate.toFixed(1)}}%
                    </div>
                </div>
            `;
        }}
        
        // Обновляем значение скрытого поля route_card при загрузке страницы
        window.onload = function() {{
            // Если на странице есть карта, обновляем значение скрытого поля
            const cardNumberElement = document.getElementById('cardNumber');
            if (cardNumberElement && cardNumberElement.value) {{
                const routeCardField = document.getElementById('route_card');
                if (routeCardField) {{
                    routeCardField.value = cardNumberElement.value;
                }}
            }}
        }}
        
        function showWarning(message) {{
            showNotification(message, 'warning');
        }}
        
        function showError(message) {{
            showNotification(message, 'error');
        }}
        
        function showNotification(message, type) {{
            const notification = document.createElement('div');
            const bgColor = type === 'error' ? '#f8d7da' : '#fff3cd';
            const textColor = type === 'error' ? '#721c24' : '#856404';
            
            notification.style.cssText = `
                position: fixed; top: 70px; right: 10px; 
                background: ${{bgColor}}; color: ${{textColor}};
                padding: 10px 15px; border-radius: 5px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1001;
                max-width: 300px; font-size: 13px;
                border: 1px solid ${{type === 'error' ? '#f5c6cb' : '#ffeaa7'}};
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            // Автоматически убираем уведомление через 5 секунд
            setTimeout(() => {{
                if (notification.parentNode) {{
                    notification.parentNode.removeChild(notification);
                }}
            }}, 5000);
        }}
        
        function validateForm() {{
            const totalCast = parseInt(document.getElementById('total_cast').value) || 0;
            const totalAccepted = parseInt(document.getElementById('total_accepted').value) || 0;
            
            if (totalCast <= 0) {{
                showError('Количество отлитых деталей должно быть больше 0');
                return false;
            }}
            
            if (totalAccepted < 0) {{
                showError('Количество принятых деталей не может быть отрицательным');
                return false;
            }}
            
            if (totalAccepted > totalCast) {{
                showError('Количество принятых деталей не может превышать количество отлитых');
                return false;
            }}
            
            return true;
        }}
        
        // Навигация стрелками по полям ввода
        function setupArrowNavigation() {{
            const inputs = document.querySelectorAll('input[type="number"], textarea, input[type="text"]');
            const inputsArray = Array.from(inputs).filter(input => !input.readOnly && !input.disabled);
            
            console.log('Найдено полей для навигации:', inputsArray.length);
            
            inputsArray.forEach((input, index) => {{
                input.addEventListener('keydown', function(e) {{
                    let targetIndex = -1;
                    
                    switch(e.key) {{
                        case 'ArrowUp':
                            e.preventDefault();
                            targetIndex = Math.max(0, index - 1);
                            break;
                        case 'ArrowDown':
                            e.preventDefault();
                            targetIndex = Math.min(inputsArray.length - 1, index + 1);
                            break;
                        case 'ArrowLeft':
                            if (input.selectionStart === 0) {{
                                e.preventDefault();
                                targetIndex = Math.max(0, index - 1);
                            }}
                            break;
                        case 'ArrowRight':
                            if (input.selectionStart === input.value.length) {{
                                e.preventDefault();
                                targetIndex = Math.min(inputsArray.length - 1, index + 1);
                            }}
                            break;
                        case 'Enter':
                            e.preventDefault();
                            targetIndex = Math.min(inputsArray.length - 1, index + 1);
                            break;
                    }}
                    
                    if (targetIndex >= 0 && targetIndex < inputsArray.length) {{
                        inputsArray[targetIndex].focus();
                        if (inputsArray[targetIndex].type === 'number' || inputsArray[targetIndex].type === 'text') {{
                            inputsArray[targetIndex].select();
                        }}
                    }}
                }});
            }});
        }}
        
        // Обработка новых дефектов
        function setupNewDefectHandlers() {{
            const newDefectInputs = document.querySelectorAll('input[name*="new_defect_"][name*="_qty"]');
            newDefectInputs.forEach(input => {{
                input.addEventListener('input', calculateAccepted);
            }});
        }}
        
        // Автоматический расчет при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {{
            calculateAccepted();
            setupArrowNavigation();
            setupNewDefectHandlers();
            
            // Добавляем обработчики для всех полей дефектов
            const allDefectInputs = document.querySelectorAll('.defect-input, input[name*="new_defect_"][name*="_qty"]');
            allDefectInputs.forEach(input => {{
                input.addEventListener('input', calculateAccepted);
            }});
        }});
        </script>
    </body>
    </html>
    '''

@app.route('/save-control', methods=['POST'])
def save_control():
    """Сохранение записи контроля с улучшенной валидацией"""
    try:
        current_shift = get_current_shift()
        if not current_shift:
            flash('Нет активной смены', 'error')
            return redirect(url_for('create_shift'))
        
        # Валидация пользовательского ввода
        route_card = request.form.get('route_card', '').strip()
        total_cast_str = request.form.get('total_cast', '0').strip()
        total_accepted_str = request.form.get('total_accepted', '0').strip()
        notes = request.form.get('notes', '').strip()
        
        # Проверяем обязательные поля
        if not route_card:
            flash('Номер маршрутной карты обязателен', 'error')
            return redirect(url_for('input_control', card=route_card))
        
        # Валидация номера маршрутной карты
        if not validate_route_card_number(route_card):
            flash('Неверный формат номера маршрутной карты. Ожидается 6 цифр.', 'error')
            return redirect(url_for('input_control', card=route_card))
        
        # Валидация числовых значений
        is_valid, error_msg = validate_positive_integer(total_cast_str, 'Всего отлито')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('input_control', card=route_card))
        
        is_valid, error_msg = validate_positive_integer(total_accepted_str, 'Всего принято')
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('input_control', card=route_card))
        
        total_cast = int(total_cast_str)
        total_accepted = int(total_accepted_str)
        
        if total_accepted > total_cast:
            flash('Количество принятых деталей не может превышать количество отлитых', 'error')
            return redirect(url_for('input_control', card=route_card))
        
        controller = current_shift['controllers'][0] if current_shift['controllers'] else 'Контролер'
        
        # Собираем данные о дефектах для валидации
        defects_data = {}
        new_defects = {}
        
        for key, value in request.form.items():
            if key.startswith('defect_') and value and value.strip():
                try:
                    defect_value = int(value)
                    if defect_value < 0:
                        flash(f'Количество дефектов не может быть отрицательным: {key}', 'error')
                        return redirect(url_for('input_control', card=route_card))
                    if defect_value > 0:
                        defect_key = key.replace('defect_', '')
                        defects_data[defect_key] = defect_value
                except ValueError:
                    logger.warning(f"Некорректное значение дефекта {key}: {value}")
                    flash(f'Некорректное значение дефекта: {key}', 'error')
                    return redirect(url_for('input_control', card=route_card))
            elif key.startswith('new_defect_') and not key.endswith('_qty') and value and value.strip():
                # Новый дефект - название
                category = key.replace('new_defect_', '')
                qty_key = f'new_defect_{category}_qty'
                quantity = request.form.get(qty_key, '0').strip()
                if quantity:
                    try:
                        qty_value = int(quantity)
                        if qty_value < 0:
                            flash(f'Количество новых дефектов не может быть отрицательным: {qty_key}', 'error')
                            return redirect(url_for('input_control', card=route_card))
                        if qty_value > 0:
                            new_defects[f"{category}_{value}"] = {
                                'category': category,
                                'name': value.strip(),
                                'quantity': qty_value
                            }
                    except ValueError:
                        logger.warning(f"Некорректное значение нового дефекта {qty_key}: {quantity}")
                        flash(f'Некорректное значение нового дефекта: {qty_key}', 'error')
                        return redirect(url_for('input_control', card=route_card))
        
        # Добавляем новые дефекты к общим данным
        for key, defect_info in new_defects.items():
            defects_data[key] = defect_info['quantity']
        
        # Валидация данных
        errors, warnings = validate_control_data(total_cast, total_accepted, defects_data)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('input_control', card=route_card))
        
        # Показываем предупреждения, но продолжаем сохранение
        for warning in warnings:
            flash(warning, 'warning')
        
        conn = get_db_connection()
        if not conn:
            flash('Ошибка подключения к БД', 'error')
            return redirect(url_for('work_menu'))
        
        cursor = conn.cursor()
        
        # Сохраняем запись контроля
        cursor.execute('''
            INSERT INTO записи_контроля
            (смена_id, номер_маршрутной_карты, всего_отлито, всего_принято, контролер, заметки)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (current_shift['id'], route_card, total_cast, total_accepted, controller, notes))
        
        record_id = cursor.lastrowid
        defects_summary = []
        
        # Обрабатываем существующие дефекты
        for key, value in request.form.items():
            if key.startswith('defect_') and value and value.strip():
                try:
                    defect_value = int(value)
                    if defect_value > 0:
                        # Извлекаем название категории и дефекта из ключа
                        # Формат ключа: defect_категория_дефект_имя
                        # Например: defect_Второй_сорт_Раковины
                        key_parts = key.replace('defect_', '').split('_', 1)
                        if len(key_parts) == 2:
                            category, defect_name = key_parts
                            # Восстанавливаем оригинальное имя дефекта с пробелами
                            defect_name = defect_name.replace('_', ' ')
                            
                            # Находим тип дефекта
                            cursor.execute('''
                                SELECT td.id
                                FROM типы_дефектов td
                                JOIN категории_дефектов cd ON td.категория_id = cd.id
                                WHERE cd.название = ? AND td.название = ?
                            ''', (category, defect_name))
                            
                            defect_type = cursor.fetchone()
                            if defect_type:
                                # Сохраняем дефект
                                cursor.execute('''
                                    INSERT INTO дефекты_записей (запись_контроля_id, тип_дефекта_id, количество)
                                    VALUES (?, ?, ?)
                                ''', (record_id, defect_type[0], defect_value))
                                
                                defects_summary.append(f"{category}: {defect_name} ({defect_value})")
                except ValueError:
                    logger.warning(f"Некорректное значение дефекта {key}: {value}")
                    continue
        
        # Обрабатываем новые типы дефектов
        for defect_key, defect_info in new_defects.items():
            category = defect_info['category']
            
            # Создаем новый тип дефекта
            # Сначала получаем ID категории
            cursor.execute('SELECT id FROM категории_дефектов WHERE название = ?', (category,))
            category_row = cursor.fetchone()
            if category_row:
                category_id = category_row[0]
                cursor.execute('''
                    INSERT OR IGNORE INTO типы_дефектов (категория_id, название)
                    VALUES (?, ?)
                ''', (category_id, defect_info['name']))
            
            # Получаем ID дефекта (созданного или существующего)
            cursor.execute('''
                SELECT td.id
                FROM типы_дефектов td
                JOIN категории_дефектов cd ON td.категория_id = cd.id
                WHERE cd.название = ? AND td.название = ?
            ''', (category, defect_info['name']))
            
            defect_type = cursor.fetchone()
            if defect_type:
                # Сохраняем дефект
                cursor.execute('''
                    INSERT INTO дефекты_записей (запись_контроля_id, тип_дефекта_id, количество)
                    VALUES (?, ?, ?)
                ''', (record_id, defect_type[0], defect_info['quantity']))
                
                defects_summary.append(f"{category}: {defect_info['name']} ({defect_info['quantity']})")
        
        conn.commit()
        conn.close()
        
        # Улучшенное обновление статуса маршрутной карты
        if route_card:
            defects_text = '; '.join(defects_summary) if defects_summary else 'Без дефектов'
            status_updated = update_route_card_status_enhanced(route_card, total_cast, total_accepted, defects_text)
            
            if status_updated:
                logger.info(f"Статус карты {route_card} успешно обновлен")
                flash('Статус маршрутной карты обновлен', 'info')
            else:
                logger.warning(f"Не удалось обновить статус карты {route_card}")
                flash('Не удалось обновить статус маршрутной карты', 'warning')
        
        # Формируем сообщение об успешном сохранении
        quality_rate = (total_accepted / total_cast * 100) if total_cast > 0 else 0
        success_msg = f'Запись сохранена! Качество: {quality_rate:.1f}% ({total_accepted}/{total_cast})'
        flash(success_msg, 'success')
        logger.info(f"Запись контроля для карты {route_card} успешно сохранена")
        
        return redirect(url_for('work_menu'))
        
    except ValueError as e:
        logger.error(f"Ошибка валидации данных: {e}")
        logger.error(traceback.format_exc())
        flash('Ошибка в данных. Проверьте правильность ввода чисел.', 'error')
        return redirect(url_for('input_control', card=request.form.get('route_card', '')))
    except Exception as e:
        logger.error(f"Ошибка сохранения записи: {e}")
        logger.error(traceback.format_exc())
        flash(f'Ошибка сохранения: {str(e)}', 'error')
        return redirect(url_for('work_menu'))

@app.route('/static/<path:filename>')
def static_files(filename):
    """Обслуживание статических файлов"""
    from flask import send_from_directory
    return send_from_directory('static', filename)

@app.route('/close-shift', methods=['POST'])
def close_shift():
    """Закрытие смены"""
    current_shift = get_current_shift()
    if not current_shift:
        return jsonify({'success': False, 'error': 'Нет активной смены'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Ошибка БД'})
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE смены 
            SET статус = 'закрыта', время_окончания = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%H:%M'), current_shift['id']))
        
        conn.commit()
        conn.close()
        
        session.pop('current_shift_id', None)
        return jsonify({'success': True, 'message': 'Смена закрыта'})
    except Exception as e:
        logger.error(f"Ошибка закрытия смены: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reports')
def reports():
    """Просмотр отчетов по сменам"""
    conn = get_db_connection()
    if not conn:
        return "Ошибка подключения к БД"
    
    try:
        cursor = conn.cursor()
        # Получаем данные по сменам с записями
        # Получаем данные по сменам с записями из кириллических таблиц
        cursor.execute('''
            SELECT
                s.id, s.дата, s.номер_смены,
                s.контролеры,
                s.время_начала, s.время_окончания, s.статус,
                COUNT(zk.id) as records_count,
                SUM(zk.всего_отлито) as total_cast,
                SUM(zk.всего_принято) as total_accepted
            FROM смены s
            LEFT JOIN записи_контроля zk ON s.id = zk.смена_id
            GROUP BY s.id
            ORDER BY s.дата DESC
        ''')
        
        shifts = cursor.fetchall()
        conn.close()
        
        return get_reports_page(shifts)
        
    except Exception as e:
        logger.error(f"Ошибка получения отчетов: {e}")
        if conn:
            conn.close()
        return f"Ошибка: {str(e)}"

def get_reports_page(shifts):
    """Страница отчетов"""
    shifts_html = ""
    
    for shift in shifts:
        # Контролеры теперь в колонке shift[3] как JSON строка
        controllers_json = shift[3] if shift[3] else '[]'
        try:
            controllers_list = json.loads(controllers_json)
            controllers_str = ', '.join(controllers_list) if controllers_list else 'Не указаны'
        except json.JSONDecodeError:
            controllers_str = 'Не указаны'
        
        status_color = '#28a745' if shift[6] == 'активна' else '#6c757d'
        status_text = 'Активна' if shift[6] == 'активна' else 'Закрыта'
        
        efficiency = 0
        if shift[7] and shift[8]:  # total_cast и total_accepted
            efficiency = round((shift[8] / shift[7]) * 100, 1) if shift[7] > 0 else 0
        
        shifts_html += f'''
        <tr>
            <td>{shift[1]}</td>
            <td>{shift[2]}</td>
            <td>{controllers_str}</td>
            <td>{shift[4]} - {shift[5] or 'активна'}</td>
            <td><span style="color: {status_color};">{status_text}</span></td>
            <td>{shift[7] or 0}</td>
            <td>{shift[8] or 0}</td>
            <td>{shift[9] or 0}</td>
            <td>{efficiency}%</td>
            <td><a href="/shift-details/{shift[0]}" class="btn-small">Детали</a></td>
        </tr>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Отчеты по сменам</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background: #f8f9fa; font-weight: bold; }}
            .btn {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }}
            .btn-small {{ padding: 5px 10px; background: #17a2b8; color: white; border: none; border-radius: 3px; text-decoration: none; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Отчеты по сменам</h1>
            
            <a href="/work-menu" class="btn">🔙 Назад к работе</a>
            
            <table>
                <thead>
                    <tr>
                        <th>Дата</th>
                        <th>Смена</th>
                        <th>Контролеры</th>
                        <th>Время</th>
                        <th>Статус</th>
                        <th>Записей</th>
                        <th>Отлито</th>
                        <th>Принято</th>
                        <th>Эффективность</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
                    {shifts_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    '''

# ===== УПРАВЛЕНИЕ КОНТРОЛЕРАМИ =====

@app.route('/manage-controllers')
def manage_controllers():
    """Страница управления контролерами"""
    conn = get_db_connection()
    controllers = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, имя, активен FROM контролеры ORDER BY имя')
            controllers = [{'id': row[0], 'name': row[1], 'active': row[2]} for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка получения списка контролеров: {e}")
            from flask import has_request_context
            request_obj = request if has_request_context() else None
            error_handler.log_user_error(f"Ошибка получения списка контролеров: {str(e)}", request_obj)
            if conn:
                conn.close()
            controllers = []
    
    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Управление контролерами</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
            .controller-item {{ display: flex; justify-content: space-between; align-items: center; padding: 10px; border: 1px solid #ddd; margin: 5px 0; border-radius: 5px; }}
            .btn {{ padding: 8px 15px; margin: 0 5px; border: none; border-radius: 5px; cursor: pointer; }}
            .btn-success {{ background: #28a745; color: white; }}
            .btn-danger {{ background: #dc3545; color: white; }}
            .btn-primary {{ background: #007bff; color: white; }}
            .add-form {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            input {{ padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👥 Управление контролерами</h1>
            
            <div class="add-form">
                <h3>➕ Добавить контролера</h3>
                <form method="POST" action="/add-controller">
                    <input type="text" name="controller_name" placeholder="Имя контролера" required style="width: 300px;">
                    <button type="submit" class="btn btn-success">Добавить</button>
                </form>
            </div>
            
            <h3>📋 Список контролеров</h3>
            {''.join([f'''
                <div class="controller-item">
                    <span>{controller['name']} {'(активен)' if controller['active'] else '(отключен)'}</span>
                    <div>
                        <button class="btn {'btn-danger' if controller['active'] else 'btn-success'}"
                                onclick="toggleController({controller['id']}, {1 - controller['active']})">
                            {'Отключить' if controller['active'] else 'Включить'}
                        </button>
                        <button class="btn btn-danger" onclick="deleteController({controller['id']})">Удалить</button>
                    </div>
                </div>
            ''' for controller in controllers])}
            
            <a href="/work-menu" class="btn btn-primary" style="text-decoration: none; margin-top: 20px;">← Назад к меню</a>
        </div>
        
        <script>
        async function toggleController(id, newStatus) {{
            try {{
                const response = await fetch('/toggle-controller', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ id: id, active: newStatus }})
                }});
                if (response.ok) {{
                    location.reload();
                }} else {{
                    const data = await response.json();
                    alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                }}
            }} catch (error) {{
                alert('Ошибка: ' + error.message);
            }}
        }}
        
        async function deleteController(id) {{
            if (confirm('Удалить контролера?')) {{
                try {{
                    const response = await fetch('/delete-controller', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: id }})
                    }});
                    if (response.ok) {{
                        location.reload();
                    }} else {{
                        const data = await response.json();
                        alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                    }}
                }} catch (error) {{
                    alert('Ошибка: ' + error.message);
                }}
            }}
        }}
        </script>
    </body>
    </html>
    '''

@app.route('/add-controller', methods=['POST'])
def add_controller():
    """Добавление нового контролера"""
    name = request.form.get('controller_name')
    if not name:
        flash('Введите имя контролера', 'error')
        return redirect(url_for('manage_controllers'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO контролеры (имя) VALUES (?)', (name,))
            conn.commit()
            conn.close()
            flash('Контролер добавлен', 'success')
            log_operation_enhanced("Добавление контролера", {
                "controller_name": name,
                "user": request.remote_addr
            })
            logger.info(f"Контролер {name} добавлен")
        except Exception as e:
            logger.error(f"Ошибка добавления контролера: {e}")
            from flask import has_request_context
            request_obj = request if has_request_context() else None
            error_handler.log_user_error(f"Ошибка добавления контролера {name}: {str(e)}", request_obj)
            flash('Ошибка добавления контролера', 'error')
            if conn:
                conn.close()
    
    return redirect(url_for('manage_controllers'))

@app.route('/toggle-controller', methods=['POST'])
def toggle_controller():
    """Включение/отключение контролера"""
    data = request.get_json()
    controller_id = data.get('id')
    active = data.get('active')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE контролеры SET активен = ? WHERE id = ?', (active, controller_id))
            conn.commit()
            conn.close()
            log_operation_enhanced("Изменение статуса контролера", {
                "controller_id": controller_id,
                "new_status": "активен" if active else "отключен",
                "user": request.remote_addr
            })
            logger.info(f"Статус контролера {controller_id} изменен на {'активен' if active else 'отключен'}")
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Ошибка изменения статуса контролера: {e}")
            from flask import has_request_context
            request_obj = request if has_request_context() else None
            error_handler.log_user_error(f"Ошибка изменения статуса контролера {controller_id}: {str(e)}", request_obj)
            if conn:
                conn.close()
    
    return jsonify({'success': False}), 500

@app.route('/delete-controller', methods=['POST'])
def delete_controller():
    """Удаление контролера"""
    data = request.get_json()
    controller_id = data.get('id')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM контролеры WHERE id = ?', (controller_id,))
            conn.commit()
            conn.close()
            log_operation_enhanced("Удаление контролера", {
                "controller_id": controller_id,
                "user": request.remote_addr
            })
            logger.info(f"Контролер {controller_id} удален")
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Ошибка удаления контролера: {e}")
            from flask import has_request_context
            request_obj = request if has_request_context() else None
            error_handler.log_user_error(f"Ошибка удаления контролера {controller_id}: {str(e)}", request_obj)
            if conn:
                conn.close()
    
    return jsonify({'success': False}), 500

# ===== ФУНКЦИИ ВАЛИДАЦИИ =====

def validate_control_data(total_cast, total_accepted, defects_data):
    """Валидация данных контроля качества"""
    errors = []
    warnings = []
    
    # Проверка основных данных
    if not total_cast or total_cast <= 0:
        errors.append("Количество отлитых деталей должно быть больше 0")
    
    if total_accepted < 0:
        errors.append("Количество принятых деталей не может быть отрицательным")
    
    if total_accepted > total_cast:
        errors.append("Количество принятых деталей не может превышать количество отлитых")
    
    # Проверка дефектов
    total_defects = sum(defects_data.values()) if defects_data else 0
    calculated_accepted = total_cast - total_defects
    
    if calculated_accepted != total_accepted:
        warnings.append(f"Расчетное количество принятых ({calculated_accepted}) не совпадает с указанным ({total_accepted})")
    
    # Проверка на подозрительно высокий процент брака
    if total_cast > 0:
        reject_rate = (total_defects / total_cast) * 100
        if reject_rate > 50:
            warnings.append(f"Высокий процент брака: {reject_rate:.1f}%")
        elif reject_rate > 30:
            warnings.append(f"Повышенный процент брака: {reject_rate:.1f}%")
    
    # Проверка на отрицательные значения дефектов
    for defect_name, count in defects_data.items():
        if count < 0:
            errors.append(f"Количество дефектов '{defect_name}' не может быть отрицательным")
    
    return errors, warnings

def update_route_card_status_enhanced(card_number, total_cast, total_accepted, defects_summary):
    """Улучшенное обновление статуса маршрутной карты"""
    success = False
    
    # Обновляем статус в маршрутные_карты.db
    basic_update = update_route_card_status(card_number)
    logger.info(f"Результат обновления статуса для карты {card_number}: {basic_update}")
    
    # Дополнительно пытаемся записать детальную информацию
    conn = get_route_cards_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Ищем таблицу для детальной информации
            detail_table = None
            for table in tables:
                if 'детал' in table.lower() or 'контрол' in table.lower():
                    detail_table = table
                    break
            
            if detail_table:
                # Пытаемся добавить детальную информацию
                cursor.execute(f"PRAGMA table_info({detail_table})")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Формируем запрос в зависимости от структуры таблицы
                insert_data = {
                    'номер_карты': card_number,
                    'отлито': total_cast,
                    'принято': total_accepted,
                    'дата_контроля': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'дефекты': defects_summary
                }
                
                # Адаптируем названия полей под реальную структуру
                adapted_data = {}
                for key, value in insert_data.items():
                    for col in columns:
                        if key.lower() in col.lower() or col.lower() in key.lower():
                            adapted_data[col] = value
                            break
                
                if adapted_data:
                    placeholders = ', '.join(['?' for _ in adapted_data])
                    columns_str = ', '.join(adapted_data.keys())
                    
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO {detail_table} ({columns_str})
                        VALUES ({placeholders})
                    """, list(adapted_data.values()))
                    
                    conn.commit()
                    success = True
                    logger.info(f"Детальная информация по карте {card_number} записана в {detail_table}")
                else:
                    logger.info(f"Не найдены подходящие поля для записи детальной информации по карте {card_number}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Ошибка записи детальной информации по карте {card_number}: {e}")
            if conn:
                conn.close()
    
    result = basic_update or success
    logger.info(f"Итоговый результат обновления для карты {card_number}: {result}")
    return result

# ===== ФУНКЦИИ ВАЛИДАЦИИ СМЕН =====

def validate_shift_data(date, shift_number, controllers):
    """Валидация данных смены (старый метод, оставлен для совместимости)"""
    return validate_shift_data_extended(date, shift_number, controllers)

def auto_close_expired_shifts():
    """Автоматическое закрытие просроченных смен"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M')
        
        # Закрываем смены предыдущих дней
        cursor.execute('''
            UPDATE смены 
            SET статус = 'закрыта', время_окончания = ?
            WHERE дата < ? AND статус = 'активна'
        ''', (current_time, current_date))
        
        # Закрываем смены текущего дня, которые должны были закончиться
        # 1 смена: 07:00 - 19:00
        # 2 смена: 19:00 - 07:00 (следующего дня)
        
        if current_time > '19:00':
            # Закрываем 1 смену если время больше 19:00
            cursor.execute('''
                UPDATE смены 
                SET статус = 'закрыта', время_окончания = '19:00'
                WHERE дата = ? AND номер_смены = 1 AND статус = 'активна'
            ''', (current_date,))
        
        if current_time > '07:00' and current_time < '19:00':
            # Закрываем 2 смену предыдущего дня если время между 07:00 и 19:00
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute('''
                UPDATE смены 
                SET статус = 'закрыта', время_окончания = '07:00'
                WHERE дата = ? AND номер_смены = 2 AND статус = 'активна'
            ''', (yesterday,))
        
        conn.commit()
        conn.close()
        
        logger.info("Автоматическое закрытие просроченных смен выполнено")
        
    except Exception as e:
        logger.error(f"Ошибка автоматического закрытия смен: {e}")
        if conn:
            conn.close()

def get_shift_statistics(shift_id):
    """Получение статистики по смене"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        
        # Получаем общую статистику по смене
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
        
        # Получаем статистику по дефектам
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
        logger.error(f"Ошибка получения статистики смены: {e}")
        if conn:
            conn.close()
        return None

# ===== НЕДОСТАЮЩИЕ API ЭНДПОИНТЫ =====

@app.route('/control-input/<card_number>')
def control_input(card_number):
    """Страница ввода контроля для конкретной маршрутной карты"""
    # Проверяем активную смену
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены', 'error')
        return redirect(url_for('create_shift'))
    
    # Ищем маршрутную карту
    card_data = search_route_card_in_foundry(card_number)
    if not card_data:
        flash(f'Маршрутная карта {card_number} не найдена', 'error')
        return redirect(url_for('work_menu'))
    
    # Перенаправляем на существующую страницу ввода контроля с параметром
    return redirect(url_for('input_control', card=card_number))

@app.route('/api/close-shift', methods=['POST'])
def api_close_shift():
    """API для закрытия смены"""
    try:
        current_shift = get_current_shift()
        if not current_shift:
            logger.warning("Попытка закрытия смены без активной смены")
            return jsonify({'success': False, 'error': 'Нет активной смены'}), 400
        
        conn = get_db_connection()
        if not conn:
            logger.error("Не удалось подключиться к базе данных при закрытии смены")
            return jsonify({'success': False, 'error': 'Ошибка подключения к БД'}), 500
        
        cursor = conn.cursor()
        # Закрываем смену
        cursor.execute('''
            UPDATE смены
            SET время_окончания = ?, статус = 'закрыта'
            WHERE id = ?
        ''', (datetime.now().strftime('%H:%M'), current_shift['id']))
        
        conn.commit()
        conn.close()
        
        # Очищаем сессию
        session.pop('current_shift_id', None)
        logger.info(f"Смена {current_shift['id']} успешно закрыта через API")
        
        return jsonify({'success': True, 'message': 'Смена закрыта успешно'})
        
    except Exception as e:
        logger.error(f"Ошибка закрытия смены: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_close_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API закрытия смены: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/qr-scan', methods=['POST'])
def api_qr_scan():
    """API для обработки результатов QR сканирования"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Получен пустой JSON в API QR сканирования")
            return jsonify({'success': False, 'error': 'Пустой JSON запрос'}), 400
            
        qr_code = data.get('qr_code', '').strip()
        
        if not qr_code:
            logger.warning("Пустой QR код в запросе")
            return jsonify({'success': False, 'error': 'QR код не распознан'}), 400
        
        # Извлекаем номер карты из QR кода (предполагаем, что QR содержит номер карты)
        # QR код может содержать полный URL или просто номер карты
        card_number = qr_code
        if '/' in qr_code:
            # Если это URL, извлекаем последнюю часть
            card_number = qr_code.split('/')[-1]
        
        # Валидируем номер карты
        if not validate_route_card_number(card_number):
            error_handler.log_user_error(f"Неверный формат номера маршрутной карты из QR-кода: {card_number}", request)
            return jsonify({
                'success': False,
                'error': 'Неверный формат номера маршрутной карты. Ожидается 6 цифр.'
            }), 400
        
        # Ищем карту
        card_data = search_route_card_in_foundry(card_number)
        if card_data:
            log_operation(logger, "Успешное сканирование QR-кода", {
                "card_number": card_number,
                "user": request.remote_addr
            })
            logger.info(f"QR сканирование: найдена маршрутная карта {card_number}")
            return jsonify({
                'success': True,
                'card_number': card_number,
                'card_data': card_data
            })
        else:
            log_operation(logger, "Неудачное сканирование QR-кода", {
                "card_number": card_number,
                "user": request.remote_addr
            })
            logger.warning(f"QR сканирование: маршрутная карта {card_number} не найдена")
            return jsonify({
                'success': False,
                'error': f'Маршрутная карта {card_number} не найдена'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка обработки QR кода: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_qr_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API сканирования QR-кода: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

# ===== ДОПОЛНИТЕЛЬНЫЕ API ДЛЯ ПОЛНОТЫ ФУНКЦИОНАЛА =====

@app.route('/api/defects/types')
def api_defect_types():
    """API для получения типов дефектов"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Не удалось подключиться к базе данных при получении типов дефектов")
            error_id = f"api_defect_types_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(conn)}"
            error_handler.log_user_error("Ошибка подключения к БД при получении типов дефектов", request)
            return jsonify({'success': False, 'error': 'Ошибка подключения к БД', 'error_id': error_id}), 500
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cd.название as категория, td.название
            FROM типы_дефектов td
            JOIN категории_дефектов cd ON td.категория_id = cd.id
            WHERE td.активен = 1
            ORDER BY cd.название, td.название
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        # Группируем по категориям
        defects_by_category = {}
        for row in rows:
            category = row[0]
            defect_name = row[1]
            if category not in defects_by_category:
                defects_by_category[category] = []
            defects_by_category[category].append(defect_name)
        
        log_operation(logger, "Получение типов дефектов", {
            "total_defects": len(rows),
            "categories_count": len(defects_by_category),
            "user": request.remote_addr
        })
        logger.info(f"Получены типы дефектов: {len(rows)} записей в {len(defects_by_category)} категориях")
        return jsonify({'success': True, 'defects': defects_by_category})
        
    except Exception as e:
        logger.error(f"Ошибка получения типов дефектов: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_defect_types_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API получения типов дефектов: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/shifts/current')
def api_current_shift():
    """API для получения информации о текущей смене"""
    try:
        # Автоматически закрываем просроченные смены
        auto_close_expired_shifts()
        
        current_shift = get_current_shift()
        if current_shift:
            # Добавляем статистику к информации о смене
            stats = get_shift_statistics(current_shift['id'])
            current_shift['statistics'] = stats
            log_operation(logger, "Получение информации о текущей смене", {
                "shift_id": current_shift['id'],
                "user": request.remote_addr
            })
            logger.info(f"Получена информация о текущей смене {current_shift['id']}")
            return jsonify({'success': True, 'shift': current_shift})
        else:
            log_operation(logger, "Попытка получения информации о текущей смене без активной смены", {
                "user": request.remote_addr
            })
            logger.info("Нет активной смены при запросе текущей смены")
            return jsonify({'success': False, 'error': 'Нет активной смены'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка получения текущей смены: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_current_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API получения текущей смены: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/shifts/all')
def api_all_shifts():
    """API для получения всех смен"""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Не удалось подключиться к базе данных при получении списка смен")
            error_id = f"api_all_shifts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(conn)}"
            error_handler.log_user_error("Ошибка подключения к БД при получении списка смен", request)
            return jsonify({'success': False, 'error': 'Ошибка подключения к БД', 'error_id': error_id}), 500
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, дата, номер_смены, старший, контролеры, время_начала, время_окончания, статус
            FROM смены
            ORDER BY дата DESC, номер_смены DESC
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        shifts = []
        for row in rows:
            shift = {
                'id': row[0],
                'date': row[1],
                'shift_number': row[2],
                'supervisor': row[3],
                'controllers': json.loads(row[4]) if row[4] else [],
                'start_time': row[5],
                'end_time': row[6],
                'status': row[7]
            }
            shifts.append(shift)
        
        log_operation(logger, "Получение списка всех смен", {
            "total_shifts": len(shifts),
            "user": request.remote_addr
        })
        logger.info(f"Получен список смен: {len(shifts)} записей")
        return jsonify({'success': True, 'shifts': shifts})
        
    except Exception as e:
        logger.error(f"Ошибка получения списка смен: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_all_shifts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API получения списка смен: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/shifts/<int:shift_id>/statistics')
def api_shift_statistics(shift_id):
    """API для получения статистики по конкретной смене"""
    try:
        stats = get_shift_statistics(shift_id)
        if stats:
            log_operation(logger, "Получение статистики по смене", {
                "shift_id": shift_id,
                "user": request.remote_addr
            })
            logger.info(f"Получена статистика для смены {shift_id}")
            return jsonify({'success': True, 'statistics': stats})
        else:
            log_operation(logger, "Попытка получения статистики по несуществующей смене", {
                "shift_id": shift_id,
                "user": request.remote_addr
            })
            logger.warning(f"Статистика для смены {shift_id} не найдена или нет данных")
            return jsonify({'success': False, 'error': 'Смена не найдена или нет данных'}), 404
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики смены {shift_id}: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_shift_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API получения статистики смены {shift_id}: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/shifts/validate', methods=['POST'])
def api_validate_shift():
    """API для валидации данных смены"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Получен пустой JSON в API валидации смены")
            error_id = f"api_validate_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(data)}"
            error_handler.log_user_error("Получен пустой JSON в API валидации смены", request)
            return jsonify({'success': False, 'error': 'Пустой JSON запрос', 'error_id': error_id}), 400
            
        date = data.get('date')
        shift_number = data.get('shift_number')
        controllers = data.get('controllers', [])
        
        errors = validate_shift_data(date, shift_number, controllers)
        
        if errors:
            log_operation(logger, "Ошибки валидации данных смены", {
                "errors_count": len(errors),
                "user": request.remote_addr
            })
            logger.warning(f"Ошибки валидации смены: {errors}")
            return jsonify({'success': False, 'errors': errors}), 400
        else:
            log_operation(logger, "Успешная валидация данных смены", {
                "user": request.remote_addr
            })
            logger.info("Данные смены успешно валидированы")
            return jsonify({'success': True, 'message': 'Данные смены корректны'})
            
    except Exception as e:
        logger.error(f"Ошибка валидации смены: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_validate_shift_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API валидации смены: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/shifts/auto-close', methods=['POST'])
def api_auto_close_shifts():
    """API для принудительного автоматического закрытия просроченных смен"""
    try:
        auto_close_expired_shifts()
        logger.info("Выполнено принудительное автоматическое закрытие просроченных смен")
        return jsonify({'success': True, 'message': 'Просроченные смены закрыты'})
        
    except Exception as e:
        logger.error(f"Ошибка автоматического закрытия смен: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/control/validate', methods=['POST'])
def api_validate_control():
    """API для валидации данных контроля"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Получен пустой JSON в API валидации контроля")
            error_id = f"api_validate_control_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(data)}"
            error_handler.log_user_error("Получен пустой JSON в API валидации контроля", request)
            return jsonify({'success': False, 'error': 'Пустой JSON запрос', 'error_id': error_id}), 400
            
        total_cast = data.get('total_cast', 0)
        total_accepted = data.get('total_accepted', 0)
        defects_data = data.get('defects', {})
        
        errors, warnings = validate_control_data(total_cast, total_accepted, defects_data)
        
        # Дополнительные расчеты
        total_defects = sum(defects_data.values()) if defects_data else 0
        quality_rate = (total_accepted / total_cast * 100) if total_cast > 0 else 0
        reject_rate = (total_defects / total_cast * 100) if total_cast > 0 else 0
        
        result = {
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'statistics': {
                'total_cast': total_cast,
                'total_accepted': total_accepted,
                'total_defects': total_defects,
                'quality_rate': round(quality_rate, 2),
                'reject_rate': round(reject_rate, 2)
            }
        }
        
        if result['success']:
            log_operation(logger, "Успешная валидация данных контроля", {
                "total_cast": total_cast,
                "total_accepted": total_accepted,
                "quality_rate": quality_rate,
                "user": request.remote_addr
            })
            logger.info(f"Данные контроля успешно валидированы: {total_accepted}/{total_cast} деталей принято, качество {quality_rate:.2f}%")
        else:
            log_operation(logger, "Ошибки валидации данных контроля", {
                "errors_count": len(errors),
                "user": request.remote_addr
            })
            logger.warning(f"Ошибки валидации данных контроля: {errors}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка валидации данных контроля: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_validate_control_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API валидации данных контроля: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

@app.route('/api/control/calculate', methods=['POST'])
def api_calculate_accepted():
    """API для расчета количества принятых деталей"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Получен пустой JSON в API расчета принятых деталей")
            error_id = f"api_calculate_accepted_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(data)}"
            error_handler.log_user_error("Получен пустой JSON в API расчета принятых деталей", request)
            return jsonify({'success': False, 'error': 'Пустой JSON запрос', 'error_id': error_id}), 400
            
        total_cast = data.get('total_cast', 0)
        defects = data.get('defects', {})
        
        total_defects = sum(defects.values()) if defects else 0
        total_accepted = max(0, total_cast - total_defects)
        
        quality_rate = (total_accepted / total_cast * 100) if total_cast > 0 else 0
        reject_rate = (total_defects / total_cast * 100) if total_cast > 0 else 0
        
        result = {
            'success': True,
            'total_accepted': total_accepted,
            'total_defects': total_defects,
            'quality_rate': round(quality_rate, 2),
            'reject_rate': round(reject_rate, 2)
        }
        
        log_operation(logger, "Расчет количества принятых деталей", {
            "total_cast": total_cast,
            "total_accepted": total_accepted,
            "quality_rate": quality_rate,
            "reject_rate": reject_rate,
            "user": request.remote_addr
        })
        logger.info(f"Рассчитано количество принятых деталей: {total_accepted}/{total_cast}, качество {quality_rate:.2f}%, брак {reject_rate:.2f}%")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка расчета принятых деталей: {e}")
        logger.error(traceback.format_exc())
        error_id = f"api_calculate_accepted_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(e)}"
        error_handler.log_user_error(f"Ошибка API расчета принятых деталей: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e), 'error_id': error_id}), 500

# ===== ОБРАБОТКА ОШИБОК =====

@app.errorhandler(404)
def not_found_error(error):
    """Обработчик ошибки 404"""
    error_id = f"not_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
    error_handler.log_user_error(f"Ошибка 404: Страница не найдена - {request.url}", request)
    log_error_with_context(logger, error, {
        "error_id": error_id,
        "url": request.url,
        "user_agent": request.user_agent.string
    })
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Страница не найдена</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }}
            .error-container {{ max-width: 500px; margin: 0 auto; }}
            .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>🚫 Страница не найдена</h1>
            <p>Запрашиваемая страница не существует.</p>
            <p style="font-size: 12px; color: #666;">ID ошибки: {error_id}</p>
            <a href="/" class="btn">🏠 На главную</a>
        </div>
    </body>
    </html>
    '''), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработчик внутренней ошибки сервера"""
    error_id = f"internal_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error)}"
    error_handler.log_user_error(f"Внутренняя ошибка сервера: {str(error)}", request)
    log_error_with_context(logger, error, {
        "error_id": error_id,
        "url": request.url,
        "user_agent": request.user_agent.string
    })
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Внутренняя ошибка сервера</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }}
            .error-container {{ max-width: 500px; margin: 0 auto; }}
            .btn {{ padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>⚠️ Внутренняя ошибка сервера</h1>
            <p>Произошла ошибка при обработке запроса.</p>
            <p style="font-size: 12px; color: #666;">ID ошибки: {error_id}</p>
            <a href="/" class="btn">🏠 На главную</a>
        </div>
    </body>
    </html>
    '''), 500

# ===== ЗАПУСК ПРИЛОЖЕНИЯ =====

if __name__ == '__main__':
    # Создаем директории если их нет
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    
    # Инициализируем базу данных
    conn = get_db_connection()
    if conn:
        init_database(conn)
        conn.close()
        logger.info("База данных инициализирована успешно")
    
    # Запускаем приложение
    logger.info("Запуск системы контроля качества литейного производства")
    app.run(host='127.0.0.1', port=5005, debug=False)