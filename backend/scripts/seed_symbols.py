import os
from sqlalchemy import text
from app.db import init_db

# Khởi tạo DB session
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal

SEED = [
    # --- Việt Nam (30 mã) ---
    ('VN30F2509','HOSE','VND'),
    # ('FPT','HOSE','VND'),
    # ('HPG','HOSE','VND'),
    # ('VCB','HOSE','VND'),
    # ('BID','HOSE','VND'),
    # ('CTG','HOSE','VND'),
    # ('TCB','HOSE','VND'),
    # ('MBB','HOSE','VND'),
    # ('VPB','HOSE','VND'),
    # ('STB','HOSE','VND'),
    # ('SSI','HOSE','VND'),
    # ('HSG','HOSE','VND'),
    # ('GAS','HOSE','VND'),
    # ('PLX','HOSE','VND'),
    # ('VIC','HOSE','VND'),
    # ('VHM','HOSE','VND'),
    # ('NVL','HOSE','VND'),
    # ('PDR','HOSE','VND'),
    # ('KDH','HOSE','VND'),
    # ('DXG','HOSE','VND'),
    # ('DIG','HOSE','VND'),
    # ('HBC','HOSE','VND'),
    # ('REE','HOSE','VND'),
    # ('VRE','HOSE','VND'),
    # ('SAB','HOSE','VND'),
    # ('MSN','HOSE','VND'),
    # ('VJC','HOSE','VND'),
    # ('HVN','HOSE','VND'),
    # ('HAG','HOSE','VND'),
    # ('ROS','HOSE','VND'),


    # --- Mỹ (100 mã, bao gồm TQQQ) ---
    # ('AAPL','NASDAQ','USD'),
    # ('MSFT','NASDAQ','USD'),
    # ('GOOGL','NASDAQ','USD'),
    # ('AMZN','NASDAQ','USD'),
    # ('META','NASDAQ','USD'),
    # ('TSLA','NASDAQ','USD'),
    # ('NVDA','NASDAQ','USD'),
    # ('NFLX','NASDAQ','USD'),
    # ('ADBE','NASDAQ','USD'),
    # ('PYPL','NASDAQ','USD'),
    # ('INTC','NASDAQ','USD'),
    # ('CSCO','NASDAQ','USD'),
    # ('PEP','NASDAQ','USD'),
    # ('AVGO','NASDAQ','USD'),
    # ('COST','NASDAQ','USD'),
    # ('TXN','NASDAQ','USD'),
    # ('QCOM','NASDAQ','USD'),
    # ('AMD','NASDAQ','USD'),
    # ('AMAT','NASDAQ','USD'),
    # ('SBUX','NASDAQ','USD'),
    # ('BKNG','NASDAQ','USD'),
    # ('MDLZ','NASDAQ','USD'),
    # ('GILD','NASDAQ','USD'),
    # ('ISRG','NASDAQ','USD'),
    # ('LRCX','NASDAQ','USD'),
    # ('ADP','NASDAQ','USD'),
    # ('MU','NASDAQ','USD'),
    # ('ZM','NASDAQ','USD'),
    # ('DOCU','NASDAQ','USD'),
    ('TQQQ','NASDAQ','USD'),  # yêu cầu đặc biệt

]

with SessionLocal() as s:
    for t,e,c in SEED:
        s.execute(text("""
            INSERT INTO symbols (ticker, exchange, currency, active)
            VALUES (:t,:e,:c,1)
            ON DUPLICATE KEY UPDATE exchange=:e, currency=:c, active=1
        """), {'t': t, 'e': e, 'c': c})
    s.commit()

print(f"Seeded {len(SEED)} symbols.")
