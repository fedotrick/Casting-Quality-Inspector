"""
Configuration module for the Quality Control application.
Reads from environment variables with sensible defaults.
"""
import os
from pathlib import Path


class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'corrected-foundry-system-2024')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.getenv('SESSION_DIR', './sessions')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'qc_'
    
    # Database paths (keep Cyrillic table names)
    DATABASE_PATH = Path(os.getenv('DATABASE_PATH', 'data/quality_control.db'))
    FOUNDRY_DB_PATH = Path(os.getenv('FOUNDRY_DB_PATH', r'C:\Users\1\Telegram\MetalFusionX\foundry.db'))
    ROUTE_CARDS_DB_PATH = Path(os.getenv('ROUTE_CARDS_DB_PATH', r'C:\Users\1\Telegram\FoamFusionLab\data\маршрутные_карты.db'))
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.getenv('LOG_FILE', 'logs/application.log'))
    
    # Feature flags
    ENABLE_EXTERNAL_DB = os.getenv('ENABLE_EXTERNAL_DB', 'true').lower() == 'true'
    ENABLE_AUTO_SHIFT_CLOSE = os.getenv('ENABLE_AUTO_SHIFT_CLOSE', 'true').lower() == 'true'
    
    # CORS configuration
    CORS_ENABLED = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
    
    # Application settings
    MAX_DEFECT_COUNT = int(os.getenv('MAX_DEFECT_COUNT', '10000'))
    MAX_CAST_COUNT = int(os.getenv('MAX_CAST_COUNT', '10000'))
    
    # All defect types from control.xlsx
    DEFECT_TYPES = {
        "second_grade": {
            "name": "Второй сорт",
            "types": ["Раковины", "Зарез литейный", "Зарез пеномодельный"]
        },
        "rework": {
            "name": "Доработка", 
            "types": [
                "Раковины", "Несоответствие размеров", "Несоответствие внешнего вида",
                "Наплыв металла", "Прорыв металла", "Вырыв", "Облой", "Песок на поверхности",
                "Песок в резьбе", "Клей", "Коробление", "Дефект пеномодели", "Лапы",
                "Питатель", "Корона", "Смещение", "Клей подтёк", "Клей по шву"
            ]
        },
        "final_reject": {
            "name": "Окончательный брак",
            "types": [
                "Недолив", "Вырыв", "Коробление", "Наплыв металла",
                "Нарушение геометрии", "Нарушение маркировки", "Непроклей", "Неслитина",
                "Несоответствие внешнего вида", "Несоответствие размеров", "Пеномодель",
                "Пористость", "Пригар песка", "Прочее", "Рыхлота", "Раковины",
                "Скол", "Слом", "Спай", "Трещины", "Зарез литейный", "Зарез пеномодельный"
            ]
        }
    }

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        Path(Config.SESSION_FILE_DIR).mkdir(exist_ok=True)
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_PATH = Path(':memory:')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
