#!/usr/bin/env python3
"""
Configuration management for PRP System - Factor III Compliance
"""

import os
from typing import Optional

class Config:
    """Base configuration class using environment variables"""
    
    # Application settings
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    PRP_ENV: str = os.environ.get('PRP_ENV', 'development')
    PORT: int = int(os.environ.get('PORT', '8000'))
    
    # Database configuration
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'postgresql://localhost/prp_dev')
    
    # Redis configuration
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
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
        required_vars = ['SECRET_KEY', 'DATABASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(cls, var) or getattr(cls, var) == f'dev-{var.lower()}-change-in-production':
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
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
        print(f"✅ Configuration valid for {config.PRP_ENV} environment")
        print(f"Database: {config.DATABASE_URL}")
        print(f"Redis: {config.REDIS_URL}")
        print(f"Features enabled: Predictive={config.ENABLE_PREDICTIVE_ANALYSIS}, "
              f"Security={config.ENABLE_SECURITY_SCANNING}, "
              f"Monitoring={config.ENABLE_PERFORMANCE_MONITORING}")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)