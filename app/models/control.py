"""
Control record and defect models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ЗаписьКонтроля(Base):
    """Control record model - записи_контроля table"""
    __tablename__ = 'записи_контроля'
    __table_args__ = (
        Index('idx_записи_смена', 'смена_id'),
        Index('idx_записи_маршрутная_карта', 'номер_маршрутной_карты'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    смена_id: Mapped[int] = mapped_column(Integer, ForeignKey('смены.id'), nullable=False)
    номер_маршрутной_карты: Mapped[str] = mapped_column(String, nullable=False)
    всего_отлито: Mapped[int] = mapped_column(Integer, nullable=False)
    всего_принято: Mapped[int] = mapped_column(Integer, nullable=False)
    контролер: Mapped[str] = mapped_column(String, nullable=False)
    заметки: Mapped[str] = mapped_column(Text, nullable=True)
    создана: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    смена = relationship("Смена", back_populates="записи")
    дефекты = relationship("ДефектЗаписи", back_populates="запись")
    
    def __repr__(self):
        return f"<ЗаписьКонтроля(id={self.id}, смена_id={self.смена_id}, номер_маршрутной_карты='{self.номер_маршрутной_карты}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'смена_id': self.смена_id,
            'номер_маршрутной_карты': self.номер_маршрутной_карты,
            'всего_отлито': self.всего_отлито,
            'всего_принято': self.всего_принято,
            'контролер': self.контролер,
            'заметки': self.заметки,
            'создана': self.создана.isoformat() if self.создана else None
        }


class ДефектЗаписи(Base):
    """Record defect model - дефекты_записей table"""
    __tablename__ = 'дефекты_записей'
    __table_args__ = (
        Index('idx_дефекты_запись', 'запись_контроля_id'),
        Index('idx_дефекты_тип', 'тип_дефекта_id'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    запись_контроля_id: Mapped[int] = mapped_column(Integer, ForeignKey('записи_контроля.id'), nullable=False)
    тип_дефекта_id: Mapped[int] = mapped_column(Integer, ForeignKey('типы_дефектов.id'), nullable=False)
    количество: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    запись = relationship("ЗаписьКонтроля", back_populates="дефекты")
    тип_дефекта = relationship("ТипДефекта")
    
    def __repr__(self):
        return f"<ДефектЗаписи(id={self.id}, запись_контроля_id={self.запись_контроля_id}, количество={self.количество})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'запись_контроля_id': self.запись_контроля_id,
            'тип_дефекта_id': self.тип_дефекта_id,
            'количество': self.количество
        }
