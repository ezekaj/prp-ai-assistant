#!/usr/bin/env python3
"""
Test script to verify PRP application can start
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check required environment variables
required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
missing_vars = []

for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"[ERROR] Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

print("[OK] Environment variables loaded successfully")
print(f"   DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"   PRP_ENV: {os.getenv('PRP_ENV', 'development')}")
print(f"   PORT: {os.getenv('PORT', '8000')}")

# Try to import the app
try:
    from prp_app import app
    print("[OK] PRP app imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import app: {e}")
    sys.exit(1)

# Try to run the app
if __name__ == '__main__':
    print("\n[STARTING] PRP application...")
    print("   Access the app at: http://localhost:8000")
    print("   Health check at: http://localhost:8000/health")
    print("   Press Ctrl+C to stop\n")
    
    try:
        app.run(
            host='0.0.0.0', 
            port=int(os.getenv('PORT', '8000')),
            debug=os.getenv('PRP_ENV') == 'development'
        )
    except Exception as e:
        print(f"[ERROR] Failed to start app: {e}")
        sys.exit(1)