#!/usr/bin/env python3
"""
Test database connection
"""

import pymysql

def test_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        # Test connection
        connection = pymysql.connect(
            host='localhost',
            port=3309,
            user='root',
            password='123456',
            database='trading_signals'
        )
        
        print("✅ Database connection successful!")
        
        # Test query
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM signals")
            result = cursor.fetchone()
            print(f"📊 Total signals: {result[0]}")
            
            # Check recent signals
            cursor.execute("""
                SELECT id, symbol_id, signal_type, timeframe, strategy_id, ts
                FROM signals 
                ORDER BY ts DESC 
                LIMIT 5
            """)
            results = cursor.fetchall()
            
            if results:
                print(f"📝 Recent signals:")
                for row in results:
                    print(f"   ID: {row[0]}, Symbol: {row[1]}, Type: {row[2]}, TF: {row[3]}, Strategy: {row[4]}, Time: {row[5]}")
            else:
                print("❌ No signals found")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Database Connection Test")
    print("=" * 40)
    
    success = test_connection()
    
    if success:
        print("\n✅ Database connection test completed!")
    else:
        print("\n❌ Database connection test failed!")
