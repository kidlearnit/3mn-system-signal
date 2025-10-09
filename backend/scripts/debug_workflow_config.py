#!/usr/bin/env python3
"""
Debug workflow configuration for MACD Multi-TF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_workflow_config():
    """Debug workflow configuration"""
    print("🔍 Debugging MACD Multi-TF Workflow Configuration")
    print("=" * 60)
    
    try:
        from app.db import init_db, SessionLocal
        from sqlalchemy import text
        import json
        
        # Initialize database
        database_url = os.getenv("DATABASE_URL", "mysql+pymysql://trading:trading123@mysql:3306/trading")
        init_db(database_url)
        
        # Wait a bit for initialization
        import time
        time.sleep(1)
        
        with SessionLocal() as session:
            # Get active workflows with MACD Multi-TF nodes
            result = session.execute(text("""
                SELECT id, name, nodes, properties
                FROM workflows 
                WHERE status = 'active'
                AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
            """)).fetchall()
            
            print(f"📋 Found {len(result)} active workflows with MACD Multi-TF nodes")
            
            for workflow_id, workflow_name, nodes_json, properties_json in result:
                print(f"\n🔍 Workflow: {workflow_name} (ID: {workflow_id})")
                
                # Parse nodes and properties
                nodes = json.loads(nodes_json)
                properties = json.loads(properties_json)
                
                print(f"   Nodes: {len(nodes)}")
                print(f"   Properties: {len(properties)}")
                
                # Find MACD Multi-TF nodes
                macd_multi_nodes = [node for node in nodes if node.get('type') == 'macd-multi']
                print(f"   MACD Multi-TF nodes: {len(macd_multi_nodes)}")
                
                for node in macd_multi_nodes:
                    node_id = node['id']
                    print(f"\n   📊 Node ID: {node_id}")
                    
                    # Get node configuration
                    node_config = properties.get(node_id, {})
                    print(f"   📋 Node config type: {type(node_config)}")
                    print(f"   📋 Node config keys: {list(node_config.keys()) if isinstance(node_config, dict) else 'Not a dict'}")
                    
                    # Check symbolThresholds
                    symbol_thresholds = node_config.get('symbolThresholds', [])
                    print(f"   📊 Symbol thresholds type: {type(symbol_thresholds)}")
                    print(f"   📊 Symbol thresholds count: {len(symbol_thresholds) if isinstance(symbol_thresholds, list) else 'Not a list'}")
                    
                    if isinstance(symbol_thresholds, list) and len(symbol_thresholds) > 0:
                        first_threshold = symbol_thresholds[0]
                        print(f"   📊 First threshold type: {type(first_threshold)}")
                        print(f"   📊 First threshold: {first_threshold}")
                        
                        if isinstance(first_threshold, dict):
                            print(f"   📊 First threshold keys: {list(first_threshold.keys())}")
                        else:
                            print(f"   ❌ First threshold is not a dict!")
                    
                    # Check other config fields
                    print(f"   📊 Fast period: {node_config.get('fastPeriod', 'Not set')}")
                    print(f"   📊 Slow period: {node_config.get('slowPeriod', 'Not set')}")
                    print(f"   📊 Signal period: {node_config.get('signalPeriod', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_workflow_config()
    
    if success:
        print("\n✅ Debug completed!")
    else:
        print("\n❌ Debug failed!")
