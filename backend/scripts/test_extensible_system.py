#!/usr/bin/env python3
"""
Test Extensible System - Kiểm tra hệ thống có thể mở rộng
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append('/code')

from app.db import SessionLocal, init_db
from app.services.extensible_signal_engine import extensible_signal_engine
from app.services.strategy_base import strategy_registry, StrategyConfig
from app.services.aggregation_engine import AggregationConfig, AggregationMethod
from app.services.strategy_implementations import RSIStrategy

# Initialize DB
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

def test_extensible_system():
    """Test hệ thống extensible"""
    
    print("🎯 Testing Extensible Strategy System")
    print("=" * 60)
    
    try:
        # 1. Test available strategies
        print("1. 📊 Testing Available Strategies")
        print("-" * 40)
        
        strategies = extensible_signal_engine.get_available_strategies()
        print(f"Available strategies: {strategies}")
        
        for strategy_name in strategies:
            info = extensible_signal_engine.get_strategy_info(strategy_name)
            print(f"  {strategy_name}: {info['description']}")
            print(f"    Weight: {info['weight']}, Min Confidence: {info['min_confidence']}")
            print(f"    Required Indicators: {info['required_indicators']}")
            print(f"    Supported Timeframes: {info['supported_timeframes']}")
            print()
        
        # 2. Test signal evaluation
        print("2. 🔍 Testing Signal Evaluation")
        print("-" * 40)
        
        with SessionLocal() as s:
            # Lấy symbol có dữ liệu
            symbol_row = s.execute("""
                SELECT DISTINCT s.id, s.ticker, s.exchange
                FROM symbols s
                WHERE EXISTS (
                    SELECT 1 FROM indicators_sma sma 
                    WHERE sma.symbol_id = s.id
                ) AND EXISTS (
                    SELECT 1 FROM indicators_macd macd 
                    WHERE macd.symbol_id = s.id
                )
                LIMIT 1
            """).first()
            
            if not symbol_row:
                print("❌ No symbols with data found")
                return False
            
            symbol_id, ticker, exchange = symbol_row
            print(f"Testing with {ticker} ({exchange})")
            
            # Test với tất cả strategies
            result = extensible_signal_engine.evaluate_signal(
                symbol_id, ticker, exchange, '5m'
            )
            
            print(f"Final Signal: {result['final_signal']}")
            print(f"Final Direction: {result['final_direction']}")
            print(f"Final Strength: {result['final_strength']:.2f}")
            print(f"Final Confidence: {result['final_confidence']:.2f}")
            print(f"Participating Strategies: {result['participating_strategies']}")
            print()
            
            # Test với chỉ SMA và MACD
            result_sma_macd = extensible_signal_engine.evaluate_signal(
                symbol_id, ticker, exchange, '5m', ['SMA Strategy', 'MACD Strategy']
            )
            
            print(f"SMA+MACD Signal: {result_sma_macd['final_signal']}")
            print(f"SMA+MACD Direction: {result_sma_macd['final_direction']}")
            print(f"SMA+MACD Strength: {result_sma_macd['final_strength']:.2f}")
            print(f"SMA+MACD Confidence: {result_sma_macd['final_confidence']:.2f}")
            print()
        
        # 3. Test multi-timeframe
        print("3. 🔄 Testing Multi-timeframe Analysis")
        print("-" * 40)
        
        multi_result = extensible_signal_engine.evaluate_multi_timeframe(
            symbol_id, ticker, exchange
        )
        
        print(f"Overall Direction: {multi_result['overall_direction']}")
        print(f"Overall Strength: {multi_result['overall_strength']:.2f}")
        print(f"Overall Confidence: {multi_result['overall_confidence']:.2f}")
        print(f"Valid Timeframes: {multi_result['valid_timeframes']}/{multi_result['total_timeframes']}")
        print()
        
        # 4. Test aggregation methods
        print("4. ⚙️ Testing Different Aggregation Methods")
        print("-" * 40)
        
        aggregation_methods = [
            AggregationMethod.WEIGHTED_AVERAGE,
            AggregationMethod.MAJORITY_VOTE,
            AggregationMethod.CONSENSUS,
            AggregationMethod.CONFIDENCE_WEIGHTED
        ]
        
        for method in aggregation_methods:
            config = AggregationConfig(method=method)
            extensible_signal_engine.update_aggregation_config(config)
            
            result = extensible_signal_engine.evaluate_signal(
                symbol_id, ticker, exchange, '5m'
            )
            
            print(f"{method.value}: {result['final_direction']} (strength: {result['final_strength']:.2f}, confidence: {result['final_confidence']:.2f})")
        
        print()
        
        # 5. Test adding new strategy
        print("5. ➕ Testing Adding New Strategy")
        print("-" * 40)
        
        # Tạo RSI strategy mới với config khác
        custom_rsi_config = StrategyConfig(
            name="Custom RSI Strategy",
            description="Custom RSI with different parameters",
            version="1.0.0",
            weight=0.9,
            min_confidence=0.7,
            parameters={
                'rsi_period': 21,
                'overbought_level': 75,
                'oversold_level': 25,
                'strong_overbought': 85,
                'strong_oversold': 15
            }
        )
        
        custom_rsi = RSIStrategy(custom_rsi_config)
        success = extensible_signal_engine.add_strategy(custom_rsi)
        
        if success:
            print("✅ Custom RSI Strategy added successfully")
            
            # Test với strategy mới
            strategies_with_custom = extensible_signal_engine.get_available_strategies()
            print(f"Available strategies after adding: {strategies_with_custom}")
            
            # Test signal với strategy mới
            result_with_custom = extensible_signal_engine.evaluate_signal(
                symbol_id, ticker, exchange, '5m', ['SMA Strategy', 'MACD Strategy', 'Custom RSI Strategy']
            )
            
            print(f"Signal with custom RSI: {result_with_custom['final_direction']}")
            print(f"Participating strategies: {result_with_custom['participating_strategies']}")
            
            # Xóa strategy mới
            extensible_signal_engine.remove_strategy("Custom RSI Strategy")
            print("✅ Custom RSI Strategy removed")
            
        else:
            print("❌ Failed to add custom RSI strategy")
        
        print()
        
        # 6. Test aggregation config
        print("6. 🔧 Testing Aggregation Configuration")
        print("-" * 40)
        
        # Test với config khác
        custom_config = AggregationConfig(
            method=AggregationMethod.CONSENSUS,
            min_strategies=2,
            consensus_threshold=0.7,
            confidence_threshold=0.6,
            custom_weights={
                'SMA Strategy': 1.2,
                'MACD Strategy': 1.0,
                'RSI Strategy': 0.8
            }
        )
        
        extensible_signal_engine.update_aggregation_config(custom_config)
        
        result_custom_config = extensible_signal_engine.evaluate_signal(
            symbol_id, ticker, exchange, '5m'
        )
        
        print(f"Custom config result: {result_custom_config['final_direction']}")
        print(f"Custom config strength: {result_custom_config['final_strength']:.2f}")
        print(f"Custom config confidence: {result_custom_config['final_confidence']:.2f}")
        
        # Reset về config mặc định
        default_config = AggregationConfig()
        extensible_signal_engine.update_aggregation_config(default_config)
        print("✅ Reset to default aggregation config")
        
        print()
        
        # 7. Test performance
        print("7. 📈 Testing Performance")
        print("-" * 40)
        
        import time
        
        start_time = time.time()
        for i in range(10):
            extensible_signal_engine.evaluate_signal(symbol_id, ticker, exchange, '5m')
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        print(f"Average evaluation time: {avg_time:.3f} seconds")
        print(f"Evaluations per second: {1/avg_time:.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extensible system: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_strategy_creation():
    """Test tạo strategy mới"""
    
    print("\n🛠️ Testing Strategy Creation")
    print("=" * 40)
    
    try:
        # Tạo một strategy đơn giản
        from app.services.strategy_base import BaseStrategy, StrategyConfig, SignalResult, SignalDirection
        
        class SimpleMovingAverageStrategy(BaseStrategy):
            """Simple Moving Average Strategy - Ví dụ strategy mới"""
            
            def __init__(self, config: StrategyConfig = None):
                if config is None:
                    config = StrategyConfig(
                        name="Simple MA Strategy",
                        description="Simple moving average crossover strategy",
                        version="1.0.0",
                        weight=0.7,
                        min_confidence=0.5,
                        parameters={
                            'short_period': 10,
                            'long_period': 20
                        }
                    )
                super().__init__(config)
            
            def evaluate_signal(self, symbol_id: int, ticker: str, exchange: str, 
                               timeframe: str) -> SignalResult:
                """Đánh giá tín hiệu (mock implementation)"""
                
                # Mock signal evaluation
                import random
                direction = random.choice(['BUY', 'SELL', 'NEUTRAL'])
                strength = random.uniform(0.3, 0.9)
                confidence = random.uniform(0.4, 0.8)
                
                return SignalResult(
                    strategy_name=self.config.name,
                    signal_type=direction.lower(),
                    direction=SignalDirection(direction),
                    strength=strength,
                    confidence=confidence,
                    details={
                        'short_ma': 100.0,
                        'long_ma': 98.5,
                        'crossover': direction == 'BUY'
                    },
                    timestamp=datetime.now().isoformat(),
                    timeframe=timeframe,
                    symbol_id=symbol_id,
                    ticker=ticker,
                    exchange=exchange
                )
            
            def get_required_indicators(self):
                return ['sma_10', 'sma_20']
            
            def get_supported_timeframes(self):
                return ['5m', '15m', '30m', '1h', '4h']
        
        # Tạo và đăng ký strategy
        simple_ma_strategy = SimpleMovingAverageStrategy()
        success = extensible_signal_engine.add_strategy(simple_ma_strategy)
        
        if success:
            print("✅ Simple MA Strategy created and registered successfully")
            
            # Test strategy
            strategies = extensible_signal_engine.get_available_strategies()
            print(f"Available strategies: {strategies}")
            
            # Test signal evaluation
            result = extensible_signal_engine.evaluate_signal(
                1, "TEST", "TEST", "5m", ["Simple MA Strategy"]
            )
            
            print(f"Simple MA Signal: {result['final_direction']}")
            print(f"Simple MA Strength: {result['final_strength']:.2f}")
            
            # Xóa strategy
            extensible_signal_engine.remove_strategy("Simple MA Strategy")
            print("✅ Simple MA Strategy removed")
            
        else:
            print("❌ Failed to create Simple MA Strategy")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing strategy creation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Starting Extensible System Test")
    print("=" * 80)
    
    try:
        # Test extensible system
        success1 = test_extensible_system()
        
        # Test strategy creation
        success2 = test_strategy_creation()
        
        if success1 and success2:
            print("\n✅ All Extensible System Tests Passed!")
            print("💡 The extensible system is working correctly")
            print("🎯 You can now easily add new strategies!")
        else:
            print("\n❌ Some tests failed!")
            print("💡 Check the logs for more details")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
