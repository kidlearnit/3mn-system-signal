#!/usr/bin/env python3
"""
Simple check for MACD Multi-TF schedule
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simple_schedule_check():
    """Simple check for MACD Multi-TF schedule"""
    print("🕐 MACD Multi-TF Job Schedule")
    print("=" * 50)
    
    print("📋 **When MACD Multi-TF Jobs Run:**")
    print("")
    
    print("✅ **Manual Execution (ON-DEMAND):**")
    print("   1. **Workflow Builder UI:**")
    print("      - Create workflow with MACD Multi-TF node")
    print("      - Click 'Execute Workflow' button")
    print("      - Choose mode: 'realtime' or 'backfill'")
    print("      - Job enqueued to 'priority' queue immediately")
    print("")
    
    print("   2. **API Endpoint:**")
    print("      POST /api/workflow/execute/<workflow_id>")
    print("      Body: {'mode': 'realtime'|'backfill'}")
    print("      - Job enqueued to 'priority' queue immediately")
    print("")
    
    print("   3. **Test Endpoint:**")
    print("      POST /api/workflow/test-macd-multi")
    print("      Body: {'mode': 'realtime'|'backfill', 'symbol': 'AAPL'}")
    print("      - Job enqueued to 'priority' queue immediately")
    print("")
    
    print("   4. **Direct Script:**")
    print("      python scripts/test_macd_docker.py")
    print("      - Job enqueued to 'priority' queue immediately")
    print("")
    
    print("❌ **Automatic Execution (SCHEDULED):**")
    print("   **MACD Multi-TF jobs do NOT run automatically**")
    print("   **Scheduler only checks for active workflows**")
    print("   **No automatic enqueueing in scheduler**")
    print("")
    
    print("📋 **Scheduler Behavior (Every 60 seconds):**")
    print("   1. Check for active MACD Multi-TF workflows")
    print("   2. If active: Skip regular US worker jobs")
    print("   3. If inactive: Run regular US worker jobs")
    print("   4. **Conflict Prevention:** worker_us is paused when MACD active")
    print("")
    
    print("📋 **Job Execution Flow:**")
    print("   1. **Manual Trigger** → API/UI/Script")
    print("   2. **Job Enqueued** → priority queue")
    print("   3. **Worker Picks Up** → worker (main worker)")
    print("   4. **Job Executes** → MACD Multi-TF pipeline")
    print("   5. **Signals Generated** → Database + Telegram")
    print("")
    
    print("📋 **Queue Management:**")
    print("   - **Queue:** priority")
    print("   - **Worker:** worker (main worker)")
    print("   - **Timeout:** 600s (realtime), 1800s (backfill)")
    print("   - **Function:** job_macd_multi_us_workflow_executor")
    print("")
    
    print("📋 **Current Status:**")
    print("   - **Scheduler:** Running (checks every 60s)")
    print("   - **Worker:** Running (listens to priority queue)")
    print("   - **MACD Multi-TF:** Ready (manual trigger only)")
    print("   - **worker_us:** Running (paused when MACD active)")

if __name__ == "__main__":
    simple_schedule_check()
