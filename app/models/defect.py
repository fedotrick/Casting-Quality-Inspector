"""
Defect category and type models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class КатегорияДефекта(Base):
    """Defect category model - категории_дефектов table"""
    __tablename__ = 'категории_дефектов'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    название: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    описание: Mapped[str] = mapped_column(Text, nullable=True)
    порядок_сортировки: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    создана: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    типы = relationship("ТипДефекта", back_populates="категория")
    
    def __repr__(self):
        return f"<КатегорияДефекта(id={self.id}, название='{self.название}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'название': self.название,
            'описание': self.описание,
            'порядок_сортировки': self.порядок_сортировки,
            'создана': self.создана.isoformat() if self.создана else None
        }


class ТипДефекта(Base):
    """Defect type model - типы_дефектов table"""
    __tablename__ = 'типы_дефектов'
    __table_args__ = (
        UniqueConstraint('категория_id', 'название', name='unique_category_defect'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    категория_id: Mapped[int] = mapped_column(Integer, ForeignKey('категории_дефектов.id'), nullable=False)
    название: Mapped[str] = mapped_column(String, nullable=False)
    описание: Mapped[str] = mapped_column(Text, nullable=True)
    активен: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    порядок_сортировки: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    создан: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    обновлен: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    категория = relationship("КатегорияДефекта", back_populates="типы")
    
    def __repr__(self):
        return f"<ТипДефекта(id={self.id}, название='{self.название}', категория_id={self.категория_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'категория_id': self.категория_id,
            'название': self.название,
            'описание': self.описание,
            'активен': self.активен,
            'порядок_сортировки': self.порядок_сортировки,
            'создан': self.создан.isoformat() if self.создан else None,
            'обновлен': self.обновлен.isoformat() if self.обновлен else None
        }
