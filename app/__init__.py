"""
Flask application factory.
"""
import logging
from pathlib import Path
from flask import Flask
from flask_cors import CORS

from .config import config
from .helpers.logging_config import setup_logging
from .database import init_db, init_app as init_database_app


def create_app(config_name='default'):
    """
    Application factory function.
    
    Args:
        config_name: Configuration name (default, development, production, testing)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Setup logging
    setup_logging(
        log_level=app.config['LOG_LEVEL'],
        log_file=app.config['LOG_FILE']
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Quality Control Application with config: {config_name}")
    
    # Enable CORS if configured
    if app.config['CORS_ENABLED']:
        CORS(app)
    
    # Initialize database with SQLAlchemy (within app context)
    with app.app_context():
        try:
            # Register teardown handler
            init_database_app(app)
            
            # Initialize database tables and default data
            init_db()
            logger.info("Database initialized successfully with SQLAlchemy")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    # Register blueprints
    from .blueprints.ui import ui_bp
    from .blueprints.api import api_bp
    
    app.register_blueprint(ui_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    logger.info("Application created successfully")
    
    return app
