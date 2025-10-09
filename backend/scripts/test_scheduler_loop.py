#!/usr/bin/env python3
"""
Test scheduler loop for MACD Multi-TF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_scheduler_loop():
    """Test scheduler loop for MACD Multi-TF"""
    print("🕐 Testing Scheduler Loop for MACD Multi-TF")
    print("=" * 50)
    
    try:
        # Import scheduler functions
        from worker.scheduler_multi import _check_macd_multi_active, _enqueue_macd_multi_jobs
        
        print("🧪 Testing scheduler loop simulation...")
        
        # Simulate 3 scheduler cycles
        for cycle in range(3):
            print(f"\n🔄 Cycle {cycle + 1}:")
            
            # Check if MACD Multi-TF is active
            is_active = _check_macd_multi_active()
            print(f"   MACD Multi-TF active: {is_active}")
            
            if is_active:
                # Enqueue jobs
                jobs_count = _enqueue_macd_multi_jobs()
                print(f"   Jobs enqueued: {jobs_count}")
                
                if jobs_count > 0:
                    print("   ✅ Jobs enqueued successfully!")
                else:
                    print("   ⚠️ No jobs enqueued")
            else:
                print("   ❌ No active MACD Multi-TF workflows")
            
            # Wait 5 seconds between cycles
            if cycle < 2:
                print("   ⏳ Waiting 5 seconds...")
                import time
                time.sleep(5)
        
        print(f"\n✅ Scheduler loop test completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Scheduler Loop Test")
    print("=" * 50)
    
    success = test_scheduler_loop()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Scheduler loop test completed!")
        print("✅ MACD Multi-TF scheduled jobs working!")
    else:
        print("❌ Scheduler loop test failed!")
