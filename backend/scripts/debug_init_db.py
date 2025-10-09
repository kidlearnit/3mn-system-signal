#!/usr/bin/env python3
"""
Debug init_db function
"""

import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_init_db():
    """Debug init_db"""
    
    print("🔍 DEBUG INIT_DB")
    print("=" * 30)
    
    try:
        # Import
        from app.db import SessionLocal, init_db
        print(f"1. Before init_db: SessionLocal = {SessionLocal}")
        
        # Get DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        print(f"2. DATABASE_URL = {database_url}")
        
        # Call init_db
        print("3. Calling init_db...")
        init_db(database_url)
        
        print(f"4. After init_db: SessionLocal = {SessionLocal}")
        
        if SessionLocal is None:
            print("❌ SessionLocal is still None after init_db")
            return False
        
        # Test connection
        print("5. Testing connection...")
        with SessionLocal() as session:
            result = session.execute("SELECT 1").fetchone()
            print(f"✅ Connection OK: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_init_db()
    sys.exit(0 if success else 1)
