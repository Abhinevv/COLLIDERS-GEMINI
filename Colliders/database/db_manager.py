"""
Database Manager for COLLIDERS
Handles database connections and operations
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from .models import Base
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manage database connections and sessions"""
    
    def __init__(self, db_path='data/colliders.db'):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = None
        self.Session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and create tables"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create engine with NullPool for better multi-threading support
        # NullPool creates a new connection for each request and closes it immediately
        db_url = f'sqlite:///{self.db_path}'
        self.engine = create_engine(
            db_url,
            connect_args={
                'check_same_thread': False,
                'timeout': 30  # 30 second timeout for locks
            },
            poolclass=NullPool,  # No connection pooling - better for SQLite threading
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_session(self):
        """
        Get a new database session
        
        Returns:
            SQLAlchemy session
        """
        return self.Session()
    
    def close_session(self, session):
        """
        Close a database session
        
        Args:
            session: SQLAlchemy session to close
        """
        if session:
            session.close()
    
    def remove_thread_session(self):
        """
        Remove the current thread's session from the scoped session registry.
        This is useful for background threads to ensure they get a fresh session.
        """
        if self.Session:
            self.Session.remove()
    
    def reset_database(self):
        """Drop all tables and recreate them (USE WITH CAUTION)"""
        logger.warning("Resetting database - all data will be lost!")
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        logger.info("Database reset complete")
    
    def backup_database(self, backup_path):
        """
        Create a backup of the database
        
        Args:
            backup_path: Path for backup file
        """
        import shutil
        try:
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False


# Global database manager instance
_db_manager = None


def get_db_manager(db_path='data/colliders.db'):
    """
    Get or create global database manager instance
    
    Args:
        db_path: Path to database file
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager

