"""
UI blueprint for HTML pages.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from ..services.shift_service import get_current_shift, create_shift, close_shift, get_all_shifts
from ..services.database_service import get_all_controllers, get_all_defect_types, search_route_card_in_foundry, check_card_already_processed
from ..services.control_service import save_control_record, get_control_records_by_shift
from ..helpers.validators import validate_shift_data_extended, validate_control_data
from ..helpers.error_handlers import handle_ui_error

logger = logging.getLogger(__name__)

ui_bp = Blueprint('ui', __name__)


@ui_bp.route('/')
def index():
    """Main page with welcome screen"""
    current_shift = get_current_shift()
    if current_shift:
        return redirect(url_for('ui.work_menu'))
    else:
        return render_template('welcome.html')


@ui_bp.route('/create-shift', methods=['GET', 'POST'])
def create_shift_route():
    """Create shift"""
    # Check for active shift
    current_shift = get_current_shift()
    if current_shift:
        flash(f'Смена {current_shift["shift_number"]} на дату {current_shift["date"]} уже активна. Закройте текущую смену перед созданием новой.', 'error')
        return redirect(url_for('ui.work_menu'))
    
    if request.method == 'POST':
        date = request.form.get('date')
        shift_number = int(request.form.get('shift_number', 0))
        controllers = request.form.getlist('controllers')
        
        # Validate data
        errors = validate_shift_data_extended(date, shift_number, controllers)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('ui.create_shift_route'))
        
        try:
            # Create shift
            shift_id = create_shift(date, shift_number, controllers)
            session['current_shift_id'] = shift_id
            flash('Смена успешно создана!', 'success')
            logger.info(f"Shift created: {shift_id}")
            return redirect(url_for('ui.work_menu'))
        except Exception as e:
            logger.error(f"Error creating shift: {e}")
            flash(f'Ошибка при создании смены: {str(e)}', 'error')
            return redirect(url_for('ui.create_shift_route'))
    
    # GET request - show form
    controllers = get_all_controllers()
    return render_template('create_shift.html', controllers=controllers)


@ui_bp.route('/work-menu')
def work_menu():
    """Work menu"""
    from ..services.shift_service import get_shift_statistics
    
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены. Создайте новую смену для продолжения работы.', 'info')
        return redirect(url_for('ui.create_shift_route'))
    
    # Get shift statistics
    stats = get_shift_statistics(current_shift['id'])
    current_shift['statistics'] = stats
    
    return render_template('work_menu.html', shift=current_shift)


@ui_bp.route('/input-control')
def input_control():
    """Quality control input page"""
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены', 'error')
        return redirect(url_for('ui.create_shift_route'))
    
    card_number = request.args.get('card')
    
    if not card_number:
        flash('Номер маршрутной карты не указан', 'error')
        return redirect(url_for('ui.work_menu'))
    
    # Search for route card
    foundry_data = search_route_card_in_foundry(card_number)
    if not foundry_data:
        flash(f'Маршрутная карта {card_number} не найдена', 'error')
        return redirect(url_for('ui.work_menu'))
    
    # Get defect types
    defect_types = get_all_defect_types()
    
    return render_template('input_control.html', 
                         shift=current_shift, 
                         card_number=card_number,
                         foundry_data=foundry_data,
                         defect_types=defect_types)


@ui_bp.route('/save-control', methods=['POST'])
def save_control():
    """Save quality control record"""
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены', 'error')
        return redirect(url_for('ui.create_shift_route'))
    
    try:
        card_number = request.form.get('card_number')
        total_cast = int(request.form.get('total_cast', 0))
        total_accepted = int(request.form.get('total_accepted', 0))
        controller = request.form.get('controller')
        notes = request.form.get('notes', '')
        
        # Get defects
        defects = {}
        for key, value in request.form.items():
            if key.startswith('defect_'):
                defect_id = int(key.replace('defect_', ''))
                count = int(value) if value else 0
                if count > 0:
                    defects[defect_id] = count
        
        # Validate
        errors, warnings = validate_control_data(total_cast, total_accepted, defects)
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('ui.input_control', card=card_number))
        
        if warnings:
            for warning in warnings:
                flash(warning, 'warning')
        
        # Save record
        record_id = save_control_record(
            current_shift['id'],
            card_number,
            total_cast,
            total_accepted,
            controller,
            defects,
            notes
        )
        
        flash('Данные контроля успешно сохранены!', 'success')
        logger.info(f"Control record saved: {record_id}")
        return redirect(url_for('ui.work_menu'))
        
    except Exception as e:
        logger.error(f"Error saving control record: {e}")
        flash(f'Ошибка при сохранении данных: {str(e)}', 'error')
        return redirect(url_for('ui.work_menu'))


@ui_bp.route('/close-shift', methods=['POST'])
def close_shift_route():
    """Close shift (POST form)"""
    current_shift = get_current_shift()
    if not current_shift:
        flash('Нет активной смены', 'error')
        return redirect(url_for('ui.index'))
    
    try:
        close_shift(current_shift['id'])
        session.pop('current_shift_id', None)
        flash('Смена успешно закрыта', 'success')
        logger.info(f"Shift closed: {current_shift['id']}")
    except Exception as e:
        logger.error(f"Error closing shift: {e}")
        flash(f'Ошибка при закрытии смены: {str(e)}', 'error')
    
    return redirect(url_for('ui.index'))


@ui_bp.route('/reports')
def reports():
    """Reports page"""
    shifts = get_all_shifts(limit=50)
    return render_template('reports.html', shifts=shifts)


@ui_bp.route('/manage-controllers')
def manage_controllers():
    """Manage controllers page"""
    controllers = get_all_controllers()
    return render_template('manage_controllers.html', controllers=controllers)


@ui_bp.route('/control-input/<card_number>')
def control_input_redirect(card_number):
    """Redirect to input control with card number"""
    return redirect(url_for('ui.input_control', card=card_number))
