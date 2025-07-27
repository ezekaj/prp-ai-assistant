#!/usr/bin/env python3
"""
Production-ready database configuration with connection pooling and monitoring
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
import time
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Base for models
Base = declarative_base()

class DatabaseConfig:
    """Production database configuration"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # PostgreSQL-specific optimizations
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        # Connection pool settings
        self.pool_size = int(os.environ.get('DB_POOL_SIZE', '20'))
        self.max_overflow = int(os.environ.get('DB_MAX_OVERFLOW', '40'))
        self.pool_recycle = int(os.environ.get('DB_POOL_RECYCLE', '3600'))
        self.pool_timeout = int(os.environ.get('DB_POOL_TIMEOUT', '30'))
        self.pool_pre_ping = True
        
        # Performance settings
        self.echo = os.environ.get('DB_ECHO', 'false').lower() == 'true'
        self.echo_pool = os.environ.get('DB_ECHO_POOL', 'false').lower() == 'true'
        
        # Create engine with production settings
        self.engine = self._create_engine()
        
        # Create session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)
        
        # Register event listeners
        self._register_listeners()
    
    def _create_engine(self):
        """Create SQLAlchemy engine with production configuration"""
        
        # PostgreSQL-specific pool class for better performance
        pool_class = pool.QueuePool
        if 'sqlite' in self.database_url:
            pool_class = pool.StaticPool
        
        engine = create_engine(
            self.database_url,
            poolclass=pool_class,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_timeout=self.pool_timeout,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo,
            echo_pool=self.echo_pool,
            connect_args={
                'connect_timeout': 10,
                'application_name': 'prp_system',
                'options': '-c statement_timeout=30000'  # 30 second statement timeout
            } if 'postgresql' in self.database_url else {}
        )
        
        return engine
    
    def _register_listeners(self):
        """Register database event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Configure connection on checkout"""
            connection_record.info['connect_time'] = time.time()
            
            # Set PostgreSQL-specific settings
            if 'postgresql' in self.database_url:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET idle_in_transaction_session_timeout = '10min'")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout"""
            checkout_time = time.time() - connection_record.info.get('connect_time', time.time())
            if checkout_time > 1.0:
                logger.warning(f"Slow connection checkout: {checkout_time:.2f}s")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Reset connection state on checkin"""
            if 'postgresql' in self.database_url:
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("RESET ALL")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self):
        """Perform database health check"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_pool_status(self):
        """Get connection pool status"""
        pool = self.engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow()
        }
    
    def close(self):
        """Close all database connections"""
        self.Session.remove()
        self.engine.dispose()

# Global database instance
_db_config = None

def get_db():
    """Get database configuration instance"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config

def init_db():
    """Initialize database tables"""
    db = get_db()
    Base.metadata.create_all(bind=db.engine)
    logger.info("Database tables initialized")

def close_db():
    """Close database connections"""
    global _db_config
    if _db_config:
        _db_config.close()
        _db_config = None
        logger.info("Database connections closed")