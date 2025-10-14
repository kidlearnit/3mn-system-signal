#!/usr/bin/env python3
"""
SMS Service - Gửi SMS thông báo khi có sự cố hệ thống
"""
import os
import requests
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SMSService:
    def __init__(self):
        """Khởi tạo SMS Service"""
        self.api_key = os.getenv('SMS_API_KEY')
        self.api_secret = os.getenv('SMS_API_SECRET')
        self.from_number = os.getenv('SMS_FROM_NUMBER', '+1234567890')
        self.to_numbers = os.getenv('SMS_TO_NUMBERS', '').split(',')
        
        # Email to SMS Gateway settings
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'gmail')  # gmail, outlook, yahoo
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_to_sms_gateways = self._get_email_to_sms_gateways()
        
        # Loại bỏ số trống
        self.to_numbers = [num.strip() for num in self.to_numbers if num.strip()]
        
        # SMS Provider URLs (có thể thay đổi theo nhà cung cấp)
        self.sms_provider = os.getenv('SMS_PROVIDER', 'email_gateway')  # twilio, vonage, email_gateway
        self.sms_url = self._get_sms_url()
        
        # Rate limiting
        self.last_sent = {}
        self.min_interval = 300  # 5 phút giữa các SMS cùng loại
        
        logger.info(f"SMS Service initialized with provider: {self.sms_provider}")
        logger.info(f"Configured to send to {len(self.to_numbers)} numbers")
    
    def _get_email_to_sms_gateways(self) -> dict:
        """Lấy danh sách Email to SMS gateways"""
        return {
            # US Carriers
            'verizon': '@vtext.com',
            'att': '@txt.att.net',
            'tmobile': '@tmomail.net',
            'sprint': '@messaging.sprintpcs.com',
            'virgin': '@vmobl.com',
            'boost': '@smsmyboostmobile.com',
            'cricket': '@sms.cricketwireless.net',
            'metropcs': '@mymetropcs.com',
            'us_cellular': '@email.uscc.net',
            
            # Canadian Carriers
            'rogers': '@pcs.rogers.com',
            'bell': '@txt.bell.ca',
            'telus': '@msg.telus.com',
            
            # International (có thể thêm nhiều hơn)
            'viettel': '@viettel.com.vn',
            'mobifone': '@mobifone.vn',
            'vinaphone': '@vinaphone.com.vn',
        }
    
    def _get_sms_url(self) -> str:
        """Lấy URL API dựa trên provider"""
        if self.sms_provider.lower() == 'twilio':
            return f"https://api.twilio.com/2010-04-01/Accounts/{self.api_key}/Messages.json"
        elif self.sms_provider.lower() == 'vonage':
            return "https://api.nexmo.com/v1/messages"
        elif self.sms_provider.lower() == 'email_gateway':
            return "smtp"  # Email gateway
        else:
            # Default fallback
            return "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json".format(self.api_key)
    
    def _is_rate_limited(self, message_type: str) -> bool:
        """Kiểm tra rate limiting"""
        now = datetime.now().timestamp()
        if message_type in self.last_sent:
            time_diff = now - self.last_sent[message_type]
            if time_diff < self.min_interval:
                logger.warning(f"SMS rate limited for {message_type}, {self.min_interval - time_diff:.0f}s remaining")
                return True
        return False
    
    def _send_twilio_sms(self, message: str) -> bool:
        """Gửi SMS qua Twilio"""
        try:
            for to_number in self.to_numbers:
                data = {
                    'From': self.from_number,
                    'To': to_number,
                    'Body': message
                }
                
                response = requests.post(
                    self.sms_url,
                    data=data,
                    auth=(self.api_key, self.api_secret),
                    timeout=30
                )
                
                if response.status_code == 201:
                    logger.info(f"SMS sent successfully to {to_number}")
                else:
                    logger.error(f"SMS failed to {to_number}: {response.status_code} - {response.text}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return False
    
    def _send_vonage_sms(self, message: str) -> bool:
        """Gửi SMS qua Vonage (Nexmo)"""
        try:
            for to_number in self.to_numbers:
                data = {
                    'from': self.from_number,
                    'to': to_number,
                    'text': message,
                    'api_key': self.api_key,
                    'api_secret': self.api_secret
                }
                
                response = requests.post(
                    self.sms_url,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('messages', [{}])[0].get('status') == '0':
                        logger.info(f"SMS sent successfully to {to_number}")
                    else:
                        logger.error(f"SMS failed to {to_number}: {result}")
                        return False
                else:
                    logger.error(f"SMS failed to {to_number}: {response.status_code} - {response.text}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Vonage SMS error: {e}")
            return False
    
    def _detect_carrier_from_number(self, phone_number: str) -> str:
        """Detect carrier từ phone number (simplified)"""
        # Đây là một implementation đơn giản
        # Trong thực tế, có thể cần database hoặc API để detect chính xác
        
        # Remove non-digits
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # US numbers
        if len(clean_number) == 11 and clean_number.startswith('1'):
            # Default to Verizon for US numbers (có thể thay đổi)
            return 'verizon'
        elif len(clean_number) == 10:
            # Assume US number without country code
            return 'verizon'
        else:
            # International - return default
            return 'verizon'
    
    def _send_email_to_sms(self, message: str) -> bool:
        """Gửi SMS qua Email to SMS Gateway (MIỄN PHÍ!)"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # SMTP settings based on email provider
            smtp_settings = {
                'gmail': {
                    'server': 'smtp.gmail.com',
                    'port': 587
                },
                'outlook': {
                    'server': 'smtp-mail.outlook.com',
                    'port': 587
                },
                'yahoo': {
                    'server': 'smtp.mail.yahoo.com',
                    'port': 587
                }
            }
            
            if self.email_provider not in smtp_settings:
                logger.error(f"Unsupported email provider: {self.email_provider}")
                return False
            
            smtp_config = smtp_settings[self.email_provider]
            
            # Create SMTP connection
            server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
            server.starttls()
            server.login(self.email_address, self.email_password)
            
            success_count = 0
            
            for phone_number in self.to_numbers:
                # Detect carrier and get email gateway
                carrier = self._detect_carrier_from_number(phone_number)
                gateway = self.email_to_sms_gateways.get(carrier)
                
                if not gateway:
                    logger.warning(f"No gateway found for carrier: {carrier}, using default")
                    gateway = '@vtext.com'  # Default to Verizon
                
                # Clean phone number (remove + and non-digits)
                clean_number = ''.join(filter(str.isdigit, phone_number))
                
                # Create email address for SMS
                if len(clean_number) == 11 and clean_number.startswith('1'):
                    # US number with country code
                    sms_email = clean_number[1:] + gateway
                elif len(clean_number) == 10:
                    # US number without country code
                    sms_email = clean_number + gateway
                else:
                    logger.warning(f"Unsupported phone number format: {phone_number}")
                    continue
                
                try:
                    # Create email message
                    msg = MIMEMultipart()
                    msg['From'] = self.email_address
                    msg['To'] = sms_email
                    msg['Subject'] = ""  # Empty subject for SMS
                    
                    # SMS message body
                    msg.attach(MIMEText(message, 'plain'))
                    
                    # Send email
                    server.send_message(msg)
                    logger.info(f"Email-to-SMS sent successfully to {phone_number} via {sms_email}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send email-to-SMS to {phone_number}: {e}")
                    continue
            
            server.quit()
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Email-to-SMS error: {e}")
            return False
    
    def send_sms(self, message: str, message_type: str = "general") -> bool:
        """Gửi SMS message"""
        # Check configuration based on provider
        if self.sms_provider.lower() == 'email_gateway':
            if not self.email_address or not self.email_password or not self.to_numbers:
                logger.warning("Email-to-SMS not configured - missing email credentials or phone numbers")
                return False
        else:
            if not self.api_key or not self.to_numbers:
                logger.warning("SMS not configured - missing API key or phone numbers")
                return False
        
        # Kiểm tra rate limiting
        if self._is_rate_limited(message_type):
            return False
        
        # Thêm timestamp và giới hạn độ dài
        timestamp = datetime.now().strftime('%H:%M:%S %d/%m/%Y')
        full_message = f"[{timestamp}] {message}"
        
        # Giới hạn độ dài SMS (160 ký tự)
        if len(full_message) > 160:
            full_message = full_message[:157] + "..."
        
        # Gửi SMS theo provider
        success = False
        if self.sms_provider.lower() == 'twilio':
            success = self._send_twilio_sms(full_message)
        elif self.sms_provider.lower() == 'vonage':
            success = self._send_vonage_sms(full_message)
        elif self.sms_provider.lower() == 'email_gateway':
            success = self._send_email_to_sms(full_message)
        else:
            logger.error(f"Unknown SMS provider: {self.sms_provider}")
            return False
        
        # Cập nhật rate limiting
        if success:
            self.last_sent[message_type] = datetime.now().timestamp()
        
        return success
    
    def send_yfinance_down_alert(self, symbol: str = "", error: str = "") -> bool:
        """Gửi alert khi yfinance connection down"""
        if error:
            message = f"🚨 YFINANCE DOWN - {symbol}\n❌ Error: {error}"
        else:
            message = f"🚨 YFINANCE DOWN - Cannot fetch data for {symbol}" if symbol else "🚨 YFINANCE DOWN - Connection failed"
        return self.send_sms(message, "yfinance_down")
    
    def send_yfinance_no_data_alert(self, symbol: str) -> bool:
        """Gửi alert khi yfinance không có dữ liệu"""
        message = f"⚠️ YAHOO FINANCE NO DATA - {symbol}\n📊 Không có dữ liệu trả về"
        return self.send_sms(message, "yfinance_no_data")
    
    def send_database_down_alert(self, error_detail: str = "") -> bool:
        """Gửi alert khi database connection down"""
        message = f"🚨 DATABASE DOWN - {error_detail}" if error_detail else "🚨 DATABASE DOWN - Connection failed"
        return self.send_sms(message, "database_down")
    
    def send_database_error_alert(self, error_detail: str, operation: str = "") -> bool:
        """Gửi alert khi có database error"""
        message = f"🚨 DB ERROR - {operation}: {error_detail}" if operation else f"🚨 DB ERROR - {error_detail}"
        return self.send_sms(message, "database_error")
    
    def send_collector_start_alert(self, collector_name: str) -> bool:
        """Gửi alert khi collector agent start"""
        message = f"✅ COLLECTOR STARTED - {collector_name}"
        return self.send_sms(message, "collector_start")
    
    def send_collector_stop_alert(self, collector_name: str) -> bool:
        """Gửi alert khi collector agent stop"""
        message = f"🛑 COLLECTOR STOPPED - {collector_name}"
        return self.send_sms(message, "collector_stop")
    
    def send_system_health_alert(self, status: str, details: str = "") -> bool:
        """Gửi alert về system health"""
        message = f"📊 SYSTEM HEALTH - {status}"
        if details:
            message += f" - {details}"
        return self.send_sms(message, "system_health")
    
    def send_test_alert(self, message="Test SMS from Trading Signals System"):
        """Send a test SMS alert"""
        if not self.email_address or not self.email_password or not self.phone_numbers:
            return "SMS not configured - missing email credentials or phone numbers"
        
        return self.send_sms(message, "test")
    
    def send_system_alert(self, message):
        """Send system alert SMS"""
        if not self.email_address or not self.email_password or not self.phone_numbers:
            print("⚠️ SMS not configured - missing email credentials or phone numbers")
            return "SMS not configured"
        
        return self.send_sms(message, "system_alert")
    
    def send_vnstock_down_alert(self, ticker: str, error: str) -> bool:
        """Gửi thông báo vnstock connection down"""
        message = f"🚨 VNSTOCK DOWN - {ticker}\n❌ Error: {error}"
        return self.send_sms(message, "vnstock_down")
    
    def send_vnstock_no_data_alert(self, ticker: str) -> bool:
        """Gửi thông báo vnstock không có dữ liệu"""
        message = f"⚠️ VNSTOCK NO DATA - {ticker}\n📊 Không có dữ liệu từ tất cả sources"
        return self.send_sms(message, "vnstock_no_data")
    
    def send_polygon_down_alert(self, ticker: str, error: str) -> bool:
        """Gửi thông báo Polygon API down"""
        message = f"🚨 POLYGON API DOWN - {ticker}\n❌ Error: {error}"
        return self.send_sms(message, "polygon_down")
    
    def send_polygon_no_data_alert(self, ticker: str, message_detail: str) -> bool:
        """Gửi thông báo Polygon không có dữ liệu"""
        message = f"⚠️ POLYGON NO DATA - {ticker}\n📊 Message: {message_detail}"
        return self.send_sms(message, "polygon_no_data")

# Global instance
sms_service = SMSService()

# Convenience functions
def send_yfinance_down_alert(symbol: str = "", error: str = "") -> bool:
    """Gửi alert khi yfinance down"""
    return sms_service.send_yfinance_down_alert(symbol, error)

def send_yfinance_no_data_alert(symbol: str) -> bool:
    """Gửi alert khi yfinance không có dữ liệu"""
    return sms_service.send_yfinance_no_data_alert(symbol)

def send_vnstock_down_alert(ticker: str, error: str) -> bool:
    """Gửi alert khi vnstock down"""
    return sms_service.send_vnstock_down_alert(ticker, error)

def send_vnstock_no_data_alert(ticker: str) -> bool:
    """Gửi alert khi vnstock không có dữ liệu"""
    return sms_service.send_vnstock_no_data_alert(ticker)

def send_polygon_down_alert(ticker: str, error: str) -> bool:
    """Gửi alert khi polygon down"""
    return sms_service.send_polygon_down_alert(ticker, error)

def send_polygon_no_data_alert(ticker: str, message_detail: str) -> bool:
    """Gửi alert khi polygon không có dữ liệu"""
    return sms_service.send_polygon_no_data_alert(ticker, message_detail)

def send_database_down_alert(error_detail: str = "") -> bool:
    """Gửi alert khi database down"""
    return sms_service.send_database_down_alert(error_detail)

def send_database_error_alert(error_detail: str, operation: str = "") -> bool:
    """Gửi alert khi có database error"""
    return sms_service.send_database_error_alert(error_detail, operation)

def send_collector_start_alert(collector_name: str) -> bool:
    """Gửi alert khi collector start"""
    return sms_service.send_collector_start_alert(collector_name)

def send_collector_stop_alert(collector_name: str) -> bool:
    """Gửi alert khi collector stop"""
    return sms_service.send_collector_stop_alert(collector_name)

def send_system_health_alert(status: str, details: str = "") -> bool:
    """Gửi alert về system health"""
    return sms_service.send_system_health_alert(status, details)

# Test function
def test_sms_service():
    """Test SMS service"""
    logger.info("Testing SMS Service...")
    
    # Test các loại alert
    test_results = {
        "yfinance_down": send_yfinance_down_alert("TQQQ", "Connection timeout"),
        "yfinance_no_data": send_yfinance_no_data_alert("AAPL"),
        "vnstock_down": send_vnstock_down_alert("VIC", "RetryError"),
        "vnstock_no_data": send_vnstock_no_data_alert("HPG"),
        "polygon_down": send_polygon_down_alert("TSLA", "HTTP 429"),
        "polygon_no_data": send_polygon_no_data_alert("NVDA", "No results"),
        "database_down": send_database_down_alert("Connection timeout"),
        "database_error": send_database_error_alert("Query failed", "SELECT"),
        "collector_start": send_collector_start_alert("US Worker"),
        "collector_stop": send_collector_stop_alert("VN Worker"),
        "system_health": send_system_health_alert("WARNING", "High memory usage")
    }
    
    logger.info("SMS Test Results:")
    for alert_type, result in test_results.items():
        status = "✅ SUCCESS" if result else "❌ FAILED"
        logger.info(f"  {alert_type}: {status}")
    
    return test_results

if __name__ == "__main__":
    # Test SMS service khi chạy trực tiếp
    test_sms_service()
