"""
SQLAlchemy session management and database initialization.
"""
import logging
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import current_app, g

from ..models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None


def get_engine():
    """Get or create the SQLAlchemy engine"""
    global _engine
    
    if _engine is None:
        db_path = current_app.config['DATABASE_PATH']
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory for database: {db_path.parent}")
        
        # Create engine with SQLite-specific settings
        database_url = f"sqlite:///{db_path}"
        _engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            connect_args={'check_same_thread': False}
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        logger.info(f"Created SQLAlchemy engine for database: {db_path}")
    
    return _engine


def get_session_factory():
    """Get or create the session factory"""
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
        )
        logger.info("Created SQLAlchemy session factory")
    
    return _session_factory


def get_db():
    """
    Get database session for Flask request context.
    Automatically managed by Flask's teardown.
    """
    if 'db_session' not in g:
        SessionFactory = get_session_factory()
        g.db_session = SessionFactory()
        logger.debug("Created new database session for request")
    
    return g.db_session


def get_session():
    """
    Get a new database session (for use outside request context).
    Caller is responsible for closing the session.
    """
    SessionFactory = get_session_factory()
    return SessionFactory()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    Usage:
        with session_scope() as session:
            session.add(obj)
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database tables"""
    try:
        engine = get_engine()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize default data
        from .init_data import initialize_default_data
        initialize_default_data()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def close_db(e=None):
    """Close database session at end of request"""
    db_session = g.pop('db_session', None)
    
    if db_session is not None:
        db_session.close()
        logger.debug("Closed database session")


def init_app(app):
    """Initialize database with Flask app"""
    app.teardown_appcontext(close_db)
    logger.info("Registered database teardown with Flask app")
