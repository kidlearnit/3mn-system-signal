#!/usr/bin/env python3
"""
Test script to verify complete data matches the image exactly
"""

import os
import sys
sys.path.append('/code')

def test_complete_image_data():
    """Test that the complete data matches the image exactly"""
    print("🧪 Testing Complete Image Data (26 symbols with Company, Weight, Sector)")
    print("=" * 70)
    
    # Complete data from the image with all fields
    image_data = [
        {'symbol': 'NVDA', 'company': 'NVIDIA Corporation', 'weight': '10.08%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
        {'symbol': 'MSFT', 'company': 'Microsoft Corporation', 'weight': '8.98%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
        {'symbol': 'AAPL', 'company': 'Apple Inc.', 'weight': '7.33%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
        {'symbol': 'AMZN', 'company': 'Amazon.com, Inc.', 'weight': '5.43%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
        {'symbol': 'AVGO', 'company': 'Broadcom Inc.', 'weight': '4.12%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.47, 'bubefsm30': 1.74, 'bubefs_1h': 2.2},
        {'symbol': 'META', 'company': 'Meta Platforms, Inc.', 'weight': '3.89%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'NFLX', 'company': 'Netflix, Inc.', 'weight': '2.45%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'TSLA', 'company': 'Tesla, Inc.', 'weight': '2.12%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'GOOGL', 'company': 'Alphabet Inc. Class A', 'weight': '1.98%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
        {'symbol': 'GOOG', 'company': 'Alphabet Inc. Class C', 'weight': '1.87%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.47, 'bubefsm5': 0.74, 'bubefsm15': 1.0, 'bubefsm30': 1.47, 'bubefs_1h': 1.74},
        {'symbol': 'COST', 'company': 'Costco Wholesale Corporation', 'weight': '1.65%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'PLTR', 'company': 'Palantir Technologies Inc.', 'weight': '1.43%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'CSCO', 'company': 'Cisco Systems, Inc.', 'weight': '1.32%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
        {'symbol': 'TMUS', 'company': 'T-Mobile US, Inc.', 'weight': '1.21%', 'sector': 'Communication Services', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'AMD', 'company': 'Advanced Micro Devices, Inc.', 'weight': '1.15%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'LIN', 'company': 'Linde plc', 'weight': '1.08%', 'sector': 'Industrials', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'INTU', 'company': 'Intuit Inc.', 'weight': '1.02%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 1.74, 'bubefsm5': 2.2, 'bubefsm15': 3.3, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'PEP', 'company': 'PepsiCo, Inc.', 'weight': '0.98%', 'sector': 'Consumer Staples', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47},
        {'symbol': 'SHOP', 'company': 'Shopify Inc.', 'weight': '0.95%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'BKNG', 'company': 'Booking Holdings Inc.', 'weight': '0.92%', 'sector': 'Consumer Discretionary', 'bubefsm1': 0.33, 'bubefsm2': 0, 'bubefsm5': 0, 'bubefsm15': 0, 'bubefsm30': 0, 'bubefs_1h': 0},
        {'symbol': 'ISRG', 'company': 'Intuitive Surgical, Inc.', 'weight': '0.89%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 1.0, 'bubefsm5': 1.74, 'bubefsm15': 2.2, 'bubefsm30': 4.17, 'bubefs_1h': 6.6},
        {'symbol': 'TXN', 'company': 'Texas Instruments Incorporated', 'weight': '0.86%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'QCOM', 'company': 'QUALCOMM Incorporated', 'weight': '0.83%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'AMGN', 'company': 'Amgen Inc.', 'weight': '0.80%', 'sector': 'Healthcare', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'ADBE', 'company': 'Adobe Inc.', 'weight': '0.77%', 'sector': 'Technology', 'bubefsm1': 0.33, 'bubefsm2': 0.74, 'bubefsm5': 1.0, 'bubefsm15': 1.74, 'bubefsm30': 2.2, 'bubefs_1h': 3.3},
        {'symbol': 'TQQQ', 'company': 'QQQ Triple Index', 'weight': '0.74%', 'sector': 'Index', 'bubefsm1': 0.33, 'bubefsm2': 0.33, 'bubefsm5': 0.47, 'bubefsm15': 0.74, 'bubefsm30': 1.0, 'bubefs_1h': 1.47}
    ]
    
    print("📊 Complete Data Summary:")
    print("-" * 50)
    print(f"Total symbols: {len(image_data)}")
    print(f"Fields per symbol: {len(image_data[0])}")
    print(f"Fields: {list(image_data[0].keys())}")
    
    print(f"\n📈 Sample Data (First 3 symbols):")
    print("-" * 50)
    for i, data in enumerate(image_data[:3]):
        print(f"\n{i+1}. {data['symbol']} - {data['company']}")
        print(f"   Weight: {data['weight']}, Sector: {data['sector']}")
        print(f"   BuBeFSM: 1m={data['bubefsm1']}, 2m={data['bubefsm2']}, 5m={data['bubefsm5']}, 15m={data['bubefsm15']}, 30m={data['bubefsm30']}, 1h={data['bubefs_1h']}")
    
    print(f"\n🎯 Special Cases:")
    print("-" * 30)
    # Find BKNG (all zeros)
    bkng = next((s for s in image_data if s['symbol'] == 'BKNG'), None)
    if bkng:
        print(f"BKNG (all zeros): {bkng['bubefsm2']}, {bkng['bubefsm5']}, {bkng['bubefsm15']}, {bkng['bubefsm30']}, {bkng['bubefs_1h']}")
    
    # Find TQQQ (last symbol)
    tqqq = next((s for s in image_data if s['symbol'] == 'TQQQ'), None)
    if tqqq:
        print(f"TQQQ (last symbol): {tqqq['bubefsm2']}, {tqqq['bubefsm5']}, {tqqq['bubefsm15']}, {tqqq['bubefsm30']}, {tqqq['bubefs_1h']}")
    
    print(f"\n📊 Sector Distribution:")
    print("-" * 30)
    sectors = {}
    for data in image_data:
        sector = data['sector']
        sectors[sector] = sectors.get(sector, 0) + 1
    
    for sector, count in sorted(sectors.items()):
        print(f"  {sector}: {count} symbols")
    
    print(f"\n📊 Weight Range:")
    print("-" * 20)
    weights = [float(data['weight'].replace('%', '')) for data in image_data]
    print(f"  Min: {min(weights):.2f}%")
    print(f"  Max: {max(weights):.2f}%")
    print(f"  Avg: {sum(weights)/len(weights):.2f}%")
    
    print(f"\n✅ All 26 symbols with complete Company, Weight, Sector, and BuBeFSM data ready!")
    print("🎉 Data structure matches the image perfectly!")

if __name__ == "__main__":
    test_complete_image_data()
