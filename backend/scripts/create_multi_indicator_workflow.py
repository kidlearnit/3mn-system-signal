#!/usr/bin/env python3
"""
Create Multi-Indicator Workflow Template
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append('/code')

from app.db import init_db, SessionLocal

# Initialize database
init_db(os.getenv("DATABASE_URL"))

def create_multi_indicator_workflow():
    """Create a sample multi-indicator workflow"""
    
    # Sample 25 symbols configuration
    symbols_config = [
        {'symbol': 'NVDA', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'MSFT', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'AAPL', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'GOOGL', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'AMZN', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'TSLA', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'META', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'NFLX', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'AMD', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'INTC', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'CRM', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'ORCL', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'ADBE', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'PYPL', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'UBER', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'SQ', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'ZM', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'SHOP', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'ROKU', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'PTON', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'PELOTON', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'DOCU', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'SNOW', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'PLTR', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07},
        {'symbol': 'COIN', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.47, 'bubefsm15': 0.22, 'bubefsm30': 0.47, 'bubefs_1h': 0.07}
    ]
    
    # Workflow structure
    workflow = {
        "id": "multi_indicator_workflow_001",
        "name": "Multi-Indicator 25 Symbols",
        "description": "Advanced multi-indicator analysis for 25 US stocks",
        "status": "active",
        "nodes": [
            {
                "id": "node_1",
                "type": "symbol",
                "x": 100,
                "y": 100,
                "properties": {
                    "symbols": symbols_config
                }
            },
            {
                "id": "node_2",
                "type": "macd-multi",
                "x": 300,
                "y": 100,
                "properties": {
                    "symbolThresholds": symbols_config,
                    "fastPeriod": 7,
                    "slowPeriod": 113,
                    "signalPeriod": 144
                }
            },
            {
                "id": "node_3",
                "type": "sma",
                "x": 500,
                "y": 100,
                "properties": {
                    "timeframes": ["1m", "2m", "5m", "15m", "30m", "1h", "4h"],
                    "periods": [5, 10, 20, 50, 100, 200, 144]
                }
            },
            {
                "id": "node_4",
                "type": "rsi",
                "x": 700,
                "y": 100,
                "properties": {
                    "timeframes": ["5m", "15m", "30m", "1h", "4h"],
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                }
            },
            {
                "id": "node_5",
                "type": "bollinger",
                "x": 900,
                "y": 100,
                "properties": {
                    "timeframes": ["15m", "30m", "1h", "4h"],
                    "period": 20,
                    "stdDev": 2
                }
            },
            {
                "id": "node_6",
                "type": "aggregation",
                "x": 1100,
                "y": 100,
                "properties": {
                    "method": "weighted_average",
                    "minStrategies": 3,
                    "consensusThreshold": 0.7,
                    "confidenceThreshold": 0.6,
                    "customWeights": {
                        "macd_multi": 0.3,
                        "sma": 0.25,
                        "rsi": 0.2,
                        "bollinger": 0.25
                    }
                }
            },
            {
                "id": "node_7",
                "type": "output",
                "x": 1300,
                "y": 100,
                "properties": {
                    "channels": ["database", "telegram"],
                    "format": "json",
                    "autoStart": True
                }
            }
        ],
        "connections": [
            {
                "from": {"nodeId": "node_1", "port": "output"},
                "to": {"nodeId": "node_2", "port": "input"}
            },
            {
                "from": {"nodeId": "node_1", "port": "output"},
                "to": {"nodeId": "node_3", "port": "input"}
            },
            {
                "from": {"nodeId": "node_1", "port": "output"},
                "to": {"nodeId": "node_4", "port": "input"}
            },
            {
                "from": {"nodeId": "node_1", "port": "output"},
                "to": {"nodeId": "node_5", "port": "input"}
            },
            {
                "from": {"nodeId": "node_2", "port": "output"},
                "to": {"nodeId": "node_6", "port": "input"}
            },
            {
                "from": {"nodeId": "node_3", "port": "output"},
                "to": {"nodeId": "node_6", "port": "input"}
            },
            {
                "from": {"nodeId": "node_4", "port": "output"},
                "to": {"nodeId": "node_6", "port": "input"}
            },
            {
                "from": {"nodeId": "node_5", "port": "output"},
                "to": {"nodeId": "node_6", "port": "input"}
            },
            {
                "from": {"nodeId": "node_6", "port": "output"},
                "to": {"nodeId": "node_7", "port": "input"}
            }
        ],
        "properties": {
            "node_1": {
                "symbols": symbols_config
            },
            "node_2": {
                "symbolThresholds": symbols_config,
                "fastPeriod": 7,
                "slowPeriod": 113,
                "signalPeriod": 144
            },
            "node_3": {
                "timeframes": ["1m", "2m", "5m", "15m", "30m", "1h", "4h"],
                "periods": [5, 10, 20, 50, 100, 200, 144]
            },
            "node_4": {
                "timeframes": ["5m", "15m", "30m", "1h", "4h"],
                "period": 14,
                "overbought": 70,
                "oversold": 30
            },
            "node_5": {
                "timeframes": ["15m", "30m", "1h", "4h"],
                "period": 20,
                "stdDev": 2
            },
            "node_6": {
                "method": "weighted_average",
                "minStrategies": 3,
                "consensusThreshold": 0.7,
                "confidenceThreshold": 0.6,
                "customWeights": {
                    "macd_multi": 0.3,
                    "sma": 0.25,
                    "rsi": 0.2,
                    "bollinger": 0.25
                }
            },
            "node_7": {
                "channels": ["database", "telegram"],
                "format": "json",
                "autoStart": True
            }
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    return workflow

def save_workflow_to_database(workflow):
    """Save workflow to database"""
    try:
        with SessionLocal() as session:
            from sqlalchemy import text
            
            # Insert workflow
            result = session.execute(text("""
                INSERT INTO workflows (id, name, description, status, nodes, connections, properties, created_at, updated_at)
                VALUES (:id, :name, :description, :status, :nodes, :connections, :properties, :created_at, :updated_at)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                description = VALUES(description),
                status = VALUES(status),
                nodes = VALUES(nodes),
                connections = VALUES(connections),
                properties = VALUES(properties),
                updated_at = VALUES(updated_at)
            """), {
                'id': workflow['id'],
                'name': workflow['name'],
                'description': workflow['description'],
                'status': workflow['status'],
                'nodes': json.dumps(workflow['nodes']),
                'connections': json.dumps(workflow['connections']),
                'properties': json.dumps(workflow['properties']),
                'created_at': workflow['created_at'],
                'updated_at': workflow['updated_at']
            })
            
            session.commit()
            print(f"✅ Workflow saved to database: {workflow['id']}")
            return True
            
    except Exception as e:
        print(f"❌ Error saving workflow to database: {e}")
        return False

def save_workflow_to_file(workflow, filename="multi_indicator_workflow.json"):
    """Save workflow to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ Workflow saved to file: {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving workflow to file: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Creating Multi-Indicator Workflow Template")
    print("=" * 50)
    
    # Create workflow
    workflow = create_multi_indicator_workflow()
    
    print(f"✅ Workflow created: {workflow['name']}")
    print(f"✅ Nodes: {len(workflow['nodes'])}")
    print(f"✅ Connections: {len(workflow['connections'])}")
    print(f"✅ Symbols: {len(workflow['properties']['node_1']['symbols'])}")
    
    # Save to file
    save_workflow_to_file(workflow)
    
    # Save to database (if available)
    try:
        save_workflow_to_database(workflow)
    except Exception as e:
        print(f"⚠️ Database save skipped: {e}")
    
    print("\n📋 Workflow Structure:")
    print("   📊 Symbol Node → 25 US stocks")
    print("   📈 MACD Multi-TF → 6 timeframes")
    print("   📉 SMA → 7 timeframes")
    print("   📊 RSI → 5 timeframes")
    print("   📈 Bollinger Bands → 4 timeframes")
    print("   🔄 Aggregation → Weighted average")
    print("   📤 Output → Database + Telegram")
    
    print("\n🎯 Aggregation Logic:")
    print("   • Min strategies: 3/4")
    print("   • Consensus threshold: 70%")
    print("   • Confidence threshold: 60%")
    print("   • Custom weights: MACD(30%), SMA(25%), RSI(20%), BB(25%)")
    
    print("\n✅ Multi-Indicator workflow template created successfully!")

if __name__ == "__main__":
    main()
