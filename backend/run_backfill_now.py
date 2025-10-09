#!/usr/bin/env python3
"""
Script đơn giản để chạy job_backfill_full_pipeline
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🚀 Running job_backfill_full_pipeline")
    print("Parameters: days=365, source='auto', strategy_id=1, tf_threshold_name='1D4hr'")
    print("=" * 80)
    
    try:
        # Import the function
        from worker.jobs import job_backfill_full_pipeline
        
        # Run the function
        result = job_backfill_full_pipeline(
            days=365, 
            source='auto', 
            strategy_id=1, 
            tf_threshold_name='1D4hr'
        )
        
        print(f"\n✅ Backfill completed! Result: {result}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()
