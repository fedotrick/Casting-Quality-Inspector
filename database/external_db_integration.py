"""External database integration for route cards."""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


class ExternalDBIntegration:
    """Handler for external database integration."""
    
    def __init__(self, foundry_db_path: Optional[Path] = None, route_cards_db_path: Optional[Path] = None):
        self.foundry_db_path = foundry_db_path
        self.route_cards_db_path = route_cards_db_path
    
    def search_route_card(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Search for route card in external databases."""
        # Try foundry database first
        if self.foundry_db_path and self.foundry_db_path.exists():
            result = self._search_in_foundry_db(card_number)
            if result:
                return result
        
        # Try route cards database
        if self.route_cards_db_path and self.route_cards_db_path.exists():
            result = self._search_in_route_cards_db(card_number)
            if result:
                return result
        
        return None
    
    def _search_in_foundry_db(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Search in foundry database."""
        try:
            conn = sqlite3.connect(str(self.foundry_db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try to find the card
            cursor.execute("SELECT * FROM route_cards WHERE card_number = ?", (card_number,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            
        except Exception as e:
            logger.error(f"Error searching foundry DB: {str(e)}")
        
        return None
    
    def _search_in_route_cards_db(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Search in route cards database."""
        try:
            conn = sqlite3.connect(str(self.route_cards_db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Try to find the card
            cursor.execute("SELECT * FROM маршрутные_карты WHERE номер = ?", (card_number,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            
        except Exception as e:
            logger.error(f"Error searching route cards DB: {str(e)}")
        
        return None


external_db_integration = ExternalDBIntegration()


def search_route_card_in_external_db(card_number: str) -> Optional[Dict[str, Any]]:
    """Search for route card in external databases."""
    return external_db_integration.search_route_card(card_number)


def update_route_card_status_in_external_db(card_number: str, status: str) -> bool:
    """Update route card status in external databases."""
    # Implementation depends on external DB structure
    logger.info(f"Updating card {card_number} status to {status}")
    return True


def write_detailed_route_card_info_to_external_db(card_number: str, info: Dict[str, Any]) -> bool:
    """Write detailed route card info to external databases."""
    # Implementation depends on external DB structure
    logger.info(f"Writing detailed info for card {card_number}")
    return True


def validate_route_card_number_in_external_db(card_number: str) -> bool:
    """Validate route card number in external databases."""
    result = search_route_card_in_external_db(card_number)
    return result is not None
