from sqlalchemy import text
from ..db import SessionLocal

def load_threshold_rules(strategy_id:int, timeframe_name:str):
    sql = """
    SELECT i.name as indicator, z.name as zone, tv.comparison, tv.min_value, tv.max_value
    FROM threshold_values tv
    JOIN strategy_thresholds st ON st.id = tv.threshold_id
    JOIN timeframes tf ON tf.id = st.timeframe_id
    JOIN indicators i ON i.id = tv.indicator_id
    JOIN zones z ON z.id = tv.zone_id
    WHERE st.strategy_id=:sid AND tf.name=:tf
    ORDER BY FIELD(z.name,'igr','greed','bull','pos','neutral','neg','bear','fear','panic') DESC
    """
    with SessionLocal() as s:
        rows = s.execute(text(sql), {'sid': strategy_id, 'tf': timeframe_name}).mappings().all()
        return [dict(r) for r in rows]
