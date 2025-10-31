"""
SQLAlchemy models for the Quality Control application.
"""
from .base import Base
from .controller import Контролёр
from .defect import КатегорияДефекта, ТипДефекта
from .shift import Смена
from .control import ЗаписьКонтроля, ДефектЗаписи

__all__ = [
    'Base',
    'Контролёр',
    'КатегорияДефекта',
    'ТипДефекта',
    'Смена',
    'ЗаписьКонтроля',
    'ДефектЗаписи'
]
