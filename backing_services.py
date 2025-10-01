"""
Backing Services Manager
Manages database and cache connections with proper lifecycle management
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, Engine, pool
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from redis import Redis, ConnectionPool
import logging
from flask import g

logger = logging.getLogger(__name__)


class BackingServicesManager:
    """Centralized manager for all backing services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._db_engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._redis_pool: Optional[ConnectionPool] = None
        self._redis_client: Optional[Redis] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize all backing services"""
        if self._initialized:
            logger.warning("Backing services already initialized")
            return
        
        try:
            self._init_database()
            self._init_redis()
            self._initialized = True
            logger.info("All backing services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize backing services: {e}")
            self.cleanup()
            raise
    
    def _init_database(self):
        """Initialize database with connection pooling"""
        db_url = self.config.get('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL is required")
        
        # Create engine with optimized pooling
        if 'sqlite' in db_url:
            # SQLite doesn't support connection pooling
            self._db_engine = create_engine(
                db_url,
                poolclass=pool.NullPool,
                echo=self.config.get('DB_ECHO', False)
            )
        else:
            # PostgreSQL, MySQL etc. with full pooling
            self._db_engine = create_engine(
                db_url,
                pool_size=self.config.get('DB_POOL_SIZE', 20),
                max_overflow=self.config.get('DB_MAX_OVERFLOW', 40),
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=self.config.get('DB_ECHO', False)
            )
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._db_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Create scoped session for thread safety
        self._scoped_session = scoped_session(self._session_factory)
        
        # Test connection
        with self._db_engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        
        logger.info(f"Database initialized: {db_url.split('@')[-1]}")
    
    def _init_redis(self):
        """Initialize Redis with connection pooling"""
        redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            # Create connection pool
            self._redis_pool = ConnectionPool.from_url(
                redis_url,
                max_connections=self.config.get('REDIS_MAX_CONNECTIONS', 50),
                decode_responses=True,
                socket_connect_timeout=self.config.get('REDIS_TIMEOUT', 5),
                socket_timeout=self.config.get('REDIS_TIMEOUT', 5),
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Create Redis client
            self._redis_client = Redis(connection_pool=self._redis_pool)
            
            # Test connection
            self._redis_client.ping()
            logger.info("Redis initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            logger.warning("Continuing without Redis caching")
            self._redis_client = None
    
    @property
    def db_engine(self) -> Optional[Engine]:
        """Get database engine"""
        if not self._initialized:
            raise RuntimeError("Backing services not initialized")
        return self._db_engine
    
    @property
    def redis_client(self) -> Optional[Redis]:
        """Get Redis client"""
        if not self._initialized:
            raise RuntimeError("Backing services not initialized")
        return self._redis_client
    
    def get_db_session(self) -> Session:
        """Get a new database session"""
        if not self._initialized:
            raise RuntimeError("Backing services not initialized")
        return self._scoped_session()
    
    @contextmanager
    def db_session_scope(self):
        """Provide a transactional scope for database operations"""
        session = self.get_db_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def init_flask_app(self, app):
        """Initialize Flask app with backing services"""
        # Store reference in app config
        app.config['backing_services'] = self
        
        # Add before_request handler to create session
        @app.before_request
        def create_db_session():
            if not hasattr(g, 'db_session'):
                g.db_session = self.get_db_session()
        
        # Add teardown handler to cleanup session
        @app.teardown_appcontext
        def cleanup_db_session(error=None):
            if hasattr(g, 'db_session'):
                if error:
                    g.db_session.rollback()
                g.db_session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all backing services"""
        health = {
            'database': 'unknown',
            'redis': 'unknown',
            'details': {}
        }
        
        # Check database
        if self._db_engine:
            try:
                with self._db_engine.connect() as conn:
                    from sqlalchemy import text
                    conn.execute(text("SELECT 1"))
                health['database'] = 'healthy'
                health['details']['db_pool'] = {
                    'size': self._db_engine.pool.size(),
                    'checked_in': self._db_engine.pool.checkedin(),
                    'overflow': self._db_engine.pool.overflow(),
                    'total': self._db_engine.pool.total()
                }
            except Exception as e:
                health['database'] = 'unhealthy'
                health['details']['db_error'] = str(e)
        
        # Check Redis
        if self._redis_client:
            try:
                self._redis_client.ping()
                info = self._redis_client.info()
                health['redis'] = 'healthy'
                health['details']['redis_info'] = {
                    'version': info.get('redis_version'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory_human': info.get('used_memory_human'),
                    'uptime_in_days': info.get('uptime_in_days')
                }
            except Exception as e:
                health['redis'] = 'unhealthy'
                health['details']['redis_error'] = str(e)
        else:
            health['redis'] = 'not_configured'
        
        return health
    
    def cleanup(self):
        """Cleanup all connections"""
        logger.info("Cleaning up backing services...")
        
        # Close database connections
        if self._scoped_session:
            self._scoped_session.remove()
        
        if self._db_engine:
            self._db_engine.dispose()
            logger.info("Database connections closed")
        
        # Close Redis connections
        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis connections closed")
        
        self._initialized = False
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Singleton instance
_backing_services: Optional[BackingServicesManager] = None


def get_backing_services() -> BackingServicesManager:
    """Get the global backing services instance"""
    global _backing_services
    if _backing_services is None:
        raise RuntimeError("Backing services not initialized. Call init_backing_services first.")
    return _backing_services


def init_backing_services(config: Dict[str, Any]) -> BackingServicesManager:
    """Initialize the global backing services instance"""
    global _backing_services
    if _backing_services is not None:
        logger.warning("Backing services already initialized")
        return _backing_services
    
    _backing_services = BackingServicesManager(config)
    _backing_services.initialize()
    return _backing_services


def cleanup_backing_services():
    """Cleanup the global backing services instance"""
    global _backing_services
    if _backing_services:
        _backing_services.cleanup()
        _backing_services = None