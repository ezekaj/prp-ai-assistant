#!/usr/bin/env python3
"""
Database models for stateless PRP system
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from logging_config import get_logger

logger = get_logger(__name__)

Base = declarative_base()

class PRPRecord(Base):
    """PRP generation and tracking record"""
    __tablename__ = 'prp_records'
    
    id = Column(String, primary_key=True)
    feature_name = Column(String(255), nullable=False)
    requirements = Column(Text)
    complexity = Column(Integer, default=5)
    estimated_time = Column(Float)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    patterns_used = Column(JSON)
    success_score = Column(Float)

class PRPAnalytics(Base):
    """Analytics and performance tracking"""
    __tablename__ = 'prp_analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prp_id = Column(String, nullable=False)
    complexity = Column(Integer)
    estimated_time = Column(Float)
    actual_time = Column(Float)
    success_rate = Column(Float)
    test_coverage = Column(Float)
    performance_score = Column(Float)
    issues_encountered = Column(JSON)
    patterns_used = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class CodebasePattern(Base):
    """Detected codebase patterns for intelligent PRP generation"""
    __tablename__ = 'codebase_patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_path = Column(String(500))
    pattern_type = Column(String(100))
    pattern_data = Column(JSON)
    confidence_score = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

class SystemMetrics(Base):
    """System performance and health metrics"""
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

def create_tables(database_url=None):
    """Create all tables in the database"""
    if not database_url:
        database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(database_url=None):
    """Get database session"""
    engine = create_tables(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == '__main__':
    # Create tables if run directly
    engine = create_tables()
    logger.info("database_tables_created_successfully", database_url=os.environ.get('DATABASE_URL', 'default'))