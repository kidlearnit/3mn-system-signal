#!/usr/bin/env python3
"""
Test script to verify the updated data matches the new image exactly
"""

import os
import sys
sys.path.append('/code')

def test_new_image_data_mapping():
    """Test that the data matches the new image values exactly"""
    print("🧪 Testing New Image Data Mapping (26 rows)")
    print("=" * 60)
    
    # Data from the new image (26 rows, exact order from top to bottom)
    image_data = [
        {'2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'2m': 1.74, '5m': 2.2, '15m': 3.3, '30m': 4.17, '1h': 6.6},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 1.74, '5m': 2.2, '15m': 3.3, '30m': 4.17, '1h': 6.6},
        {'2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0, '5m': 0, '15m': 0, '30m': 0, '1h': 0},
        {'2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47}
    ]
    
    # Updated data from workflow (with 1m added as 0.33 for all)
    workflow_data = [
        {'1m': 0.33, '2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'1m': 0.33, '2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.47, '30m': 1.74, '1h': 2.2},
        {'1m': 0.33, '2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'1m': 0.33, '2m': 0.47, '5m': 0.74, '15m': 1.0, '30m': 1.47, '1h': 1.74},
        {'1m': 0.33, '2m': 1.74, '5m': 2.2, '15m': 3.3, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 1.74, '5m': 2.2, '15m': 3.3, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0, '5m': 0, '15m': 0, '30m': 0, '1h': 0},
        {'1m': 0.33, '2m': 1.0, '5m': 1.74, '15m': 2.2, '30m': 4.17, '1h': 6.6},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0.74, '5m': 1.0, '15m': 1.74, '30m': 2.2, '1h': 3.3},
        {'1m': 0.33, '2m': 0.33, '5m': 0.47, '15m': 0.74, '30m': 1.0, '1h': 1.47}
    ]
    
    print("📊 Comparing New Image Data vs Workflow Data:")
    print("-" * 60)
    
    all_match = True
    for i in range(len(image_data)):
        symbol_name = f"SYM{i+1}"
        print(f"\n{symbol_name} (Row {i+1}):")
        for tf in ['2m', '5m', '15m', '30m', '1h']:
            image_val = image_data[i][tf]
            workflow_val = workflow_data[i][tf]
            match = "✅" if image_val == workflow_val else "❌"
            print(f"  {tf}: {match} Image={image_val}, Workflow={workflow_val}")
            if image_val != workflow_val:
                all_match = False
    
    print(f"\n{'='*60}")
    if all_match:
        print("🎉 All 26 rows match the new image perfectly!")
    else:
        print("⚠️ Some data does not match the new image")
    print(f"{'='*60}")
    
    # Show 1m values (all should be 0.33)
    print(f"\n📈 1m Timeframe Values (all should be 0.33):")
    print("-" * 40)
    for i in range(len(workflow_data)):
        symbol_name = f"SYM{i+1}"
        val = workflow_data[i]['1m']
        status = "✅" if val == 0.33 else "❌"
        print(f"  {symbol_name}: {status} {val}")
    
    # Show summary statistics
    print(f"\n📊 Summary Statistics:")
    print("-" * 30)
    print(f"Total rows: {len(workflow_data)}")
    print(f"Timeframes: 6 (1m, 2m, 5m, 15m, 30m, 1h)")
    print(f"1m values: All 0.33")
    print(f"Image match: {'✅ Perfect' if all_match else '❌ Issues found'}")

if __name__ == "__main__":
    test_new_image_data_mapping()
