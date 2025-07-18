#!/usr/bin/env python3
"""
Health check script for containerized PRP system
"""

import os
import sys
import requests
import psycopg2
import redis
from datetime import datetime

def check_database():
    """Check database connectivity"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return False, "DATABASE_URL not configured"
        
        # Parse connection details from URL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return True, "Database connection OK"
    except Exception as e:
        return False, f"Database connection failed: {e}"

def check_redis():
    """Check Redis connectivity"""
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.Redis.from_url(redis_url)
        client.ping()
        client.close()
        
        return True, "Redis connection OK"
    except Exception as e:
        return False, f"Redis connection failed: {e}"

def check_application():
    """Check application health endpoint"""
    try:
        port = os.environ.get('PORT', '8000')
        response = requests.get(f'http://localhost:{port}/health', timeout=5)
        
        if response.status_code == 200:
            return True, "Application health check OK"
        else:
            return False, f"Application returned status {response.status_code}"
    except Exception as e:
        return False, f"Application health check failed: {e}"

def main():
    """Run all health checks"""
    checks = [
        ("Database", check_database),
        ("Redis", check_redis),
        ("Application", check_application)
    ]
    
    all_passed = True
    results = []
    
    for name, check_func in checks:
        passed, message = check_func()
        results.append((name, passed, message))
        if not passed:
            all_passed = False
    
    # Print results
    print(f"Health Check Report - {datetime.now().isoformat()}")
    print("=" * 50)
    
    for name, passed, message in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status} - {message}")
    
    print("=" * 50)
    print(f"Overall Status: {'✅ HEALTHY' if all_passed else '❌ UNHEALTHY'}")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()