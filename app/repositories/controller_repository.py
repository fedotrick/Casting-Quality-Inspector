"""
Repository for controller operations.
"""
import logging
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from ..models import Контролёр
from ..helpers.error_handlers import ОшибкаБазыДанных

logger = logging.getLogger(__name__)


class ControllerRepository:
    """Repository for controller CRUD operations"""
    
    def __init__(self, session):
        self.session = session
    
    def get_all(self, active_only: bool = True) -> List[Контролёр]:
        """Get all controllers"""
        try:
            query = self.session.query(Контролёр)
            if active_only:
                query = query.filter_by(активен=1)
            return query.order_by(Контролёр.имя).all()
        except Exception as e:
            logger.error(f"Error getting controllers: {e}")
            raise ОшибкаБазыДанных(f"Failed to get controllers: {str(e)}")
    
    def get_by_id(self, controller_id: int) -> Optional[Контролёр]:
        """Get controller by ID"""
        try:
            return self.session.query(Контролёр).filter_by(id=controller_id).first()
        except Exception as e:
            logger.error(f"Error getting controller by ID: {e}")
            raise ОшибкаБазыДанных(f"Failed to get controller: {str(e)}")
    
    def get_by_name(self, name: str) -> Optional[Контролёр]:
        """Get controller by name"""
        try:
            return self.session.query(Контролёр).filter_by(имя=name).first()
        except Exception as e:
            logger.error(f"Error getting controller by name: {e}")
            raise ОшибкаБазыДанных(f"Failed to get controller: {str(e)}")
    
    def add(self, name: str) -> Контролёр:
        """Add new controller"""
        try:
            controller = Контролёр(имя=name, активен=1)
            self.session.add(controller)
            self.session.flush()
            logger.info(f"Added controller: {name}")
            return controller
        except IntegrityError:
            self.session.rollback()
            raise ОшибкаБазыДанных(f"Контролер '{name}' уже существует")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding controller: {e}")
            raise ОшибкаБазыДанных(f"Failed to add controller: {str(e)}")
    
    def toggle_active(self, controller_id: int) -> bool:
        """Toggle controller active status"""
        try:
            controller = self.get_by_id(controller_id)
            if controller:
                controller.активен = 1 if controller.активен == 0 else 0
                self.session.flush()
                logger.info(f"Toggled controller {controller_id} status to {controller.активен}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error toggling controller: {e}")
            raise ОшибкаБазыДанных(f"Failed to toggle controller: {str(e)}")
    
    def delete(self, controller_id: int) -> bool:
        """Delete controller"""
        try:
            controller = self.get_by_id(controller_id)
            if controller:
                self.session.delete(controller)
                self.session.flush()
                logger.info(f"Deleted controller {controller_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting controller: {e}")
            raise ОшибкаБазыДанных(f"Failed to delete controller: {str(e)}")
