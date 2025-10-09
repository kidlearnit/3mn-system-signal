#!/usr/bin/env python3
"""
Debug init_db function chi tiết
"""

import os
import sys
import traceback

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_init_db_detailed():
    """Debug init_db chi tiết"""
    
    print("🔍 DEBUG INIT_DB DETAILED")
    print("=" * 40)
    
    try:
        # Import
        from app.db import SessionLocal, init_db
        print(f"1. Before init_db: SessionLocal = {SessionLocal}")
        
        # Get DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        print(f"2. DATABASE_URL = {database_url}")
        
        # Test database connection manually
        print("3. Testing database connection manually...")
        from sqlalchemy import create_engine
        
        try:
            engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)
            print("✅ Engine created successfully")
            
            # Test connection
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                print(f"✅ Manual connection OK: {result}")
                
        except Exception as e:
            print(f"❌ Manual connection failed: {e}")
            return False
        
        # Call init_db with error handling
        print("4. Calling init_db with error handling...")
        try:
            init_db(database_url)
            print("✅ init_db called without exception")
        except Exception as e:
            print(f"❌ init_db failed: {e}")
            traceback.print_exc()
            return False
        
        print(f"5. After init_db: SessionLocal = {SessionLocal}")
        
        if SessionLocal is None:
            print("❌ SessionLocal is still None after init_db")
            
            # Try to import again
            print("6. Trying to import SessionLocal again...")
            from app.db import SessionLocal as SessionLocal2
            print(f"   SessionLocal2 = {SessionLocal2}")
            
            return False
        
        # Test connection
        print("7. Testing connection...")
        from sqlalchemy import text
        with SessionLocal() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            print(f"✅ Connection OK: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_init_db_detailed()
    sys.exit(0 if success else 1)
