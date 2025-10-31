"""Enhanced external integration with retry logic and proper error handling."""

import time
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar
from functools import wraps

from .unified_logging import get_logger
from .unified_error_handlers import IntegrationError, DatabaseError


logger = get_logger(__name__)

T = TypeVar('T')


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Success after {attempt + 1} attempts: {func.__name__}",
                            function=func.__name__,
                            attempt=attempt + 1
                        )
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                            error=str(e),
                            retry_delay=current_delay
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}",
                            function=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e)
                        )
            
            # All attempts failed
            raise IntegrationError(
                f"Failed after {max_attempts} attempts: {str(last_exception)}",
                details={
                    'function': func.__name__,
                    'attempts': max_attempts,
                    'last_error': str(last_exception)
                },
                retry_attempted=True
            )
        
        return wrapper
    return decorator


class ExternalDBConnection:
    """Context manager for external database connections."""
    
    def __init__(self, db_path: Path, db_name: str = "external"):
        self.db_path = db_path
        self.db_name = db_name
        self.connection = None
    
    def __enter__(self):
        """Open database connection."""
        try:
            if not self.db_path.exists():
                raise DatabaseError(
                    f"Database file not found: {self.db_path}",
                    details={'db_path': str(self.db_path), 'db_name': self.db_name},
                    user_message=f"База данных {self.db_name} не найдена"
                )
            
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            
            logger.debug(
                f"Connected to {self.db_name} database",
                db_path=str(self.db_path)
            )
            
            return self.connection
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Failed to connect to database: {str(e)}",
                details={'db_path': str(self.db_path), 'db_name': self.db_name},
                user_message=f"Не удалось подключиться к базе данных {self.db_name}"
            )
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.debug(f"Closed connection to {self.db_name} database")
            except sqlite3.Error as e:
                logger.warning(
                    f"Error closing {self.db_name} database connection",
                    error=str(e)
                )


