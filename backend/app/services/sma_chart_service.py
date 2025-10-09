#!/usr/bin/env python3
"""
SMA Chart Service - Tạo và gửi chart với SMA indicators
"""
import os
import tempfile
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timezone, timedelta
import requests
from typing import Dict, List, Optional
import numpy as np
from app.db import SessionLocal
from sqlalchemy import text

class SMAChartService:
    def __init__(self):
        self.tg_token = os.getenv('TG_TOKEN')
        self.tg_chat_id = os.getenv('TG_CHAT_ID')
        
        # SMA periods
        self.sma_periods = {
            'ma18': 18,
            'ma36': 36, 
            'ma48': 48,
            'ma144': 144
        }
    
    def is_configured(self) -> bool:
        """Kiểm tra xem Telegram đã được cấu hình chưa"""
        return bool(self.tg_token and self.tg_chat_id)
    
    def get_candles_data(self, symbol_id: int, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """Lấy dữ liệu candles từ database"""
        try:
            with SessionLocal() as s:
                query = text("""
                    SELECT ts, open, high, low, close, volume
                    FROM candles_tf 
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC 
                    LIMIT :limit
                """)
                
                result = s.execute(query, {
                    'symbol_id': symbol_id,
                    'timeframe': timeframe,
                    'limit': limit
                })
                
                data = result.fetchall()
                
                if not data:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(data, columns=['ts', 'open', 'high', 'low', 'close', 'volume'])
                df['ts'] = pd.to_datetime(df['ts'])
                df.set_index('ts', inplace=True)
                df.sort_index(inplace=True)
                
                return df
                
        except Exception as e:
            print(f"Error getting candles data: {e}")
            return pd.DataFrame()
    
    def get_sma_data(self, symbol_id: int, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """Lấy dữ liệu SMA indicators từ database"""
        try:
            with SessionLocal() as s:
                query = text("""
                    SELECT ts, m1 as ma18, m2 as ma36, m3 as ma48, ma144
                    FROM indicators_sma 
                    WHERE symbol_id = :symbol_id AND timeframe = :timeframe
                    ORDER BY ts DESC 
                    LIMIT :limit
                """)
                
                result = s.execute(query, {
                    'symbol_id': symbol_id,
                    'timeframe': timeframe,
                    'limit': limit
                })
                
                data = result.fetchall()
                
                if not data:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                df = pd.DataFrame(data, columns=['ts', 'ma18', 'ma36', 'ma48', 'ma144'])
                df['ts'] = pd.to_datetime(df['ts'])
                df.set_index('ts', inplace=True)
                df.sort_index(inplace=True)
                
                return df
                
        except Exception as e:
            print(f"Error getting SMA data: {e}")
            return pd.DataFrame()
    
    def create_sma_chart(self, symbol_id: int, ticker: str, timeframe: str, 
                        signal_type: str, signal_direction: str) -> Optional[str]:
        """Tạo SMA chart cho timeframe cụ thể"""
        try:
            # Lấy dữ liệu candles và SMA
            candles_df = self.get_candles_data(symbol_id, timeframe, 100)
            sma_df = self.get_sma_data(symbol_id, timeframe, 100)
            
            if candles_df.empty:
                print(f"No candles data for {ticker} {timeframe}")
                return None
            
            # Merge SMA data với candles
            if not sma_df.empty:
                candles_df = candles_df.join(sma_df, how='left')
            
            # Tạo temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Chuẩn bị data cho mplfinance
            plot_data = candles_df.copy()
            
            # Tạo additional plots cho SMA
            additional_plots = []
            
            # Thêm SMA lines
            if 'ma18' in plot_data.columns:
                additional_plots.append(
                    mpf.make_addplot(plot_data['ma18'], color='blue', width=1, alpha=0.7)
                )
            if 'ma36' in plot_data.columns:
                additional_plots.append(
                    mpf.make_addplot(plot_data['ma36'], color='orange', width=1, alpha=0.7)
                )
            if 'ma48' in plot_data.columns:
                additional_plots.append(
                    mpf.make_addplot(plot_data['ma48'], color='red', width=1, alpha=0.7)
                )
            if 'ma144' in plot_data.columns:
                additional_plots.append(
                    mpf.make_addplot(plot_data['ma144'], color='purple', width=2, alpha=0.8)
                )
            
            # Tạo style
            signal_color = 'green' if signal_direction == 'BUY' else 'red' if signal_direction == 'SELL' else 'gray'
            
            # Tạo chart
            fig, axes = mpf.plot(
                plot_data,
                type='candle',
                style='charles',
                addplot=additional_plots,
                volume=True,
                figsize=(12, 8),
                title=f'{ticker} - {timeframe.upper()} SMA Chart\nSignal: {signal_type.upper()} ({signal_direction})',
                ylabel='Price ($)',
                ylabel_lower='Volume',
                savefig=temp_path,
                returnfig=True
            )
            
            # Thêm legend
            axes[0].legend(['MA18', 'MA36', 'MA48', 'MA144'], loc='upper left')
            
            # Highlight signal area
            if not plot_data.empty:
                latest_price = plot_data['close'].iloc[-1]
                axes[0].axhline(y=latest_price, color=signal_color, linestyle='--', alpha=0.5, linewidth=2)
                axes[0].text(0.02, 0.98, f'Latest: ${latest_price:.2f}', 
                           transform=axes[0].transAxes, fontsize=10, 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor=signal_color, alpha=0.3))
            
            plt.tight_layout()
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating SMA chart: {e}")
            return None
    
    def send_chart_to_telegram(self, chart_path: str, caption: str = "") -> bool:
        """Gửi chart đến Telegram"""
        if not self.is_configured():
            print("Telegram not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.tg_token}/sendPhoto"
            
            with open(chart_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.tg_chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    print(f"Chart sent successfully to Telegram")
                    return True
                else:
                    print(f"Failed to send chart: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"Error sending chart to Telegram: {e}")
            return False
        finally:
            # Clean up temporary file
            try:
                os.unlink(chart_path)
            except:
                pass
    
    def send_sma_signal_with_chart(self, symbol_id: int, ticker: str, exchange: str, 
                                 timeframe: str, signal_data: Dict, is_test: bool = False) -> bool:
        """Gửi SMA signal kèm chart"""
        try:
            signal_type = signal_data.get('signal_type', 'neutral')
            signal_direction = signal_data.get('signal_direction', 'HOLD')
            
            # Tạo chart
            chart_path = self.create_sma_chart(symbol_id, ticker, timeframe, signal_type, signal_direction)
            
            if chart_path:
                # Tạo caption cho chart
                tf_category = self._get_timeframe_category(timeframe)
                market_source = "VN" if exchange in ("HOSE", "HNX", "UPCOM") else "US"
                market_flag = "🇻🇳" if market_source == "VN" else "🇺🇸"
                test_flag = "🧪 *[TEST MODE]*\n" if is_test else ""
                
                caption = f"""
📊 *{ticker} SMA Chart - {timeframe.upper()} ({tf_category})*
{market_flag} *{market_source} MARKET*
{test_flag}
🎯 *Signal:* {signal_type.upper()} ({signal_direction})
💰 *Price:* ${signal_data.get('close', 0):.2f}
📈 *MA18:* ${signal_data.get('m1', 0):.2f}
📊 *MA36:* ${signal_data.get('m2', 0):.2f}
📉 *MA48:* ${signal_data.get('m3', 0):.2f}
🎯 *MA144:* ${signal_data.get('ma144', 0):.2f}

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
🏢 *Exchange:* {exchange}
                """.strip()
                
                # Gửi chart
                success = self.send_chart_to_telegram(chart_path, caption)
                return success
            else:
                print(f"Failed to create chart for {ticker} {timeframe}")
                return False
                
        except Exception as e:
            print(f"Error sending SMA signal with chart: {e}")
            return False
    
    def _get_timeframe_category(self, timeframe: str) -> str:
        """Lấy category của timeframe"""
        if timeframe in ['1m', '2m', '5m'] or '1D1' in timeframe or '1D2' in timeframe or '1D5' in timeframe:
            return 'SHORT'
        elif timeframe in ['15m', '30m', '1h'] or '1D15Min' in timeframe or '1D30Min' in timeframe or '1D1hr' in timeframe:
            return 'CORE'
        elif timeframe in ['4h'] or '1D4hr' in timeframe:
            return 'LONG'
        else:
            return 'UNKNOWN'

# Global instance
sma_chart_service = SMAChartService()
