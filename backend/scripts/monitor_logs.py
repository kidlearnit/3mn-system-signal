#!/usr/bin/env python3
"""
Script để monitor logs của trading system
"""

import os
import time
import subprocess
from datetime import datetime

def monitor_logs():
    """Monitor logs in real-time"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    
    print("🔍 TRADING SYSTEM LOG MONITOR")
    print("=" * 50)
    print(f"📁 Log directory: {log_dir}")
    print(f"⏰ Started at: {datetime.now()}")
    print("=" * 50)
    
    # Check if logs exist
    errors_log = os.path.join(log_dir, 'errors.log')
    system_log = os.path.join(log_dir, 'system.log')
    
    if not os.path.exists(errors_log):
        print("❌ errors.log not found")
        return
    
    if not os.path.exists(system_log):
        print("❌ system.log not found")
        return
    
    print("✅ Log files found")
    print("📊 Monitoring logs... (Press Ctrl+C to stop)")
    print("-" * 50)
    
    try:
        # Monitor errors.log
        with open(errors_log, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    print(f"🚨 ERROR: {line.strip()}")
                else:
                    time.sleep(1)
                    
    except KeyboardInterrupt:
        print("\n👋 Log monitoring stopped")
    except Exception as e:
        print(f"❌ Error monitoring logs: {e}")

def show_recent_errors():
    """Show recent errors"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    errors_log = os.path.join(log_dir, 'errors.log')
    
    if not os.path.exists(errors_log):
        print("❌ errors.log not found")
        return
    
    print("🚨 RECENT ERRORS")
    print("=" * 50)
    
    try:
        with open(errors_log, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-10:] if len(lines) > 10 else lines
            
            if not recent_lines:
                print("✅ No errors found")
                return
            
            for line in recent_lines:
                print(f"❌ {line.strip()}")
                
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

def show_system_status():
    """Show system status from logs"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    system_log = os.path.join(log_dir, 'system.log')
    
    if not os.path.exists(system_log):
        print("❌ system.log not found")
        return
    
    print("📊 SYSTEM STATUS")
    print("=" * 50)
    
    try:
        with open(system_log, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-20:] if len(lines) > 20 else lines
            
            if not recent_lines:
                print("ℹ️ No system logs found")
                return
            
            for line in recent_lines:
                print(f"ℹ️ {line.strip()}")
                
    except Exception as e:
        print(f"❌ Error reading system logs: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "errors":
            show_recent_errors()
        elif sys.argv[1] == "status":
            show_system_status()
        elif sys.argv[1] == "monitor":
            monitor_logs()
        else:
            print("Usage: python monitor_logs.py [errors|status|monitor]")
    else:
        print("🔍 TRADING SYSTEM LOG MONITOR")
        print("=" * 50)
        print("Usage:")
        print("  python monitor_logs.py errors   - Show recent errors")
        print("  python monitor_logs.py status   - Show system status")
        print("  python monitor_logs.py monitor  - Monitor logs in real-time")
        print("=" * 50)
        
        # Show recent errors by default
        show_recent_errors()
