#!/usr/bin/env python3
"""
Test script to check how Vietnamese symbols are handled in MACD Multi-TF
"""

import os
import sys
sys.path.append('/code')

from app.db import init_db, SessionLocal
from sqlalchemy import text

def test_vn_symbols_handling():
    """Test how Vietnamese symbols are handled in MACD Multi-TF"""
    print("🧪 Testing Vietnamese Symbols Handling in MACD Multi-TF")
    print("=" * 60)
    
    try:
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Re-import SessionLocal after init_db
        from app.db import SessionLocal
        
        with SessionLocal() as session:
            # Check VN symbols in database
            print("📊 Vietnamese Symbols in Database:")
            print("-" * 40)
            
            vn_symbols = session.execute(text("""
                SELECT id, ticker, exchange, active
                FROM symbols 
                WHERE exchange IN ('HOSE', 'HNX', 'UPCOM')
                ORDER BY exchange, ticker
                LIMIT 10
            """)).fetchall()
            
            print(f"Found {len(vn_symbols)} VN symbols:")
            for symbol_id, ticker, exchange, active in vn_symbols:
                status = "✅ Active" if active else "❌ Inactive"
                print(f"  {ticker} ({exchange}): {status}")
            
            # Check US symbols for comparison
            print(f"\n📊 US Symbols in Database:")
            print("-" * 40)
            
            us_symbols = session.execute(text("""
                SELECT id, ticker, exchange, active
                FROM symbols 
                WHERE exchange IN ('NASDAQ', 'NYSE')
                ORDER BY exchange, ticker
                LIMIT 10
            """)).fetchall()
            
            print(f"Found {len(us_symbols)} US symbols:")
            for symbol_id, ticker, exchange, active in us_symbols:
                status = "✅ Active" if active else "❌ Inactive"
                print(f"  {ticker} ({exchange}): {status}")
            
            # Check current MACD Multi-TF workflow configuration
            print(f"\n🔧 Current MACD Multi-TF Workflow Configuration:")
            print("-" * 50)
            
            workflows = session.execute(text("""
                SELECT id, name, status, nodes
                FROM workflows 
                WHERE status = 'active'
                AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 3
            """)).fetchall()
            
            for workflow_id, name, status, nodes in workflows:
                print(f"Workflow: {name} (ID: {workflow_id[:8]}...)")
                print(f"Status: {status}")
                
                # Parse nodes to find MACD Multi-TF configuration
                import json
                try:
                    nodes_data = json.loads(nodes) if isinstance(nodes, str) else nodes
                    for node in nodes_data:
                        if node.get('type') == 'macd-multi':
                            properties = node.get('properties', {})
                            symbol_thresholds = properties.get('symbolThresholds', [])
                            
                            print(f"  MACD Multi-TF Node found:")
                            print(f"  - Symbol thresholds: {len(symbol_thresholds)} symbols")
                            
                            # Check if any VN symbols are in the configuration
                            vn_symbols_in_config = []
                            us_symbols_in_config = []
                            
                            for symbol_config in symbol_thresholds:
                                symbol = symbol_config.get('symbol', '')
                                if symbol:
                                    # Check if this symbol exists in VN exchanges
                                    vn_check = session.execute(text("""
                                        SELECT exchange FROM symbols 
                                        WHERE ticker = :ticker AND exchange IN ('HOSE', 'HNX', 'UPCOM')
                                        LIMIT 1
                                    """), {'ticker': symbol}).fetchone()
                                    
                                    if vn_check:
                                        vn_symbols_in_config.append(symbol)
                                    else:
                                        us_symbols_in_config.append(symbol)
                            
                            print(f"  - VN symbols in config: {len(vn_symbols_in_config)}")
                            if vn_symbols_in_config:
                                print(f"    {vn_symbols_in_config[:5]}{'...' if len(vn_symbols_in_config) > 5 else ''}")
                            
                            print(f"  - US symbols in config: {len(us_symbols_in_config)}")
                            if us_symbols_in_config:
                                print(f"    {us_symbols_in_config[:5]}{'...' if len(us_symbols_in_config) > 5 else ''}")
                            
                            break
                except Exception as e:
                    print(f"  Error parsing workflow nodes: {e}")
                
                print()
            
            # Check current MACD Multi-TF job implementation
            print(f"🔍 Current MACD Multi-TF Implementation Analysis:")
            print("-" * 50)
            print("❌ ISSUE FOUND:")
            print("  - MACD Multi-TF job (macd_multi_us_jobs.py) is HARDCODED for US symbols only")
            print("  - Line 87: exchange = 'NASDAQ' (hardcoded)")
            print("  - Line 97: exchange = 'NASDAQ' (hardcoded)")
            print("  - Line 101: exchange = 'NASDAQ' (hardcoded)")
            print("  - Line 106: exchange = 'NASDAQ' (hardcoded)")
            print()
            print("✅ SOLUTION NEEDED:")
            print("  1. Modify MACD Multi-TF to detect symbol exchange automatically")
            print("  2. Use appropriate data source (vnstock for VN, yfinance for US)")
            print("  3. Handle different market hours and timezones")
            print("  4. Support both VN and US symbols in same workflow")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vn_symbols_handling()
