#!/usr/bin/env python3
"""
Celery task queue for PRP System - Factor VIII Compliance
"""

import os
from celery import Celery
from sqlalchemy import create_engine
from redis import Redis
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
celery_app = Celery('prp_tasks')
celery_app.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_concurrency=int(os.environ.get('CELERY_CONCURRENCY', '4')),
    task_routes={
        'prp_tasks.generate_prp_async': {'queue': 'prp_generation'},
        'prp_tasks.analyze_codebase_async': {'queue': 'analysis'},
        'prp_tasks.compute_analytics_async': {'queue': 'analytics'},
    },
    task_annotations={
        'prp_tasks.generate_prp_async': {'rate_limit': '10/m'},
        'prp_tasks.compute_analytics_async': {'rate_limit': '5/m'},
    }
)

# Initialize backing services for tasks
def get_db_engine():
    """Get database engine from environment"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return create_engine(database_url)

def get_redis_client():
    """Get Redis client from environment"""
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    return Redis.from_url(redis_url)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def generate_prp_async(self, feature_name, requirements, complexity=5):
    """Asynchronous PRP generation task"""
    try:
        from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
        
        db_engine = get_db_engine()
        redis_client = get_redis_client()
        
        generator = StatelessPRPGenerator(db_engine, redis_client)
        result = generator.generate_prp(feature_name, requirements, complexity)
        
        # Store result in Redis for retrieval
        redis_client.setex(
            f"prp_result:{self.request.id}",
            3600,  # 1 hour expiry
            str(result)
        )
        
        return {
            'task_id': self.request.id,
            'status': 'completed',
            'prp_id': result.get('prp_id'),
            'message': 'PRP generated successfully'
        }
        
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def analyze_codebase_async(self, project_path):
    """Asynchronous codebase analysis task"""
    try:
        from PRPs.scripts.prp_generator_stateless import StatelessPRPGenerator
        
        db_engine = get_db_engine()
        redis_client = get_redis_client()
        
        generator = StatelessPRPGenerator(db_engine, redis_client)
        patterns = generator.analyze_codebase_patterns(project_path)
        
        # Cache analysis results
        redis_client.setex(
            f"codebase_analysis:{project_path}",
            7200,  # 2 hours expiry
            str(patterns)
        )
        
        return {
            'task_id': self.request.id,
            'status': 'completed',
            'patterns': patterns,
            'message': 'Codebase analysis completed'
        }
        
    except Exception as exc:
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True)
def compute_analytics_async(self, date_range=None):
    """Asynchronous analytics computation task"""
    try:
        from PRPs.scripts.prp_analytics_stateless import StatelessPRPAnalytics
        
        db_engine = get_db_engine()
        redis_client = get_redis_client()
        
        analytics = StatelessPRPAnalytics(db_engine, redis_client)
        dashboard_data = analytics.compute_dashboard_metrics(date_range)
        
        return {
            'task_id': self.request.id,
            'status': 'completed',
            'dashboard_data': dashboard_data,
            'message': 'Analytics computation completed'
        }
        
    except Exception as exc:
        raise self.retry(countdown=120, exc=exc)

@celery_app.task
def cleanup_expired_data():
    """Periodic cleanup task"""
    try:
        redis_client = get_redis_client()
        db_engine = get_db_engine()
        
        # Clean up expired analysis data
        retention_days = int(os.environ.get('ANALYTICS_RETENTION_DAYS', '90'))
        
        with db_engine.connect() as conn:
            conn.execute(
                "DELETE FROM prp_analytics WHERE created_at < NOW() - INTERVAL %s DAY",
                (retention_days,)
            )
        
        return {'status': 'completed', 'message': 'Cleanup completed'}
        
    except Exception as exc:
        raise exc

# Periodic task scheduling
celery_app.conf.beat_schedule = {
    'cleanup-expired-data': {
        'task': 'prp_tasks.cleanup_expired_data',
        'schedule': 86400.0,  # Daily
    },
}

if __name__ == '__main__':
    celery_app.start()