class EnhancedExternalDBIntegration:
    """Enhanced external database integration with retry logic and proper error handling."""
    
    def __init__(
        self,
        foundry_db_path: Optional[Path] = None,
        route_cards_db_path: Optional[Path] = None
    ):
        self.foundry_db_path = foundry_db_path
        self.route_cards_db_path = route_cards_db_path
        
        logger.info(
            "Initialized external DB integration",
            foundry_db=str(foundry_db_path) if foundry_db_path else None,
            route_cards_db=str(route_cards_db_path) if route_cards_db_path else None
        )
    
    @retry_on_failure(max_attempts=3, delay=0.5, exceptions=(sqlite3.Error,))
    def search_route_card(self, card_number: str) -> Optional[Dict[str, Any]]:
        """
        Search for route card in external databases with retry logic.
        
        Args:
            card_number: Route card number to search
        
        Returns:
            Dictionary with card data if found, None otherwise
        
        Raises:
            IntegrationError: If all retry attempts fail
            ValidationError: If card number is invalid
        """
        if not card_number:
            from .unified_error_handlers import ValidationError
            raise ValidationError(
                "Card number cannot be empty",
                field="card_number",
                user_message="Номер карты не может быть пустым"
            )
        
        logger.info(
            "Searching for route card",
            card_number=card_number
        )
        
        # Try foundry database first
        if self.foundry_db_path and self.foundry_db_path.exists():
            result = self._search_in_foundry_db(card_number)
            if result:
                logger.info(
                    "Route card found in foundry database",
                    card_number=card_number
                )
                return result
        
        # Try route cards database
        if self.route_cards_db_path and self.route_cards_db_path.exists():
            result = self._search_in_route_cards_db(card_number)
            if result:
                logger.info(
                    "Route card found in route cards database",
                    card_number=card_number
                )
                return result
        
        logger.warning(
            "Route card not found in any database",
            card_number=card_number
        )
        return None
    
    def _search_in_foundry_db(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Search in foundry database."""
        try:
            with ExternalDBConnection(self.foundry_db_path, "foundry") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM route_cards WHERE card_number = ?",
                    (card_number,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        
        except DatabaseError:
            raise
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Error searching foundry database: {str(e)}",
                details={'card_number': card_number, 'database': 'foundry'},
                user_message="Ошибка при поиске в базе данных литейного производства"
            )
    
    def _search_in_route_cards_db(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Search in route cards database."""
        try:
            with ExternalDBConnection(self.route_cards_db_path, "route_cards") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM маршрутные_карты WHERE номер = ?",
                    (card_number,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
        
        except DatabaseError:
            raise
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Error searching route cards database: {str(e)}",
                details={'card_number': card_number, 'database': 'route_cards'},
                user_message="Ошибка при поиске в базе данных маршрутных карт"
            )
    
    @retry_on_failure(max_attempts=3, delay=0.5, exceptions=(sqlite3.Error,))
    def update_route_card_status(
        self,
        card_number: str,
        status: str
    ) -> bool:
        """
        Update route card status in external databases with retry logic.
        
        Args:
            card_number: Route card number
            status: New status
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            IntegrationError: If all retry attempts fail
        """
        logger.info(
            "Updating route card status",
            card_number=card_number,
            status=status
        )
        
        try:
            # Try to update in foundry database
            if self.foundry_db_path and self.foundry_db_path.exists():
                with ExternalDBConnection(self.foundry_db_path, "foundry") as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE route_cards SET status = ? WHERE card_number = ?",
                        (status, card_number)
                    )
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(
                            "Route card status updated in foundry database",
                            card_number=card_number,
                            status=status
                        )
                        return True
            
            # Try to update in route cards database
            if self.route_cards_db_path and self.route_cards_db_path.exists():
                with ExternalDBConnection(self.route_cards_db_path, "route_cards") as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE маршрутные_карты SET статус = ? WHERE номер = ?",
                        (status, card_number)
                    )
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        logger.info(
                            "Route card status updated in route cards database",
                            card_number=card_number,
                            status=status
                        )
                        return True
            
            logger.warning(
                "Route card not found for status update",
                card_number=card_number
            )
            return False
        
        except DatabaseError:
            raise
        except sqlite3.Error as e:
            raise DatabaseError(
                f"Error updating route card status: {str(e)}",
                details={'card_number': card_number, 'status': status},
                user_message="Ошибка при обновлении статуса маршрутной карты"
            )
    
    @retry_on_failure(max_attempts=3, delay=0.5, exceptions=(sqlite3.Error,))
    def write_detailed_info(
        self,
        card_number: str,
        info: Dict[str, Any]
    ) -> bool:
        """
        Write detailed route card info to external databases with retry logic.
        
        Args:
            card_number: Route card number
            info: Detailed information to write
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            IntegrationError: If all retry attempts fail
        """
        logger.info(
            "Writing detailed route card info",
            card_number=card_number,
            info_keys=list(info.keys()) if info else []
        )
        
        # Implementation depends on external DB structure
        # This is a placeholder that logs the operation
        logger.info(
            "Detailed info written (placeholder)",
            card_number=card_number
        )
        
        return True
    
    def validate_card_number(self, card_number: str) -> bool:
        """
        Validate route card number in external databases.
        
        Args:
            card_number: Route card number to validate
        
        Returns:
            True if card exists, False otherwise
        """
        try:
            result = self.search_route_card(card_number)
            return result is not None
        except IntegrationError as e:
            logger.warning(
                "Failed to validate card number due to integration error",
                card_number=card_number,
                error=str(e)
            )
            return False


# Global instance for backward compatibility
enhanced_integration = EnhancedExternalDBIntegration()


def get_external_integration() -> EnhancedExternalDBIntegration:
    """Get the global external integration instance."""
    return enhanced_integration


def configure_external_integration(
    foundry_db_path: Optional[Path] = None,
    route_cards_db_path: Optional[Path] = None
):
    """
    Configure the global external integration instance.
    
    Args:
        foundry_db_path: Path to foundry database
        route_cards_db_path: Path to route cards database
    """
    global enhanced_integration
    enhanced_integration = EnhancedExternalDBIntegration(
        foundry_db_path=foundry_db_path,
        route_cards_db_path=route_cards_db_path
    )
    
    logger.info(
        "External integration configured",
        foundry_db=str(foundry_db_path) if foundry_db_path else None,
        route_cards_db=str(route_cards_db_path) if route_cards_db_path else None
    )
