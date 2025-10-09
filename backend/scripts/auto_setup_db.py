#!/usr/bin/env python3
"""
Script tự động setup database cho trading system
- Tạo database nếu chưa có
- Tạo user nếu chưa có
- Tạo tables nếu chưa có
- Seed initial data
"""

import os
import sys
import time
import pymysql
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def wait_for_mysql(max_retries=30, delay=2):
    """Đợi MySQL khởi động"""
    print("⏳ Waiting for MySQL to start...")
    
    for i in range(max_retries):
        try:
            # Try to connect to MySQL without database
            host = os.getenv("MYSQL_HOST", "mysql")
            port = int(os.getenv("MYSQL_PORT", "3306"))
            user = os.getenv("MYSQL_ROOT_USER", "root")
            password = os.getenv("MYSQL_ROOT_PASSWORD", "secret")
            
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                charset='utf8mb4'
            )
            conn.close()
            print("✅ MySQL is ready!")
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f"  ⏳ Attempt {i+1}/{max_retries}: {e}")
                time.sleep(delay)
            else:
                print(f"❌ MySQL connection failed after {max_retries} attempts: {e}")
                return False
    
    return False

def verify_database_exists():
    """Kiểm tra database có tồn tại không"""
    print("📊 Verifying database...")
    
    try:
        # Connect to existing database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            print("  ✅ Database connection verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("  💡 Make sure database is running and DATABASE_URL is correct")
        return False

def verify_database_user():
    """Kiểm tra database user có quyền truy cập không"""
    print("👤 Verifying database user...")
    
    try:
        # Connect with user credentials
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Test user permissions
            conn.execute(text("SELECT 1"))
            print("  ✅ Database user verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database user: {e}")
        print("  💡 Make sure database user has proper permissions")
        return False

def create_tables_if_not_exists():
    """Tạo tables nếu chưa có"""
    print("📋 Creating tables and views...")
    
    try:
        # Read single migration file
        migration_path = os.path.join(os.path.dirname(__file__), '..', 'database_migration.sql')
        if not os.path.exists(migration_path):
            print(f"❌ Migration file not found: {migration_path}")
            return False
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("  ✅ Database migration file loaded")
        
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Split SQL by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE', 'DELETE')):
                    try:
                        conn.execute(text(statement))
                        print(f"  ✅ Executed: {statement[:50]}...")
                    except Exception as e:
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            print(f"  ℹ️ Already exists: {statement[:50]}...")
                        else:
                            print(f"  ⚠️ Warning: {e}")
            
            conn.commit()
            print("  ✅ Database migration completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def seed_initial_data():
    """Seed dữ liệu ban đầu"""
    print("🌱 Seeding initial data...")
    
    try:
        # Run seed_symbols.py
        seed_script = os.path.join(os.path.dirname(__file__), 'seed_symbols.py')
        if os.path.exists(seed_script):
            import subprocess
            result = subprocess.run([sys.executable, seed_script], 
                                  capture_output=True, text=True, cwd=os.path.dirname(seed_script))
            if result.returncode == 0:
                print("  ✅ Symbols seeded successfully")
            else:
                print(f"  ⚠️ Seed symbols warning: {result.stderr}")
        else:
            print("  ℹ️ Seed script not found, skipping")
        
        # Run load_thresholds.py
        threshold_script = os.path.join(os.path.dirname(__file__), 'load_thresholds.py')
        if os.path.exists(threshold_script):
            result = subprocess.run([sys.executable, threshold_script], 
                                  capture_output=True, text=True, cwd=os.path.dirname(threshold_script))
            if result.returncode == 0:
                print("  ✅ Thresholds loaded successfully")
            else:
                print(f"  ⚠️ Load thresholds warning: {result.stderr}")
        else:
            print("  ℹ️ Threshold script not found, skipping")
        
        return True
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        return False

def verify_setup():
    """Kiểm tra setup đã hoàn thành"""
    print("🔍 Verifying setup...")
    
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check tables
            result = conn.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)).fetchone()
            
            table_count = result[0]
            print(f"  📊 Found {table_count} tables")
            
            # Check symbols
            result = conn.execute(text("SELECT COUNT(*) as count FROM symbols")).fetchone()
            symbol_count = result[0]
            print(f"  📈 Found {symbol_count} symbols")
            
            # Check timeframes
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM timeframes")).fetchone()
                timeframe_count = result[0]
                print(f"  ⏰ Found {timeframe_count} timeframes")
            except:
                print(f"  ℹ️ Timeframes table not found (optional)")
            
            # Check strategies
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM trade_strategies")).fetchone()
                strategy_count = result[0]
                print(f"  📊 Found {strategy_count} strategies")
            except:
                print(f"  ℹ️ Strategies table not found (optional)")
            
            # Check SMA tables
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM indicators_sma")).fetchone()
                sma_indicators_count = result[0]
                print(f"  📊 Found {sma_indicators_count} SMA indicators")
            except:
                print(f"  ⚠️ SMA indicators table not found")
            
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM sma_signals")).fetchone()
                sma_signals_count = result[0]
                print(f"  🎯 Found {sma_signals_count} SMA signals")
            except:
                print(f"  ⚠️ SMA signals table not found")
            
            # Check MACD tables
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM indicators_macd")).fetchone()
                macd_indicators_count = result[0]
                print(f"  📊 Found {macd_indicators_count} MACD indicators")
            except:
                print(f"  ℹ️ MACD indicators table not found (optional)")
            
            # Check views
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM symbol_thresholds_view")).fetchone()
                symbol_thresholds_view_count = result[0]
                print(f"  📊 Found {symbol_thresholds_view_count} symbol thresholds view records")
            except:
                print(f"  ⚠️ symbol_thresholds_view not found")
            
            try:
                result = conn.execute(text("SELECT COUNT(*) as count FROM market_threshold_templates_view")).fetchone()
                market_thresholds_view_count = result[0]
                print(f"  📊 Found {market_thresholds_view_count} market thresholds view records")
            except:
                print(f"  ⚠️ market_threshold_templates_view not found")
            
            print("  ✅ Setup verification completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Starting automatic database setup...")
    print("=" * 60)
    
    try:
        # 1. Wait for MySQL
        if not wait_for_mysql():
            sys.exit(1)
        
        # 2. Verify database exists
        if not verify_database_exists():
            sys.exit(1)
        
        # 3. Verify database user
        if not verify_database_user():
            sys.exit(1)
        
        # 4. Create tables
        if not create_tables_if_not_exists():
            sys.exit(1)
        
        # 5. Seed initial data
        if not seed_initial_data():
            sys.exit(1)
        
        # 6. Verify setup
        if not verify_setup():
            sys.exit(1)
        
        print("\n✅ Automatic database setup completed successfully!")
        print("💡 Your trading system is ready to use!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
