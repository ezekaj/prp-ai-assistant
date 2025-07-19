#!/usr/bin/env python3
"""
Configuration management for PRP System - Factor III Compliance
"""

import os
from typing import Optional
from logging_config import configure_logging, get_logger

# Configure logging on import
configure_logging()
logger = get_logger(__name__)

class Config:
    """Base configuration class using environment variables"""
    
    # Application settings - NO DEFAULT SECRETS
    SECRET_KEY: str = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY: str = os.environ.get('JWT_SECRET_KEY')
    PRP_ENV: str = os.environ.get('PRP_ENV', 'development')
    PORT: int = int(os.environ.get('PORT', '8000'))
    
    # Database configuration with connection pooling
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'postgresql://localhost/prp_dev')
    
    # Database pool configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '20')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '40')),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
        'pool_pre_ping': True,
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true'
    }
    
    # Redis configuration
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_POOL_SIZE: int = int(os.environ.get('REDIS_POOL_SIZE', '10'))
    REDIS_TIMEOUT: int = int(os.environ.get('REDIS_TIMEOUT', '5'))
    
    # Analytics settings
    ANALYTICS_RETENTION_DAYS: int = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))
    MAX_PRP_COMPLEXITY: int = int(os.environ.get('MAX_PRP_COMPLEXITY', '10'))
    DEFAULT_SUCCESS_THRESHOLD: float = float(os.environ.get('DEFAULT_SUCCESS_THRESHOLD', '0.8'))
    
    # Feature flags
    ENABLE_PREDICTIVE_ANALYSIS: bool = os.environ.get('ENABLE_PREDICTIVE_ANALYSIS', 'true').lower() == 'true'
    ENABLE_SECURITY_SCANNING: bool = os.environ.get('ENABLE_SECURITY_SCANNING', 'true').lower() == 'true'
    ENABLE_PERFORMANCE_MONITORING: bool = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    
    # External service credentials
    CLAUDE_API_KEY: Optional[str] = os.environ.get('CLAUDE_API_KEY')
    GITHUB_TOKEN: Optional[str] = os.environ.get('GITHUB_TOKEN')
    
    # Logging configuration
    LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.environ.get('LOG_FORMAT', 'text')  # 'text' or 'json'
    
    # Celery configuration
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    CELERY_CONCURRENCY: int = int(os.environ.get('CELERY_CONCURRENCY', '4'))
    
    # Web server configuration
    WEB_CONCURRENCY: int = int(os.environ.get('WEB_CONCURRENCY', '4'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing_vars = []
        
        for var in required_vars:
            value = getattr(cls, var)
            if not value:
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        # Validate secrets strength in production
        if cls.is_production():
            if len(cls.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            if len(cls.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.PRP_ENV.lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.PRP_ENV.lower() == 'development'

class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def validate(cls):
        """Additional production validation"""
        super().validate()
        
        # Ensure security settings in production
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production")
        
        if not cls.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY must be set in production")

class TestingConfig(Config):
    """Testing-specific configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/prp_test')
    REDIS_URL = os.environ.get('TEST_REDIS_URL', 'redis://localhost:6379/1')

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('PRP_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig

# Export the appropriate config
config = get_config()

if __name__ == '__main__':
    # Validate configuration when run directly
    try:
        config.validate()
        logger.info("configuration_validated", 
                   environment=config.PRP_ENV,
                   database_url=config.DATABASE_URL,
                   redis_url=config.REDIS_URL,
                   features={
                       "predictive": config.ENABLE_PREDICTIVE_ANALYSIS,
                       "security": config.ENABLE_SECURITY_SCANNING,
                       "monitoring": config.ENABLE_PERFORMANCE_MONITORING
                   })
    except ValueError as e:
        logger.error("configuration_validation_failed", error=str(e))
        exit(1)