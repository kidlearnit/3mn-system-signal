#!/usr/bin/env python3
"""
Test script for 6 timeframes logic (1m, 2m, 5m, 15m, 30m, 1h)
Tests the new logic where signals are only sent when ALL 6 timeframes agree
"""

import os
import sys
sys.path.append('/code')

from app.db import init_db, SessionLocal
from worker.macd_multi_us_jobs import _calculate_overall_bubefsm_signal, _calculate_bubefsm_signals

def test_6_timeframes_logic():
    """Test the 6 timeframes unanimous signal logic"""
    print("🧪 Testing 6 Timeframes Unanimous Signal Logic")
    print("=" * 60)
    
    # Test 1: All BULL (should be unanimous)
    print("\n1️⃣ Testing UNANIMOUS BULL (all 6 timeframes BULL):")
    timeframe_results_bull = {
        '1m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.8, 'fast_macd': 0.8, 'signal_macd': 0.7, 'threshold': 0.5}, 'threshold': 0.5},
        '2m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.7, 'fast_macd': 0.7, 'signal_macd': 0.6, 'threshold': 0.5}, 'threshold': 0.5},
        '5m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.6, 'fast_macd': 0.6, 'signal_macd': 0.5, 'threshold': 0.5}, 'threshold': 0.5},
        '15m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.9, 'fast_macd': 0.9, 'signal_macd': 0.8, 'threshold': 0.5}, 'threshold': 0.5},
        '30m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.9, 'fast_macd': 0.9, 'signal_macd': 0.8, 'threshold': 0.5}, 'threshold': 0.5},
        '1h': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.9, 'fast_macd': 0.9, 'signal_macd': 0.8, 'threshold': 0.5}, 'threshold': 0.5}
    }
    
    result_bull = _calculate_overall_bubefsm_signal(timeframe_results_bull)
    print(f"   Signal: {result_bull['signal_type']}")
    print(f"   Bull: {result_bull['bull_count']}, Bear: {result_bull['bear_count']}, Neutral: {result_bull['neutral_count']}")
    print(f"   Confidence: {result_bull['confidence']}")
    print(f"   Unanimous: {result_bull['unanimous']}")
    print(f"   ✅ Should send signal: {result_bull['signal_type'] != 'NEUTRAL' and result_bull['unanimous']}")
    
    # Test 2: All BEAR (should be unanimous)
    print("\n2️⃣ Testing UNANIMOUS BEAR (all 6 timeframes BEAR):")
    timeframe_results_bear = {
        '1m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.8, 'fast_macd': -0.8, 'signal_macd': -0.7, 'threshold': 0.5}, 'threshold': 0.5},
        '2m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.7, 'fast_macd': -0.7, 'signal_macd': -0.6, 'threshold': 0.5}, 'threshold': 0.5},
        '5m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.6, 'fast_macd': -0.6, 'signal_macd': -0.5, 'threshold': 0.5}, 'threshold': 0.5},
        '15m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.9, 'fast_macd': -0.9, 'signal_macd': -0.8, 'threshold': 0.5}, 'threshold': 0.5},
        '30m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.6, 'fast_macd': -0.6, 'signal_macd': -0.5, 'threshold': 0.5}, 'threshold': 0.5},
        '1h': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.6, 'fast_macd': -0.6, 'signal_macd': -0.5, 'threshold': 0.5}, 'threshold': 0.5}
    }
    
    result_bear = _calculate_overall_bubefsm_signal(timeframe_results_bear)
    print(f"   Signal: {result_bear['signal_type']}")
    print(f"   Bull: {result_bear['bull_count']}, Bear: {result_bear['bear_count']}, Neutral: {result_bear['neutral_count']}")
    print(f"   Confidence: {result_bear['confidence']}")
    print(f"   Unanimous: {result_bear['unanimous']}")
    print(f"   ✅ Should send signal: {result_bear['signal_type'] != 'NEUTRAL' and result_bear['unanimous']}")
    
    # Test 3: Mixed signals (should NOT send signal)
    print("\n3️⃣ Testing MIXED SIGNALS (should NOT send signal):")
    timeframe_results_mixed = {
        '1m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.8, 'fast_macd': 0.8, 'signal_macd': 0.7, 'threshold': 0.5}, 'threshold': 0.5},
        '2m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.7, 'fast_macd': -0.7, 'signal_macd': -0.6, 'threshold': 0.5}, 'threshold': 0.5},
        '5m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.6, 'fast_macd': 0.6, 'signal_macd': 0.5, 'threshold': 0.5}, 'threshold': 0.5},
        '15m': {'bubefsm': {'signal_type': 'BEAR', 'strength': 0.5, 'fast_macd': -0.5, 'signal_macd': -0.4, 'threshold': 0.5}, 'threshold': 0.5},
        '30m': {'bubefsm': {'signal_type': 'NEUTRAL', 'strength': 0, 'fast_macd': 0.3, 'signal_macd': 0.2, 'threshold': 0.5}, 'threshold': 0.5},
        '1h': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.4, 'fast_macd': 0.4, 'signal_macd': 0.3, 'threshold': 0.5}, 'threshold': 0.5}
    }
    
    result_mixed = _calculate_overall_bubefsm_signal(timeframe_results_mixed)
    print(f"   Signal: {result_mixed['signal_type']}")
    print(f"   Bull: {result_mixed['bull_count']}, Bear: {result_mixed['bear_count']}, Neutral: {result_mixed['neutral_count']}")
    print(f"   Confidence: {result_mixed['confidence']}")
    print(f"   Unanimous: {result_mixed['unanimous']}")
    print(f"   ❌ Should NOT send signal: {result_mixed['signal_type'] != 'NEUTRAL' and result_mixed['unanimous']}")
    
    # Test 4: Majority BULL but not unanimous (should NOT send signal)
    print("\n4️⃣ Testing MAJORITY BULL (5/6 BULL, should NOT send signal):")
    timeframe_results_majority = {
        '1m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.8, 'fast_macd': 0.8, 'signal_macd': 0.7, 'threshold': 0.5}, 'threshold': 0.5},
        '2m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.7, 'fast_macd': 0.7, 'signal_macd': 0.6, 'threshold': 0.5}, 'threshold': 0.5},
        '5m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.6, 'fast_macd': 0.6, 'signal_macd': 0.5, 'threshold': 0.5}, 'threshold': 0.5},
        '15m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.9, 'fast_macd': 0.9, 'signal_macd': 0.8, 'threshold': 0.5}, 'threshold': 0.5},
        '30m': {'bubefsm': {'signal_type': 'BULL', 'strength': 0.9, 'fast_macd': 0.9, 'signal_macd': 0.8, 'threshold': 0.5}, 'threshold': 0.5},
        '1h': {'bubefsm': {'signal_type': 'NEUTRAL', 'strength': 0, 'fast_macd': 0.3, 'signal_macd': 0.2, 'threshold': 0.5}, 'threshold': 0.5}
    }
    
    result_majority = _calculate_overall_bubefsm_signal(timeframe_results_majority)
    print(f"   Signal: {result_majority['signal_type']}")
    print(f"   Bull: {result_majority['bull_count']}, Bear: {result_majority['bear_count']}, Neutral: {result_majority['neutral_count']}")
    print(f"   Confidence: {result_majority['confidence']}")
    print(f"   Unanimous: {result_majority['unanimous']}")
    print(f"   ❌ Should NOT send signal: {result_majority['signal_type'] != 'NEUTRAL' and result_majority['unanimous']}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("✅ Unanimous BULL (6/6): Should send signal")
    print("✅ Unanimous BEAR (6/6): Should send signal") 
    print("❌ Mixed signals: Should NOT send signal")
    print("❌ Majority (5/6): Should NOT send signal")
    print("=" * 60)

def test_field_mapping():
    """Test field name mapping for different timeframes"""
    print("\n🔍 Testing Field Name Mapping:")
    print("-" * 40)
    
    # Test field name mapping logic
    test_cases = [
        ('1m', 'bubefsm1'),
        ('2m', 'bubefsm2'),
        ('5m', 'bubefsm5'),
        ('15m', 'bubefsm15'),
        ('30m', 'bubefsm30'),
        ('1h', 'bubefs_1h')
    ]
    
    for tf, expected_field in test_cases:
        if tf == '1m':
            field_name = 'bubefsm1'
        elif tf == '1h':
            field_name = 'bubefs_1h'
        else:
            field_name = f'bubefsm{tf.replace("m", "")}'
        
        status = "✅" if field_name == expected_field else "❌"
        print(f"   {status} {tf} -> {field_name} (expected: {expected_field})")

if __name__ == "__main__":
    # Initialize database
    init_db(os.getenv("DATABASE_URL"))
    
    # Run tests
    test_field_mapping()
    test_6_timeframes_logic()
    
    print("\n🎉 All tests completed!")
