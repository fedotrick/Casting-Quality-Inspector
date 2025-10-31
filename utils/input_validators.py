"""Input validators for the quality control system."""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class InputValidator:
    """Central input validator."""
    
    @staticmethod
    def validate_string(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> tuple[bool, str]:
        """Validate string input."""
        if not value or not isinstance(value, str):
            return False, f"Поле '{field_name}' должно быть строкой"
        
        if len(value.strip()) < min_length:
            return False, f"Поле '{field_name}' должно содержать минимум {min_length} символов"
        
        if len(value) > max_length:
            return False, f"Поле '{field_name}' слишком длинное (максимум {max_length} символов)"
        
        return True, ""
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> tuple[bool, str]:
        """Validate integer input."""
        try:
            int_value = int(value)
            
            if min_val is not None and int_value < min_val:
                return False, f"Поле '{field_name}' должно быть не меньше {min_val}"
            
            if max_val is not None and int_value > max_val:
                return False, f"Поле '{field_name}' должно быть не больше {max_val}"
            
            return True, ""
        except (ValueError, TypeError):
            return False, f"Поле '{field_name}' должно быть целым числом"


input_validator = InputValidator()


def validate_route_card_number(card_number: str) -> bool:
    """Validate route card number."""
    if not card_number or not isinstance(card_number, str):
        return False
    # Allow only digits, 6 characters
    return bool(re.match(r'^\d{6}$', card_number))


def validate_positive_integer(value: Any, field_name: str) -> tuple[bool, str]:
    """Validate positive integer."""
    return input_validator.validate_integer(value, field_name, min_val=1)


def validate_shift_data_extended(date: str, shift_number: int, controllers: List[str]) -> List[str]:
    """Extended shift data validation."""
    errors = []
    
    # Date validation
    if not date:
        errors.append("Дата смены обязательна")
    else:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            if parsed_date.date() > datetime.now().date() + timedelta(days=1):
                errors.append("Дата смены не может быть в будущем")
        except ValueError:
            errors.append("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
    
    # Shift number validation
    if shift_number not in [1, 2]:
        errors.append("Номер смены должен быть 1 или 2")
    
    # Controllers validation
    if not controllers or len(controllers) == 0:
        errors.append("Необходимо выбрать хотя бы одного контролера")
    
    return errors


def validate_and_log_input(data: Dict[str, Any], required_fields: List[str], operation: str) -> List[str]:
    """Validate and log input data."""
    errors = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Поле '{field}' обязательно для заполнения")
    
    if errors:
        logger.warning(f"Validation errors in {operation}: {errors}")
    
    return errors


def validate_control_data(total_cast: int, total_accepted: int, defects_data: Dict[str, int]) -> List[str]:
    """Validate control data."""
    errors = []
    
    if total_cast <= 0:
        errors.append("Количество отлитых деталей должно быть больше 0")
    
    if total_accepted < 0:
        errors.append("Количество принятых деталей не может быть отрицательным")
    
    if total_accepted > total_cast:
        errors.append("Количество принятых деталей не может превышать количество отлитых")
    
    for defect_name, count in defects_data.items():
        if count < 0:
            errors.append(f"Количество дефектов '{defect_name}' не может быть отрицательным")
    
    return errors


def validate_json_input(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate JSON input."""
    return validate_and_log_input(data, required_fields, "json_validation")


def validate_form_input(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate form input."""
    return validate_and_log_input(data, required_fields, "form_validation")


def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS.
    
    Preserves single quotes while encoding other dangerous characters.
    """
    if not value:
        return ""
    
    result = str(value)
    
    # HTML encode dangerous characters to prevent XSS
    # Note: Must encode & first to avoid double-encoding
    result = result.replace('&', '&amp;')
    result = result.replace('<', '&lt;')
    result = result.replace('>', '&gt;')
    result = result.replace('"', '&quot;')
    # Preserve single quotes - do not encode or remove them
    
    return result.strip()


def validate_table_name(table_name: str, allowed_tables: List[str]) -> bool:
    """Validate table name against whitelist."""
    return table_name in allowed_tables


def validate_column_name(column_name: str, allowed_columns: List[str]) -> bool:
    """Validate column name against whitelist."""
    return column_name in allowed_columns
