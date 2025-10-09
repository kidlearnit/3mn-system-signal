#!/usr/bin/env python3
import sqlite3
import os

# Tạo database và table symbols
db_path = "test.db"

# Xóa database cũ nếu có
if os.path.exists(db_path):
    os.remove(db_path)

# Tạo database mới
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tạo table symbols
cursor.execute("""
CREATE TABLE symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    exchange TEXT,
    currency TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Thêm một số symbols mẫu
symbols = [
    ('AAPL', 'NASDAQ', 'USD'),
    ('GOOGL', 'NASDAQ', 'USD'),
    ('MSFT', 'NASDAQ', 'USD'),
    ('TSLA', 'NASDAQ', 'USD'),
    ('AMZN', 'NASDAQ', 'USD'),
    ('META', 'NASDAQ', 'USD'),
    ('NVDA', 'NASDAQ', 'USD'),
    ('NFLX', 'NASDAQ', 'USD'),
    ('VIC', 'HOSE', 'VND'),
    ('VCB', 'HOSE', 'VND'),
    ('BID', 'HOSE', 'VND'),
    ('CTG', 'HOSE', 'VND'),
    ('TCB', 'HOSE', 'VND'),
    ('MBB', 'HOSE', 'VND'),
    ('VPB', 'HOSE', 'VND'),
    ('STB', 'HOSE', 'VND'),
    ('FPT', 'HOSE', 'VND'),
    ('HPG', 'HOSE', 'VND'),
    ('GAS', 'HOSE', 'VND'),
    ('PLX', 'HOSE', 'VND'),
]

for ticker, exchange, currency in symbols:
    cursor.execute("""
        INSERT INTO symbols (ticker, exchange, currency, active)
        VALUES (?, ?, ?, 1)
    """, (ticker, exchange, currency))

conn.commit()
conn.close()

print(f"✅ Created {len(symbols)} symbols in {db_path}")
print("Symbols created:")
for ticker, exchange, currency in symbols:
    print(f"  - {ticker} ({exchange}, {currency})")
