#!/usr/bin/env python3
"""
Check when MACD Multi-TF jobs run
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_macd_schedule():
    """Check when MACD Multi-TF jobs run"""
    print("🕐 MACD Multi-TF Job Schedule Analysis")
    print("=" * 60)
    
    try:
        from app.db import init_db, SessionLocal
        from sqlalchemy import text
        
        # Initialize database
        init_db(os.getenv("DATABASE_URL"))
        
        # Check active workflows with MACD Multi-TF nodes
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT id, name, status, nodes, properties
                FROM workflows 
                WHERE status = 'active'
                AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
            """)).fetchall()
            
            if result:
                print(f"✅ Found {len(result)} active MACD Multi-TF workflows:")
                for row in result:
                    print(f"   - ID: {row.id}, Name: {row.name}, Status: {row.status}")
                    
                    # Parse nodes to find MACD Multi-TF configuration
                    import json
                    nodes = json.loads(row.nodes)
                    properties = json.loads(row.properties)
                    
                    for node in nodes:
                        if node.get('type') == 'macd-multi':
                            node_id = node['id']
                            node_config = properties.get(node_id, {})
                            
                            print(f"     📊 MACD Multi-TF Node: {node_id}")
                            print(f"        Fast Period: {node_config.get('fastPeriod', 7)}")
                            print(f"        Slow Period: {node_config.get('slowPeriod', 113)}")
                            print(f"        Signal Period: {node_config.get('signalPeriod', 144)}")
                            
                            symbol_thresholds = node_config.get('symbolThresholds', [])
                            print(f"        Symbols: {len(symbol_thresholds)}")
                            for symbol_data in symbol_thresholds[:3]:  # Show first 3
                                symbol = symbol_data.get('symbol', '')
                                print(f"          - {symbol}")
                            if len(symbol_thresholds) > 3:
                                print(f"          ... and {len(symbol_thresholds) - 3} more")
            else:
                print("❌ No active MACD Multi-TF workflows found")
        
        # Check recent signals
        print(f"\n📊 Recent MACD Multi-TF Signals:")
        with SessionLocal() as session:
            result = session.execute(text("""
                SELECT s.id, s.symbol_id, s.signal_type, s.ts, sy.ticker
                FROM signals s
                JOIN symbols sy ON s.symbol_id = sy.id
                WHERE s.strategy_id = 1
                ORDER BY s.ts DESC
                LIMIT 5
            """)).fetchall()
            
            if result:
                for row in result:
                    print(f"   - {row.ticker}: {row.signal_type} at {row.ts}")
            else:
                print("   No recent signals found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def explain_schedule():
    """Explain when MACD Multi-TF jobs run"""
    print(f"\n🕐 When MACD Multi-TF Jobs Run:")
    print("=" * 60)
    
    print("📋 **Manual Execution (API):**")
    print("   1. Via Workflow Builder UI:")
    print("      - Create workflow with MACD Multi-TF node")
    print("      - Click 'Execute Workflow'")
    print("      - Choose mode: 'realtime' or 'backfill'")
    print("      - Job enqueued to 'priority' queue immediately")
    
    print("\n   2. Via API Endpoint:")
    print("      POST /api/workflow/execute/<workflow_id>")
    print("      Body: {'mode': 'realtime'|'backfill'}")
    print("      - Job enqueued to 'priority' queue immediately")
    
    print("\n   3. Via Test Endpoint:")
    print("      POST /api/workflow/test-macd-multi")
    print("      Body: {'mode': 'realtime'|'backfill', 'symbol': 'AAPL'}")
    print("      - Job enqueued to 'priority' queue immediately")
    
    print("\n📋 **Automatic Execution (Scheduler):**")
    print("   ❌ **MACD Multi-TF jobs do NOT run automatically**")
    print("   ❌ **Scheduler only checks for active workflows**")
    print("   ❌ **No automatic enqueueing in scheduler**")
    
    print("\n📋 **Scheduler Behavior:**")
    print("   1. **Every 60 seconds:**")
    print("      - Check for active MACD Multi-TF workflows")
    print("      - If active: Skip regular US worker jobs")
    print("      - If inactive: Run regular US worker jobs")
    
    print("\n   2. **Conflict Prevention:**")
    print("      - When MACD Multi-TF active: worker_us is paused")
    print("      - When MACD Multi-TF inactive: worker_us runs normally")
    
    print("\n📋 **Job Execution Flow:**")
    print("   1. **Manual Trigger** → API/UI")
    print("   2. **Job Enqueued** → priority queue")
    print("   3. **Worker Picks Up** → worker (main worker)")
    print("   4. **Job Executes** → MACD Multi-TF pipeline")
    print("   5. **Signals Generated** → Database + Telegram")
    
    print("\n📋 **Queue Management:**")
    print("   - **Queue:** priority")
    print("   - **Worker:** worker (main worker)")
    print("   - **Timeout:** 600s (realtime), 1800s (backfill)")
    print("   - **Function:** job_macd_multi_us_workflow_executor")

if __name__ == "__main__":
    print("🧪 MACD Multi-TF Schedule Check")
    print("=" * 60)
    
    # Check current status
    status_ok = check_macd_schedule()
    
    # Explain schedule
    explain_schedule()
    
    print("\n" + "=" * 60)
    if status_ok:
        print("✅ Schedule analysis completed!")
    else:
        print("❌ Schedule analysis failed!")
