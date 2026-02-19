"""
Database Connection Module

Database connection management with SQLite (dev) and PostgreSQL (prod) support.
"""

from typing import Optional
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
    
    def init_sqlite(self, db_path: str = "nanobot.db"):
        """Initialize SQLite database (for development)"""
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        self._session_factory = sessionmaker(bind=self._engine)
        return self
    
    def init_postgres(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "nanobot",
        username: str = "nanobot",
        password: str = ""
    ):
        """Initialize PostgreSQL database (for production)"""
        self._engine = create_engine(
            f"postgresql://{username}:{password}@{host}:{port}/{database}",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        self._session_factory = sessionmaker(bind=self._engine)
        return self
    
    def create_tables(self):
        """Create all tables"""
        from storage.models.models import Base
        Base.metadata.create_all(self._engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session (context manager)"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init_sqlite() or init_postgres() first.")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @property
    def engine(self):
        """Get engine"""
        return self._engine


# Global database manager
_db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get global database manager"""
    return _db_manager


def init_database(database_url: str = None):
    """Initialize database from URL or environment"""
    if database_url:
        if database_url.startswith("postgresql"):
            _db_manager.init_postgres()  # Will use URL
        else:
            _db_manager.init_sqlite(database_url)
    else:
        # Default to SQLite for development
        _db_manager.init_sqlite("nanobot.db")
    
    _db_manager.create_tables()
    return _db_manager
