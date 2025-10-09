"""
System Monitoring Service
Tích hợp SMS alerts cho system monitoring
"""

import os
import time
import threading
import subprocess
from datetime import datetime
from typing import Dict, List
from app.services.sms_service import SMSService
from app.db import SessionLocal
from sqlalchemy import text
import redis

class SystemMonitor:
    def __init__(self):
        self.sms_service = SMSService()
        self.running = False
        self.monitor_thread = None
        self.check_interval = 300  # 5 minutes
        self.last_alert_times = {}  # Prevent spam alerts
        
    def start_monitoring(self):
        """Start system monitoring in background thread"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🔍 System monitoring started")
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("🛑 System monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_system_health()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
                
    def _check_system_health(self):
        """Check various system components"""
        checks = {
            'database': self._check_database,
            'redis': self._check_redis,
            'docker_services': self._check_docker_services,
            'disk_space': self._check_disk_space,
            'memory_usage': self._check_memory_usage
        }
        
        alerts = []
        
        for check_name, check_func in checks.items():
            try:
                status = check_func()
                if not status['healthy']:
                    alerts.append({
                        'component': check_name,
                        'status': status['status'],
                        'message': status.get('message', 'Unknown error')
                    })
            except Exception as e:
                alerts.append({
                    'component': check_name,
                    'status': 'error',
                    'message': str(e)
                })
        
        # Send alerts if any issues found
        if alerts:
            self._send_system_alerts(alerts)
            
    def _check_database(self) -> Dict:
        """Check database connection"""
        try:
            with SessionLocal() as s:
                s.execute(text("SELECT 1"))
            return {'healthy': True, 'status': 'connected'}
        except Exception as e:
            return {'healthy': False, 'status': 'disconnected', 'message': str(e)}
            
    def _check_redis(self) -> Dict:
        """Check Redis connection"""
        try:
            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            return {'healthy': True, 'status': 'connected'}
        except Exception as e:
            return {'healthy': False, 'status': 'disconnected', 'message': str(e)}
            
    def _check_docker_services(self) -> Dict:
        """Check Docker services status"""
        try:
            # Check key services
            services = ['mysql', 'redis', 'web', 'worker', 'scheduler']
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}} {{.Status}}'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return {'healthy': False, 'status': 'docker_error', 'message': result.stderr}
                
            running_services = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    name, status = line.split(' ', 1)
                    running_services.append(name)
                    
            missing_services = [s for s in services if s not in running_services]
            
            if missing_services:
                return {
                    'healthy': False, 
                    'status': 'services_down', 
                    'message': f"Services down: {', '.join(missing_services)}"
                }
                
            return {'healthy': True, 'status': 'all_running'}
            
        except Exception as e:
            return {'healthy': False, 'status': 'check_error', 'message': str(e)}
            
    def _check_disk_space(self) -> Dict:
        """Check disk space"""
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {'healthy': True, 'status': 'unknown'}  # Skip if can't check
                
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {'healthy': True, 'status': 'unknown'}
                
            # Parse df output
            parts = lines[1].split()
            if len(parts) >= 5:
                usage = parts[4].replace('%', '')
                try:
                    usage_pct = float(usage)
                    if usage_pct > 90:
                        return {
                            'healthy': False, 
                            'status': 'critical', 
                            'message': f"Disk usage: {usage_pct}%"
                        }
                    elif usage_pct > 80:
                        return {
                            'healthy': False, 
                            'status': 'warning', 
                            'message': f"Disk usage: {usage_pct}%"
                        }
                except ValueError:
                    pass
                    
            return {'healthy': True, 'status': 'ok'}
            
        except Exception as e:
            return {'healthy': True, 'status': 'unknown'}  # Skip if can't check
            
    def _check_memory_usage(self) -> Dict:
        """Check memory usage"""
        try:
            result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {'healthy': True, 'status': 'unknown'}
                
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {'healthy': True, 'status': 'unknown'}
                
            # Parse memory info
            mem_line = lines[1].split()
            if len(mem_line) >= 7:
                total = int(mem_line[1])
                used = int(mem_line[2])
                available = int(mem_line[6])
                
                usage_pct = (used / total) * 100
                
                if usage_pct > 95:
                    return {
                        'healthy': False, 
                        'status': 'critical', 
                        'message': f"Memory usage: {usage_pct:.1f}%"
                    }
                elif usage_pct > 85:
                    return {
                        'healthy': False, 
                        'status': 'warning', 
                        'message': f"Memory usage: {usage_pct:.1f}%"
                    }
                    
            return {'healthy': True, 'status': 'ok'}
            
        except Exception as e:
            return {'healthy': True, 'status': 'unknown'}  # Skip if can't check
            
    def _send_system_alerts(self, alerts: List[Dict]):
        """Send SMS alerts for system issues"""
        try:
            # Prevent spam - only send alerts every 30 minutes for same issue
            current_time = datetime.now()
            alert_key = ','.join([f"{a['component']}:{a['status']}" for a in alerts])
            
            if alert_key in self.last_alert_times:
                time_since_last = (current_time - self.last_alert_times[alert_key]).total_seconds()
                if time_since_last < 1800:  # 30 minutes
                    return
                    
            self.last_alert_times[alert_key] = current_time
            
            # Create alert message
            message = "🚨 SYSTEM ALERT - Trading Signals\n\n"
            message += f"⏰ Time: {current_time.strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            
            for alert in alerts:
                status_icon = "🔴" if alert['status'] == 'critical' else "⚠️"
                message += f"{status_icon} {alert['component'].upper()}: {alert['status']}\n"
                message += f"   📝 {alert['message']}\n\n"
                
            message += "🔧 Please check system immediately!"
            
            # Send SMS
            self.sms_service.send_system_alert(message)
            print(f"📱 System alert sent: {alert_key}")
            
        except Exception as e:
            print(f"❌ Failed to send system alert: {e}")

# Global monitor instance
system_monitor = SystemMonitor()
