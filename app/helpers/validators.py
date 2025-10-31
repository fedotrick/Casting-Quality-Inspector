"""
Input validation utilities.
"""
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def validate_route_card_number(card_number: str) -> bool:
    """
    Validate route card number format.
    
    Args:
        card_number: Card number to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not card_number:
        return False
    # Check that card number consists only of digits and has length of 6 characters
    return re.match(r'^\d{6}$', card_number) is not None


def validate_positive_integer(value: Any, field_name: str) -> Tuple[bool, str]:
    """
    Validate that value is a positive integer.
    
    Args:
        value: Value to validate
        field_name: Field name for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            return False, f"Поле '{field_name}' должно быть положительным числом"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Поле '{field_name}' должно быть числом"


def validate_input_data(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that all required fields are present and not empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Поле '{field}' обязательно для заполнения")
    return errors


def validate_shift_data_extended(date: str, shift_number: int, controllers: List[str]) -> List[str]:
    """
    Extended validation of shift data.
    
    Args:
        date: Shift date in YYYY-MM-DD format
        shift_number: Shift number (1 or 2)
        controllers: List of controller names
        
    Returns:
        List of error messages (empty if valid)
    """
    from ..repositories import ShiftRepository
    from ..database import get_db
    
    errors = []
    
    # Validate date
    if not date:
        errors.append("Дата смены обязательна")
    else:
        try:
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            # Check that date is not in the future (with small buffer for next day shifts)
            if parsed_date.date() > datetime.now().date() + timedelta(days=1):
                errors.append("Дата смены не может быть в будущем")
        except ValueError:
            errors.append("Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
    
    # Validate shift number
    if shift_number is None or shift_number not in [1, 2]:
        errors.append("Номер смены должен быть 1 или 2")
    
    # Validate controllers
    if not controllers or len(controllers) == 0:
        errors.append("Необходимо выбрать хотя бы одного контролера")
    
    # Check for duplicate active shift
    if not errors and date and shift_number:
        try:
            session = get_db()
            repo = ShiftRepository(session)
            if repo.check_duplicate(date, shift_number):
                errors.append(f"Смена {shift_number} на дату {date} уже активна")
        except Exception as e:
            logger.error(f"Ошибка проверки дублирования смены: {e}")
            errors.append("Ошибка проверки данных смены")
    
    return errors


def validate_control_data(total_cast: int, total_accepted: int, defects_data: Dict[str, int]) -> Tuple[List[str], List[str]]:
    """
    Enhanced validation of quality control data.
    
    Args:
        total_cast: Total number of cast parts
        total_accepted: Total number of accepted parts
        defects_data: Dictionary of defect types and counts
        
    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    
    # Validate basic data
    if not total_cast or total_cast <= 0:
        errors.append("Количество отлитых деталей должно быть больше 0")
    
    if total_accepted < 0:
        errors.append("Количество принятых деталей не может быть отрицательным")
    
    if total_accepted > total_cast:
        errors.append("Количество принятых деталей не может превышать количество отлитых")
    
    # Validate defects
    total_defects = sum(defects_data.values()) if defects_data else 0
    calculated_accepted = total_cast - total_defects
    
    if calculated_accepted != total_accepted:
        warnings.append(f"Расчетное количество принятых ({calculated_accepted}) не совпадает с указанным ({total_accepted})")
    
    # Check for suspiciously high reject rate
    if total_cast > 0:
        reject_rate = (total_defects / total_cast) * 100
        if reject_rate > 50:
            warnings.append(f"Высокий процент брака: {reject_rate:.1f}%")
        elif reject_rate > 30:
            warnings.append(f"Повышенный процент брака: {reject_rate:.1f}%")
    
    # Check for negative defect counts
    for defect_name, count in defects_data.items():
        if count < 0:
            errors.append(f"Количество дефектов '{defect_name}' не может быть отрицательным")
    
    # Additional validation for special cases
    if total_cast > 10000:
        warnings.append(f"Очень большое количество отлитых деталей: {total_cast}")
    
    if total_defects > 5000:
        warnings.append(f"Очень большое количество дефектов: {total_defects}")
    
    return errors, warnings


def validate_and_log_input(data: Dict[str, Any], required_fields: List[str], operation: str) -> List[str]:
    """
    Validate user input and log the operation.
    
    Args:
        data: Data to validate
        required_fields: List of required fields
        operation: Operation name for logging
        
    Returns:
        List of error messages (empty if valid)
    """
    from .logging_config import log_operation
    
    errors = validate_input_data(data, required_fields)
    
    log_operation(logger, operation, {
        'data_keys': list(data.keys()),
        'required_fields': required_fields,
        'validation_errors': errors
    })
    
    return errors


def validate_json_input(data: Dict[str, Any], schema: Dict[str, type]) -> List[str]:
    """
    Validate JSON input against a schema.
    
    Args:
        data: Input data
        schema: Schema dictionary mapping field names to expected types
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    for field, expected_type in schema.items():
        if field not in data:
            errors.append(f"Отсутствует обязательное поле '{field}'")
        elif not isinstance(data[field], expected_type):
            errors.append(f"Поле '{field}' должно быть типа {expected_type.__name__}")
    
    return errors


def validate_form_input(form_data: Dict[str, Any], validations: Dict[str, callable]) -> List[str]:
    """
    Validate form input using custom validation functions.
    
    Args:
        form_data: Form data to validate
        validations: Dictionary mapping field names to validation functions
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    for field, validation_func in validations.items():
        if field in form_data:
            try:
                is_valid, error_msg = validation_func(form_data[field])
                if not is_valid:
                    errors.append(error_msg)
            except Exception as e:
                logger.error(f"Validation error for field {field}: {e}")
                errors.append(f"Ошибка валидации поля '{field}'")
    
    return errors


# Alias for compatibility
input_validator = {
    'validate_route_card_number': validate_route_card_number,
    'validate_positive_integer': validate_positive_integer,
    'validate_input_data': validate_input_data,
    'validate_shift_data_extended': validate_shift_data_extended,
    'validate_control_data': validate_control_data
}
