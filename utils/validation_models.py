"""Pydantic validation models for request data."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator, field_validator
from datetime import date, datetime


class ShiftCreateRequest(BaseModel):
    """Validation model for shift creation."""
    дата: str = Field(..., description="Дата смены в формате YYYY-MM-DD")
    номер_смены: int = Field(..., ge=1, le=2, description="Номер смены (1 или 2)")
    контролеры: List[str] = Field(..., min_length=1, description="Список контролеров")
    
    @field_validator('дата')
    @classmethod
    def validate_date(cls, v):
        """Validate date format."""
        try:
            parsed = datetime.strptime(v, '%Y-%m-%d')
            if parsed.date() > datetime.now().date() + datetime.timedelta(days=1):
                raise ValueError("Дата не может быть в будущем")
            return v
        except ValueError as e:
            if "does not match format" in str(e):
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")
            raise


class ControlDataRequest(BaseModel):
    """Validation model for control data."""
    номер_маршрутной_карты: str = Field(..., pattern=r'^\d{6}$', description="6-значный номер маршрутной карты")
    всего_отлито: int = Field(..., gt=0, le=100000, description="Количество отлитых деталей")
    всего_принято: int = Field(..., ge=0, le=100000, description="Количество принятых деталей")
    контролер: str = Field(..., min_length=1, max_length=255, description="Имя контролера")
    заметки: Optional[str] = Field(None, max_length=1000, description="Заметки")
    дефекты: Dict[str, int] = Field(default_factory=dict, description="Дефекты")
    
    @field_validator('всего_принято')
    @classmethod
    def validate_accepted(cls, v, info):
        """Validate that accepted doesn't exceed cast."""
        if 'всего_отлито' in info.data and v > info.data['всего_отлито']:
            raise ValueError("Количество принятых не может превышать отлитых")
        return v
    
    @field_validator('дефекты')
    @classmethod
    def validate_defects(cls, v):
        """Validate defects data."""
        for key, value in v.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Неверное значение дефекта '{key}'")
            if value > 100000:
                raise ValueError(f"Слишком большое значение дефекта '{key}'")
        return v


class ControllerRequest(BaseModel):
    """Validation model for controller operations."""
    имя: str = Field(..., min_length=1, max_length=255, description="Имя контролера")
    активен: Optional[bool] = Field(True, description="Статус активности")


class RouteCardSearchRequest(BaseModel):
    """Validation model for route card search."""
    номер_карты: str = Field(..., pattern=r'^\d{6}$', description="6-значный номер маршрутной карты")


class QRScanRequest(BaseModel):
    """Validation model for QR scan."""
    данные: str = Field(..., min_length=1, max_length=500, description="Данные QR кода")


class LoginRequest(BaseModel):
    """Validation model for login."""
    username: str = Field(..., min_length=3, max_length=100, description="Имя пользователя")
    password: str = Field(..., min_length=8, max_length=128, description="Пароль")


class ChangePasswordRequest(BaseModel):
    """Validation model for password change."""
    old_password: str = Field(..., min_length=8, max_length=128, description="Старый пароль")
    new_password: str = Field(..., min_length=8, max_length=128, description="Новый пароль")
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.islower() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v


class StatisticsQueryRequest(BaseModel):
    """Validation model for statistics query."""
    дата_начала: Optional[str] = Field(None, description="Дата начала в формате YYYY-MM-DD")
    дата_конца: Optional[str] = Field(None, description="Дата окончания в формате YYYY-MM-DD")
    контролер: Optional[str] = Field(None, max_length=255, description="Имя контролера")
    
    @field_validator('дата_начала', 'дата_конца')
    @classmethod
    def validate_dates(cls, v):
        """Validate date format."""
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")
        return v
