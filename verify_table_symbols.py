#!/usr/bin/env python3
"""
Verify that the 25 symbols from the table are correctly inserted
"""

import pymysql
import sys

# Expected symbols from the table (in order of weight)
EXPECTED_SYMBOLS = [
    ('NVDA', 'NVIDIA Corporation', 10.08, 'Technology'),
    ('MSFT', 'Microsoft Corporation', 8.98, 'Technology'),
    ('AAPL', 'Apple Inc.', 7.33, 'Technology'),
    ('AMZN', 'Amazon.com, Inc.', 5.43, 'Consumer Discretionary'),
    ('AVGO', 'Broadcom Inc.', 5.40, 'Technology'),
    ('META', 'Meta Platforms, Inc.', 3.86, 'Communication Services'),
    ('NFLX', 'Netflix, Inc.', 2.84, 'Communication Services'),
    ('TSLA', 'Tesla, Inc.', 2.68, 'Consumer Discretionary'),
    ('GOOGL', 'Alphabet Inc. (Class A)', 2.63, 'Communication Services'),
    ('GOOG', 'Alphabet Inc. (Class C)', 2.47, 'Communication Services'),
    ('COST', 'Costco Wholesale Corporation', 2.43, 'Consumer Staples'),
    ('PLTR', 'Palantir Technologies Inc.', 2.30, 'Technology'),
    ('CSCO', 'Cisco Systems, Inc.', 1.55, 'Technology'),
    ('TMUS', 'T-Mobile US, Inc.', 1.54, 'Communication Services'),
    ('AMD', 'Advanced Micro Devices, Inc.', 1.50, 'Technology'),
    ('LIN', 'Linde plc', 1.26, 'Industrials'),
    ('INTU', 'Intuit Inc.', 1.23, 'Technology'),
    ('PEP', 'PepsiCo, Inc.', 1.09, 'Consumer Staples'),
    ('SHOP', 'Shopify Inc.', 1.07, 'Technology'),
    ('BKNG', 'Booking Holdings Inc.', 1.02, 'Consumer Discretionary'),
    ('ISRG', 'Intuitive Surgical, Inc.', 0.96, 'Healthcare'),
    ('TXN', 'Texas Instruments', 0.96, 'Technology'),
    ('QCOM', 'QUALCOMM Incorporated', 0.91, 'Technology'),
    ('AMGN', 'Amgen Inc.', 0.87, 'Healthcare'),
    ('ADBE', 'Adobe Inc.', 0.83, 'Technology'),
    ('TQQQ', 'QQQ Triple Index', None, 'QQQ triple long')
]

def test_database_connection():
    """Test database connection."""
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3309,
            user='trader',
            password='traderpass',
            database='trading',
            charset='utf8mb4'
        )
        return connection
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def verify_symbols(connection):
    """Verify symbols against expected data."""
    print("🔍 Verifying symbols against table data...")
    
    with connection.cursor() as cursor:
        # Get all symbols from database
        cursor.execute("""
            SELECT ticker, company_name, weight, sector, exchange, active
            FROM symbols 
            WHERE active = 1
            ORDER BY weight DESC, ticker
        """)
        db_symbols = cursor.fetchall()
        
        print(f"📊 Database has {len(db_symbols)} active symbols")
        print(f"📋 Expected {len(EXPECTED_SYMBOLS)} symbols")
        
        # Create lookup dictionary for expected symbols
        expected_dict = {symbol[0]: symbol for symbol in EXPECTED_SYMBOLS}
        db_dict = {symbol[0]: symbol for symbol in db_symbols}
        
        # Check for missing symbols
        missing_symbols = []
        for ticker, company, weight, sector in EXPECTED_SYMBOLS:
            if ticker not in db_dict:
                missing_symbols.append((ticker, company))
        
        if missing_symbols:
            print(f"\n❌ Missing symbols ({len(missing_symbols)}):")
            for ticker, company in missing_symbols:
                print(f"   {ticker} - {company}")
        else:
            print("✅ All expected symbols found in database")
        
        # Check for extra symbols
        extra_symbols = []
        for ticker in db_dict:
            if ticker not in expected_dict:
                extra_symbols.append(ticker)
        
        if extra_symbols:
            print(f"\n⚠️  Extra symbols in database ({len(extra_symbols)}):")
            for ticker in extra_symbols:
                print(f"   {ticker}")
        
        # Verify symbol details
        print(f"\n🔍 Verifying symbol details...")
        mismatches = []
        
        for ticker, company, weight, sector in EXPECTED_SYMBOLS:
            if ticker in db_dict:
                db_ticker, db_company, db_weight, db_sector, db_exchange, db_active = db_dict[ticker]
                
                # Check company name
                if db_company != company:
                    mismatches.append(f"{ticker}: Company name mismatch - DB: '{db_company}' vs Expected: '{company}'")
                
                # Check weight (handle None values)
                if weight is None and db_weight is not None:
                    mismatches.append(f"{ticker}: Weight mismatch - DB: {db_weight} vs Expected: None")
                elif weight is not None and db_weight is None:
                    mismatches.append(f"{ticker}: Weight mismatch - DB: None vs Expected: {weight}")
                elif weight is not None and db_weight is not None and abs(float(db_weight) - float(weight)) > 0.01:
                    mismatches.append(f"{ticker}: Weight mismatch - DB: {db_weight} vs Expected: {weight}")
                
                # Check sector
                if db_sector != sector:
                    mismatches.append(f"{ticker}: Sector mismatch - DB: '{db_sector}' vs Expected: '{sector}'")
        
        if mismatches:
            print(f"\n❌ Found {len(mismatches)} mismatches:")
            for mismatch in mismatches:
                print(f"   {mismatch}")
        else:
            print("✅ All symbol details match expected data")
        
        # Show summary by sector
        print(f"\n📊 Summary by Sector:")
        cursor.execute("""
            SELECT sector, COUNT(*) as count, ROUND(SUM(weight), 2) as total_weight
            FROM symbols 
            WHERE active = 1 AND weight IS NOT NULL
            GROUP BY sector
            ORDER BY total_weight DESC
        """)
        sectors = cursor.fetchall()
        
        for sector, count, total_weight in sectors:
            print(f"   {sector}: {count} symbols, {total_weight}% total weight")
        
        # Show top 10 by weight
        print(f"\n🏆 Top 10 by Weight:")
        cursor.execute("""
            SELECT ticker, company_name, weight, sector
            FROM symbols 
            WHERE active = 1 AND weight IS NOT NULL
            ORDER BY weight DESC
            LIMIT 10
        """)
        top_symbols = cursor.fetchall()
        
        for i, (ticker, company, weight, sector) in enumerate(top_symbols, 1):
            print(f"   {i:2d}. {ticker} ({weight}%) - {company}")

def main():
    """Main function."""
    print("🚀 Verifying Table Symbols")
    print("=" * 50)
    
    connection = test_database_connection()
    if not connection:
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    try:
        verify_symbols(connection)
        
        print(f"\n" + "=" * 50)
        print("📋 Verification Summary:")
        print("✅ Database connection successful")
        print("✅ Symbols verification completed")
        print("\n💡 If there are mismatches, run the updated SQL script:")
        print("   mysql-init/06-insert-table-symbols.sql")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
    finally:
        connection.close()

if __name__ == '__main__':
    main()
