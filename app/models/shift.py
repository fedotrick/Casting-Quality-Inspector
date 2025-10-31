"""
Shift model.
"""
from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Смена(Base):
    """Shift model - смены table"""
    __tablename__ = 'смены'
    __table_args__ = (
        Index('idx_смены_статус_дата', 'статус', 'дата'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    дата: Mapped[str] = mapped_column(String, nullable=False)
    номер_смены: Mapped[int] = mapped_column(Integer, nullable=False)
    старший: Mapped[str] = mapped_column(String, default='Контролеры', nullable=False)
    контролеры: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    время_начала: Mapped[str] = mapped_column(String, nullable=False)
    время_окончания: Mapped[str] = mapped_column(String, nullable=True)
    статус: Mapped[str] = mapped_column(String, default='активна', nullable=False)
    
    # Relationships
    записи = relationship("ЗаписьКонтроля", back_populates="смена")
    
    def __repr__(self):
        return f"<Смена(id={self.id}, дата='{self.дата}', номер_смены={self.номер_смены}, статус='{self.статус}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        import json
        return {
            'id': self.id,
            'дата': self.дата,
            'номер_смены': self.номер_смены,
            'старший': self.старший,
            'контролеры': json.loads(self.контролеры) if self.контролеры else [],
            'время_начала': self.время_начала,
            'время_окончания': self.время_окончания,
            'статус': self.статус
        }
