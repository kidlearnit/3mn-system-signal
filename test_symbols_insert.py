#!/usr/bin/env python3
"""
Test script to verify symbols insertion in MySQL database
"""

import os
import sys
import pymysql
from sqlalchemy import create_engine, text

# Add backend to path
sys.path.append('backend')

def test_direct_connection():
    """Test direct PyMySQL connection."""
    print("🔍 Testing direct PyMySQL connection...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3309,
            user='trader',
            password='traderpass',
            database='trading',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Check symbols table
            cursor.execute("SELECT COUNT(*) FROM symbols")
            count = cursor.fetchone()
            print(f"✅ Found {count[0]} symbols in database")
            
            # Show symbols by exchange
            cursor.execute("""
                SELECT exchange, currency, COUNT(*) as count 
                FROM symbols 
                WHERE active = 1 
                GROUP BY exchange, currency 
                ORDER BY exchange, currency
            """)
            exchanges = cursor.fetchall()
            
            print("\n📊 Symbols by Exchange:")
            for exchange, currency, count in exchanges:
                print(f"   {exchange} ({currency}): {count} symbols")
            
            # Show sample symbols
            cursor.execute("""
                SELECT ticker, exchange, currency, active 
                FROM symbols 
                ORDER BY exchange, ticker 
                LIMIT 10
            """)
            symbols = cursor.fetchall()
            
            print("\n📋 Sample Symbols:")
            for ticker, exchange, currency, active in symbols:
                status = "✅" if active else "❌"
                print(f"   {status} {ticker} ({exchange}, {currency})")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\n🔍 Testing SQLAlchemy connection...")
    
    try:
        from app.db_config import get_database_url
        
        database_url = get_database_url()
        print(f"📍 Using database URL: {database_url}")
        
        engine = create_engine(database_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Check symbols table
            result = conn.execute(text("SELECT COUNT(*) FROM symbols"))
            count = result.fetchone()
            print(f"✅ Found {count[0]} symbols in database")
            
            # Show symbols by exchange
            result = conn.execute(text("""
                SELECT exchange, currency, COUNT(*) as count 
                FROM symbols 
                WHERE active = 1 
                GROUP BY exchange, currency 
                ORDER BY exchange, currency
            """))
            exchanges = result.fetchall()
            
            print("\n📊 Symbols by Exchange:")
            for exchange, currency, count in exchanges:
                print(f"   {exchange} ({currency}): {count} symbols")
            
            # Show US stocks (for email digest)
            result = conn.execute(text("""
                SELECT ticker, exchange 
                FROM symbols 
                WHERE exchange IN ('NASDAQ', 'NYSE') AND active = 1
                ORDER BY ticker
            """))
            us_stocks = result.fetchall()
            
            print(f"\n🇺🇸 US Stocks ({len(us_stocks)} symbols):")
            tickers = [stock[0] for stock in us_stocks]
            print(f"   {', '.join(tickers)}")
            
            # Show Vietnamese stocks
            result = conn.execute(text("""
                SELECT ticker, exchange 
                FROM symbols 
                WHERE exchange = 'HOSE' AND active = 1
                ORDER BY ticker
            """))
            vn_stocks = result.fetchall()
            
            print(f"\n🇻🇳 Vietnamese Stocks ({len(vn_stocks)} symbols):")
            tickers = [stock[0] for stock in vn_stocks]
            print(f"   {', '.join(tickers)}")
            
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

def check_email_digest_symbols():
    """Check if symbols match EMAIL_DIGEST_SYMBOLS configuration."""
    print("\n🔍 Checking EMAIL_DIGEST_SYMBOLS configuration...")
    
    # Get configured symbols from .env
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        for line in env_content.split('\n'):
            if line.startswith('EMAIL_DIGEST_SYMBOLS='):
                configured_symbols = line.split('=')[1].strip().split(',')
                configured_symbols = [s.strip() for s in configured_symbols]
                break
        else:
            print("❌ EMAIL_DIGEST_SYMBOLS not found in .env")
            return False
        
        print(f"📧 Configured symbols: {', '.join(configured_symbols)}")
        
        # Check if all configured symbols exist in database
        try:
            from app.db_config import get_database_url
            database_url = get_database_url()
            engine = create_engine(database_url, pool_pre_ping=True)
            
            with engine.connect() as conn:
                placeholders = ','.join(['%s'] * len(configured_symbols))
                query = f"""
                    SELECT ticker, exchange, active 
                    FROM symbols 
                    WHERE ticker IN ({placeholders})
                    ORDER BY ticker
                """
                result = conn.execute(text(query), configured_symbols)
                db_symbols = result.fetchall()
                
                print(f"\n📊 Database check:")
                print(f"   Configured: {len(configured_symbols)} symbols")
                print(f"   Found in DB: {len(db_symbols)} symbols")
                
                if len(db_symbols) == len(configured_symbols):
                    print("✅ All configured symbols found in database")
                else:
                    print("⚠️  Some symbols missing from database")
                    
                    # Find missing symbols
                    db_tickers = [symbol[0] for symbol in db_symbols]
                    missing = [s for s in configured_symbols if s not in db_tickers]
                    if missing:
                        print(f"   Missing: {', '.join(missing)}")
                
                # Show status of each symbol
                print(f"\n📋 Symbol Status:")
                for ticker, exchange, active in db_symbols:
                    status = "✅ Active" if active else "❌ Inactive"
                    print(f"   {ticker} ({exchange}): {status}")
                
        except Exception as e:
            print(f"❌ Database check failed: {e}")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ .env file not found")
        return False
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Symbols Database Setup")
    print("=" * 50)
    
    tests = [
        test_direct_connection,
        test_sqlalchemy_connection,
        check_email_digest_symbols
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print(f"✅ Successful tests: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! Symbols database is properly configured.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Docker containers are running: docker compose ps")
        print("2. Check MySQL is accessible: telnet localhost 3309")
        print("3. Verify mysql-init scripts were executed")
        print("4. Check MySQL logs: docker compose logs mysql")

if __name__ == '__main__':
    main()
