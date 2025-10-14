import os, time
import redis
from rq import Queue
from datetime import datetime
from app.db import SessionLocal
from sqlalchemy import text

r = redis.from_url(os.getenv('REDIS_URL'))
q = Queue('default', connection=r)

# Đơn giản: mỗi phút xếp job cho tất cả symbols active
def loop():
    while True:
        with SessionLocal() as s:
            rows = s.execute(text("SELECT id, ticker FROM symbols WHERE active=1")).fetchall()
        for sid, tck in rows:
            # Ví dụ: chiến lược id=1, dùng ma trận '1D4hr' để đối chiếu (bạn có thể map động theo tf)
            q.enqueue('worker.jobs.full_pipeline', sid, 1, '1D4hr', job_timeout=180)
        time.sleep(60)

if __name__ == "__main__":
    loop()
