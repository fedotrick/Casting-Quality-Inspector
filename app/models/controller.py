"""
Controller model.
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Контролёр(Base):
    """Controller model - контролеры table"""
    __tablename__ = 'контролеры'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    имя: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    активен: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Контролёр(id={self.id}, имя='{self.имя}', активен={self.активен})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'имя': self.имя,
            'активен': self.активен
        }
