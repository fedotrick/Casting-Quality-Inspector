"""
API blueprint for JSON endpoints.
"""
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, session

from ..services.shift_service import get_current_shift, close_shift, get_shift_statistics, auto_close_expired_shifts
from ..services.database_service import (search_route_card_in_foundry, check_card_already_processed,
                                          get_all_defect_types, add_controller, toggle_controller,
                                          delete_controller, get_all_controllers)
from ..services.control_service import calculate_quality_metrics
from ..helpers.validators import validate_route_card_number, validate_shift_data_extended, validate_control_data
from ..helpers.error_handlers import validate_and_handle_errors, error_handler
from ..helpers.logging_config import log_operation

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/search-card/<card_number>')
def search_card(card_number):
    """Search for route card"""
    try:
        # Validate card number
        if not validate_route_card_number(card_number):
            return jsonify({
                'success': False,
                'error': 'Неверный формат номера маршрутной карты'
            }), 400
        
        # Check if already processed
        if check_card_already_processed(card_number):
            return jsonify({
                'success': False,
                'error': f'Маршрутная карта {card_number} уже обработана в текущей смене',
                'already_processed': True
            }), 400
        
        # Search in foundry DB
        card_data = search_route_card_in_foundry(card_number)
        
        if card_data:
            log_operation(logger, "Route card search", {"card_number": card_number, "found": True})
            return jsonify({
                'success': True,
                'card': dict(card_data)
            })
        else:
            log_operation(logger, "Route card search", {"card_number": card_number, "found": False})
            return jsonify({
                'success': False,
                'error': f'Маршрутная карта {card_number} не найдена'
            }), 404
            
    except Exception as e:
        logger.error(f"Error searching card: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/close-shift', methods=['POST'])
def api_close_shift():
    """API endpoint to close shift"""
    try:
        current_shift = get_current_shift()
        if not current_shift:
            logger.warning("Attempt to close shift without active shift")
            return jsonify({'success': False, 'error': 'Нет активной смены'}), 400
        
        close_shift(current_shift['id'])
        session.pop('current_shift_id', None)
        logger.info(f"Shift {current_shift['id']} closed successfully via API")
        
        return jsonify({'success': True, 'message': 'Смена закрыта успешно'})
        
    except Exception as e:
        logger.error(f"Error closing shift: {e}")
        error_handler.log_user_error(f"API close shift error: {str(e)}", request)
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/qr-scan', methods=['POST'])
def api_qr_scan():
    """API endpoint for QR scan processing"""
    try:
        data = request.get_json()
        if not data:
            logger.warning("Empty JSON in QR scan API")
            return jsonify({'success': False, 'error': 'Пустой JSON запрос'}), 400
            
        qr_code = data.get('qr_code', '').strip()
        
        if not qr_code:
            logger.warning("Empty QR code in request")
            return jsonify({'success': False, 'error': 'QR код не распознан'}), 400
        
        # Extract card number from QR code
        card_number = qr_code
        if '/' in qr_code:
            card_number = qr_code.split('/')[-1]
        
        # Validate card number
        if not validate_route_card_number(card_number):
            error_handler.log_user_error(f"Invalid route card number from QR: {card_number}", request)
            return jsonify({
                'success': False,
                'error': 'Неверный формат номера маршрутной карты. Ожидается 6 цифр.'
            }), 400
        
        # Search card
        card_data = search_route_card_in_foundry(card_number)
        if card_data:
            log_operation(logger, "Successful QR scan", {"card_number": card_number})
            return jsonify({
                'success': True,
                'card_number': card_number,
                'card_data': dict(card_data)
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Маршрутная карта {card_number} не найдена'
            }), 404
            
    except Exception as e:
        logger.error(f"Error processing QR scan: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/defects/types')
def get_defects_types():
    """Get all defect types"""
    try:
        defect_types = get_all_defect_types()
        return jsonify({
            'success': True,
            'defect_types': defect_types
        })
    except Exception as e:
        logger.error(f"Error getting defect types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shifts/current')
def get_current_shift_api():
    """Get current shift via API"""
    try:
        current_shift = get_current_shift()
        if current_shift:
            # Get statistics
            stats = get_shift_statistics(current_shift['id'])
            current_shift['statistics'] = stats
            return jsonify({
                'success': True,
                'shift': current_shift
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Нет активной смены'
            }), 404
    except Exception as e:
        logger.error(f"Error getting current shift: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shifts/all')
def get_all_shifts_api():
    """Get all shifts via API"""
    try:
        from ..services.shift_service import get_all_shifts
        
        limit = request.args.get('limit', 50, type=int)
        shifts = get_all_shifts(limit=limit)
        
        return jsonify({
            'success': True,
            'shifts': shifts
        })
    except Exception as e:
        logger.error(f"Error getting all shifts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shifts/<int:shift_id>/statistics')
def get_shift_statistics_api(shift_id):
    """Get shift statistics via API"""
    try:
        stats = get_shift_statistics(shift_id)
        if stats:
            return jsonify({
                'success': True,
                'statistics': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Статистика не найдена'
            }), 404
    except Exception as e:
        logger.error(f"Error getting shift statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shifts/validate', methods=['POST'])
def validate_shift():
    """Validate shift data"""
    try:
        data = request.get_json()
        date = data.get('date')
        shift_number = data.get('shift_number')
        controllers = data.get('controllers', [])
        
        errors = validate_shift_data_extended(date, shift_number, controllers)
        
        return jsonify({
            'success': len(errors) == 0,
            'errors': errors
        })
    except Exception as e:
        logger.error(f"Error validating shift: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/shifts/auto-close', methods=['POST'])
def auto_close_shifts():
    """Auto-close expired shifts"""
    try:
        auto_close_expired_shifts()
        return jsonify({
            'success': True,
            'message': 'Просроченные смены закрыты'
        })
    except Exception as e:
        logger.error(f"Error auto-closing shifts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/control/validate', methods=['POST'])
def validate_control():
    """Validate control data"""
    try:
        data = request.get_json()
        total_cast = data.get('total_cast', 0)
        total_accepted = data.get('total_accepted', 0)
        defects_data = data.get('defects', {})
        
        # Convert string keys to int
        defects_data = {int(k): v for k, v in defects_data.items()}
        
        errors, warnings = validate_control_data(total_cast, total_accepted, defects_data)
        
        return jsonify({
            'success': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        })
    except Exception as e:
        logger.error(f"Error validating control data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/control/calculate', methods=['POST'])
def calculate_control():
    """Calculate quality metrics"""
    try:
        data = request.get_json()
        total_cast = data.get('total_cast', 0)
        total_accepted = data.get('total_accepted', 0)
        defects_data = data.get('defects', {})
        
        # Convert string keys to int
        defects_data = {int(k): v for k, v in defects_data.items()}
        
        metrics = calculate_quality_metrics(total_cast, total_accepted, defects_data)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Controller management endpoints
@api_bp.route('/add-controller', methods=['POST'])
def add_controller_api():
    """Add new controller"""
    try:
        name = request.form.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Имя контролера не указано'}), 400
        
        controller_id = add_controller(name)
        logger.info(f"Controller added: {name}")
        
        return jsonify({
            'success': True,
            'controller_id': controller_id,
            'message': f'Контролер "{name}" добавлен'
        })
    except Exception as e:
        logger.error(f"Error adding controller: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/toggle-controller', methods=['POST'])
def toggle_controller_api():
    """Toggle controller status"""
    try:
        controller_id = request.form.get('id', type=int)
        if not controller_id:
            return jsonify({'success': False, 'error': 'ID контролера не указан'}), 400
        
        toggle_controller(controller_id)
        logger.info(f"Controller {controller_id} status toggled")
        
        return jsonify({
            'success': True,
            'message': 'Статус контролера изменен'
        })
    except Exception as e:
        logger.error(f"Error toggling controller: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/delete-controller', methods=['POST'])
def delete_controller_api():
    """Delete controller"""
    try:
        controller_id = request.form.get('id', type=int)
        if not controller_id:
            return jsonify({'success': False, 'error': 'ID контролера не указан'}), 400
        
        delete_controller(controller_id)
        logger.info(f"Controller {controller_id} deleted")
        
        return jsonify({
            'success': True,
            'message': 'Контролер удален'
        })
    except Exception as e:
        logger.error(f"Error deleting controller: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
