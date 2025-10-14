#!/usr/bin/env python3
"""
Enhanced Email Digest - Professional Trading Signals
Provides comprehensive analysis with risk management and portfolio insights
"""

import os
import time
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text

import app.db as db
from app.services.email_service import email_service
from app.services.enhanced_signal_engine import enhanced_signal_engine, EnhancedSignalType
from app.services.portfolio_manager import portfolio_manager
from worker.sma_jobs import job_sma_pipeline
from utils.market_time import is_market_open

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedEmailDigest:
    """Professional email digest with comprehensive analysis"""
    
    def __init__(self):
        self.symbols_limit = int(os.getenv("EMAIL_DIGEST_LIMIT", "25"))
        self.timeframes = [tf.strip() for tf in os.getenv("EMAIL_DIGEST_TIMEFRAMES", "1m,2m,5m,15m").split(",") if tf.strip()]
        
    def get_symbols_to_monitor(self) -> List[Tuple[int, str, str]]:
        """Get symbols to monitor with market status check"""
        symbols_env = os.getenv("EMAIL_DIGEST_SYMBOLS", "").strip()
        
        with db.SessionLocal() as s:
            if symbols_env:
                tickers = [t.strip() for t in symbols_env.split(",") if t.strip()]
                if not tickers:
                    return []
                
                rows: List[Tuple[int, str, str]] = []
                for t in tickers:
                    row = s.execute(text(
                        "SELECT id, ticker, exchange FROM symbols WHERE ticker = :t AND active=1 LIMIT 1"
                    ), {"t": t}).fetchone()
                    if row:
                        rows.append((row[0], row[1], row[2]))
                return rows[:self.symbols_limit]
            
            # Fallback: top active symbols
            rows = s.execute(text(
                "SELECT id, ticker, exchange FROM symbols WHERE active=1 ORDER BY id LIMIT :lim"
            ), {"lim": self.symbols_limit}).fetchall()
            return [(sid, tck, ex) for sid, tck, ex in rows]
    
    def get_enhanced_signal_data(self, symbol_id: int, timeframes: List[str]) -> Dict[str, Any]:
        """Get enhanced signal data with quality analysis"""
        
        with db.SessionLocal() as s:
            # Get latest candles
            candles_query = text("""
                SELECT ts, open, high, low, close, volume
                FROM candles_1m 
                WHERE symbol_id = :symbol_id 
                ORDER BY ts DESC 
                LIMIT 200
            """)
            
            candles_df = pd.read_sql(candles_query, s.bind, params={"symbol_id": symbol_id})
            
            if candles_df.empty:
                return {}
            
            # Get latest SMA indicators
            sma_query = text("""
                SELECT timeframe, m1, m2, m3, ma144, close as cp
                FROM indicators_sma 
                WHERE symbol_id = :symbol_id 
                AND timeframe IN :timeframes
                ORDER BY ts DESC 
                LIMIT 1
            """)
            
            sma_data = s.execute(sma_query, {
                "symbol_id": symbol_id,
                "timeframes": tuple(timeframes)
            }).fetchall()
            
            if not sma_data:
                return {}
            
            # Get volume data
            volume_query = text("""
                SELECT AVG(volume) as avg_volume, MAX(volume) as max_volume
                FROM candles_1m 
                WHERE symbol_id = :symbol_id 
                AND ts >= :start_date
            """)
            
            start_date = datetime.now() - timedelta(days=30)
            volume_data = s.execute(volume_query, {
                "symbol_id": symbol_id,
                "start_date": start_date
            }).fetchone()
            
            # Prepare data for enhanced analysis
            ma_structure = {
                'cp': sma_data[0][5],  # close price
                'm1': sma_data[0][1],  # m1
                'm2': sma_data[0][2],  # m2
                'm3': sma_data[0][3],  # m3
                'ma144': sma_data[0][4]  # ma144
            }
            
            volume_info = {
                'current': candles_df.iloc[0]['volume'] if not candles_df.empty else 0,
                'average': volume_data[0] if volume_data else 0,
                'max': volume_data[1] if volume_data else 0
            }
            
            # Generate enhanced signal
            enhanced_signal = enhanced_signal_engine.generate_enhanced_signal(
                candles_df, ma_structure, volume_info
            )
            
            return {
                'ma_structure': ma_structure,
                'volume_info': volume_info,
                'enhanced_signal': enhanced_signal,
                'candles_count': len(candles_df)
            }
    
    def build_enhanced_html_table(self, signals_data: List[Dict[str, Any]]) -> str:
        """Build enhanced HTML table with professional analysis"""
        
        if not signals_data:
            return "<p>No signals available at this time.</p>"
        
        # Sort by confidence score
        signals_data.sort(key=lambda x: x.get('enhanced_signal', {}).get('confidence_score', 0), reverse=True)
        
        html = """
        <style>
            .enhanced-table {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .enhanced-table th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 8px;
                text-align: center;
                font-weight: 600;
                font-size: 12px;
            }
            .enhanced-table td {
                padding: 10px 8px;
                text-align: center;
                border-bottom: 1px solid #ddd;
                font-size: 11px;
            }
            .enhanced-table tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            .enhanced-table tr:hover {
                background-color: #e3f2fd;
            }
            .signal-strong-buy { background-color: #d4edda !important; color: #155724; }
            .signal-buy { background-color: #cce5ff !important; color: #004085; }
            .signal-weak-buy { background-color: #fff3cd !important; color: #856404; }
            .signal-hold { background-color: #f8f9fa !important; color: #6c757d; }
            .signal-weak-sell { background-color: #fff3cd !important; color: #856404; }
            .signal-sell { background-color: #f8d7da !important; color: #721c24; }
            .signal-strong-sell { background-color: #f5c6cb !important; color: #721c24; }
            .confidence-high { color: #28a745; font-weight: bold; }
            .confidence-medium { color: #ffc107; font-weight: bold; }
            .confidence-low { color: #dc3545; font-weight: bold; }
            .risk-low { color: #28a745; }
            .risk-medium { color: #ffc107; }
            .risk-high { color: #dc3545; }
            .summary-box {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .metric-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }
            .metric-label {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
            }
        </style>
        """
        
        # Summary section
        total_signals = len(signals_data)
        strong_signals = len([s for s in signals_data if s.get('enhanced_signal', {}).get('signal_type', '').startswith('strong_')])
        high_confidence = len([s for s in signals_data if s.get('enhanced_signal', {}).get('confidence_score', 0) >= 0.7])
        
        html += f"""
        <div class="summary-box">
            <h2>📊 Professional Trading Signals Summary</h2>
            <p><strong>{total_signals}</strong> Total Signals | <strong>{strong_signals}</strong> Strong Signals | <strong>{high_confidence}</strong> High Confidence</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
        
        # Portfolio metrics (if available)
        try:
            portfolio_metrics = portfolio_manager.get_portfolio_metrics()
            html += f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{portfolio_metrics.total_pnl_pct:.2f}%</div>
                    <div class="metric-label">Total P&L</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{portfolio_metrics.win_rate:.1f}%</div>
                    <div class="metric-label">Win Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{portfolio_metrics.sharpe_ratio:.2f}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{portfolio_metrics.open_positions}</div>
                    <div class="metric-label">Open Positions</div>
                </div>
            </div>
            """
        except Exception as e:
            logger.warning(f"Could not get portfolio metrics: {e}")
        
        # Signals table
        html += """
        <table class="enhanced-table">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Exchange</th>
                    <th>Signal</th>
                    <th>Confidence</th>
                    <th>Risk Level</th>
                    <th>Stop Loss</th>
                    <th>Take Profit</th>
                    <th>Position Size</th>
                    <th>R/R Ratio</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for signal_data in signals_data:
            symbol = signal_data['symbol']
            exchange = signal_data['exchange']
            enhanced_signal = signal_data.get('enhanced_signal', {})
            
            # Determine currency based on symbol
            is_vn_stock = symbol.endswith(('VN', 'VNM', 'VCB', 'VIC', 'VHM', 'VJC', 'VRE', 'VPI', 'VPB', 'VSH', 'VTO', 'VHC', 'VND', 'VOS', 'VSC', 'VSI', 'VTB', 'VTV', 'VWS', 'VXF', 'VYS', 'VZB', 'VZC', 'VZD', 'VZE', 'VZF', 'VZG', 'VZH', 'VZI', 'TPB', 'VGC'))
            if is_vn_stock:
                currency = "₫"
                currency_multiplier = 1000  # Convert to VND (multiply by 1000)
            else:
                currency = "$"
                currency_multiplier = 1
            
            if not enhanced_signal:
                continue
            
            signal_type = enhanced_signal.get('signal_type', 'hold')
            confidence = enhanced_signal.get('confidence_score', 0)
            risk_metrics = enhanced_signal.get('risk_metrics', {})
            recommendation = enhanced_signal.get('recommendation', {})
            
            # Signal styling
            signal_class = f"signal-{signal_type.replace('_', '-')}"
            
            # Confidence styling
            if confidence >= 0.7:
                confidence_class = "confidence-high"
                confidence_text = "HIGH"
            elif confidence >= 0.5:
                confidence_class = "confidence-medium"
                confidence_text = "MED"
            else:
                confidence_class = "confidence-low"
                confidence_text = "LOW"
            
            # Risk styling
            risk_score = enhanced_signal.get('risk_score', 0)
            if risk_score <= 0.3:
                risk_class = "risk-low"
                risk_text = "LOW"
            elif risk_score <= 0.6:
                risk_class = "risk-medium"
                risk_text = "MED"
            else:
                risk_class = "risk-high"
                risk_text = "HIGH"
            
            # Format values
            stop_loss = risk_metrics.stop_loss if hasattr(risk_metrics, 'stop_loss') else 0
            take_profit = risk_metrics.take_profit if hasattr(risk_metrics, 'take_profit') else 0
            position_size = risk_metrics.position_size if hasattr(risk_metrics, 'position_size') else 0
            risk_reward = risk_metrics.risk_reward_ratio if hasattr(risk_metrics, 'risk_reward_ratio') else 0
            
            notes = recommendation.get('notes', [])
            notes_text = "; ".join(notes[:2]) if notes else "None"
            
            html += f"""
            <tr class="{signal_class}">
                <td><strong>{symbol}</strong></td>
                <td>{exchange}</td>
                <td><strong>{signal_type.upper().replace('_', ' ')}</strong></td>
                <td class="{confidence_class}">{confidence_text}</td>
                <td class="{risk_class}">{risk_text}</td>
                <td>{currency}{stop_loss * currency_multiplier:.0f}</td>
                <td>{currency}{take_profit * currency_multiplier:.0f}</td>
                <td>{position_size:.1%}</td>
                <td>{risk_reward:.2f}</td>
                <td style="font-size: 10px;">{notes_text}</td>
            </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        # Footer
        html += """
        <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 8px;">
            <h3>📋 Trading Guidelines</h3>
            <ul style="font-size: 12px; line-height: 1.6;">
                <li><strong>Strong Signals:</strong> High confidence, low risk - consider taking position</li>
                <li><strong>Medium Signals:</strong> Moderate confidence - use smaller position size</li>
                <li><strong>Weak Signals:</strong> Low confidence, high risk - avoid or use very small size</li>
                <li><strong>Always use stop loss</strong> and never risk more than 1-2% per trade</li>
                <li><strong>Check volume confirmation</strong> before entering positions</li>
                <li><strong>Monitor market conditions</strong> and adjust position sizes accordingly</li>
            </ul>
        </div>
        """
        
        return html
    
    def collect_enhanced_signals(self) -> List[Dict[str, Any]]:
        """Collect enhanced signals for all monitored symbols"""
        
        symbols = self.get_symbols_to_monitor()
        signals_data = []
        
        for symbol_id, ticker, exchange in symbols:
            try:
                # Check if market is open
                market_open = is_market_open(exchange)
                if not market_open:
                    logger.debug(f"Skipping {ticker} ({exchange}) - market closed")
                    continue
                
                # Get enhanced signal data
                signal_data = self.get_enhanced_signal_data(symbol_id, self.timeframes)
                
                if signal_data and signal_data.get('enhanced_signal'):
                    signal_data['symbol'] = ticker
                    signal_data['exchange'] = exchange
                    signals_data.append(signal_data)
                
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")
                continue
        
        return signals_data
    
    def run_enhanced_digest(self) -> bool:
        """Run enhanced email digest"""
        
        try:
            # Check if any market is open
            symbols = self.get_symbols_to_monitor()
            markets_open = False
            
            for sid, ticker, exchange in symbols:
                market_open = is_market_open(exchange)
                if market_open:
                    markets_open = True
                    break
            
            if not markets_open:
                logger.info("All monitored markets are closed; skipping enhanced digest send.")
                return False
            
            # Check email service
            if not email_service.is_configured():
                logger.warning("Email service not configured; skipping enhanced digest send")
                return False
            
            # Refresh signals by running pipeline for open markets
            for sid, ticker, exchange in symbols:
                try:
                    market_open = is_market_open(exchange)
                    if market_open:
                        job_sma_pipeline(sid, ticker, exchange)
                        logger.debug(f"Ran SMA pipeline for {ticker} ({exchange}) - market open")
                except Exception as e:
                    logger.warning(f"Pipeline failed for {ticker}: {e}")
                    continue
            
            # Collect enhanced signals
            signals_data = self.collect_enhanced_signals()
            
            if not signals_data:
                logger.info("No enhanced signals available; skipping digest send.")
                return False
            
            # Build enhanced HTML
            html = self.build_enhanced_html_table(signals_data)
            
            # Send email
            subject = os.getenv("EMAIL_DIGEST_SUBJECT", "Enhanced Trading Signals")
            ok = bool(email_service.send(
                subject,
                body_text="Enhanced Trading Signals (HTML) attached",
                body_html=html
            ))
            
            logger.info(f"Enhanced digest sent: {ok}")
            return ok
            
        except Exception as e:
            logger.error(f"Error running enhanced digest: {e}")
            return False

def main():
    """Main function for enhanced email digest"""
    db.init_db(os.getenv("DATABASE_URL"))
    
    digest = EnhancedEmailDigest()
    
    if os.getenv("ONESHOT") == "1":
        # Run once for testing
        digest.run_enhanced_digest()
    else:
        # Run continuously
        interval = int(os.getenv("EMAIL_DIGEST_INTERVAL_SECONDS", "600"))
        logger.info(f"Starting enhanced email digest loop; interval={interval} seconds")
        
        while True:
            try:
                digest.run_enhanced_digest()
            except Exception as e:
                logger.error(f"Error in enhanced digest loop: {e}")
            
            time.sleep(interval)

if __name__ == "__main__":
    main()
