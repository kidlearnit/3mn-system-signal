import os
from sqlalchemy import text
from app.db import init_db

# Khởi tạo DB session
init_db(os.getenv("DATABASE_URL"))
from app.db import SessionLocal

# Chuẩn bị dữ liệu theo bảng bạn cung cấp (ví dụ rút gọn)
DATA = {
	'1D4hr': {
		'fmacd': {
		'igr': ('>=', 3.0), 'greed': ('>=', 2.2), 'bull': ('>=', 1.47), 'pos': ('>=', 1.0),
		'neutral': ('>=', 0.74), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -3.0)
		},
		'smacd': {
		'igr': ('>=', 2.2), 'greed': ('>=', 1.47), 'bull': ('>=', 1.0), 'pos': ('>=', 0.74),
		'neutral': ('>=', 0.47), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -2.2)
		},
		'bars': {
		'Hurricane': ('>=', 3.0), 'Storm': ('>=', 2.0), 'StrongWind': ('>=', 1.74), 'Windy': ('>=', 1.47), 'Neutral': ('>=', 1.0)
		}
	},
	'1D1hr': {
		'fmacd': {
			'igr': ('>=', 1.74), 'greed': ('>=', 1.0), 'bull': ('>=', 1.47), 'pos': ('>=', 0.74),
			'neutral': ('>=', 0.47), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -2.2)
		},
		'smacd': {
			'igr': ('>=', 1.0), 'greed': ('>=', 0.74), 'bull': ('>=', 0.74), 'pos': ('>=', 0.47),
			'neutral': ('>=', 0.33), 'neg': ('<', 0.0), 'bear': ('<', -0.47), 'fear': ('<', -1.0), 'panic': ('<', -1.47)
		},
		'bars': {
			'Hurricane': ('>=', 2.0), 'Storm': ('>=', 1.74), 'StrongWind': ('>=', 1.0), 'Windy': ('>=', 0.74), 'Neutral': ('>=', 0.47)
		}
	},
	'1D30Min': {
		'fmacd': {
			'igr': ('>=', 1.74), 'greed': ('>=', 1.0), 'bull': ('>=', 1.47), 'pos': ('>=', 0.74),
			'neutral': ('>=', 0.47), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -2.2)
		},
		'smacd': {
			'igr': ('>=', 1.0), 'greed': ('>=', 0.74), 'bull': ('>=', 0.74), 'pos': ('>=', 0.47),
			'neutral': ('>=', 0.33), 'neg': ('<', 0.0), 'bear': ('<', -0.47), 'fear': ('<', -1.0), 'panic': ('<', -1.47)
		},
		'bars': {
			'Hurricane': ('>=', 1.47), 'Storm': ('>=', 1.14), 'StrongWind': ('>=', 1.0), 'Windy': ('>=', 0.74), 'Neutral': ('>=', 0.47)
		}
	},
	'1D15Min': {
		'fmacd': {
			'igr': ('>=', 1.14), 'greed': ('>=', 0.74), 'bull': ('>=', 0.74), 'pos': ('>=', 0.47),
			'neutral': ('>=', 0.33), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -0.74)
		},
		'smacd': {
			'igr': ('>=', 0.74), 'greed': ('>=', 0.47), 'bull': ('>=', 0.47), 'pos': ('>=', 0.33),
			'neutral': ('>=', 0.22), 'neg': ('<', 0.0), 'bear': ('<', -0.33), 'fear': ('<', -0.47), 'panic': ('<', -0.47)
		},
		'bars': {
			'Hurricane': ('>=', 1.0), 'Storm': ('>=', 0.74), 'StrongWind': ('>=', 0.47), 'Windy': ('>=', 0.33), 'Neutral': ('>=', 0.22)
		}
	},
	'1D5Min': {
		'fmacd': {
			'igr': ('>=', 1.0), 'greed': ('>=', 0.74), 'bull': ('>=', 0.47), 'pos': ('>=', 0.33),
			'neutral': ('>=', 0.22), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -0.33)
		},
		'smacd': {
			'igr': ('>=', 0.74), 'greed': ('>=', 0.47), 'bull': ('>=', 0.33), 'pos': ('>=', 0.22),
			'neutral': ('>=', 0.17), 'neg': ('<', 0.0), 'bear': ('<', -0.22), 'fear': ('<', -0.47), 'panic': ('<', -0.47)
		},
		'bars': {
			'Hurricane': ('>=', 0.74), 'Storm': ('>=', 0.47), 'StrongWind': ('>=', 0.33), 'Windy': ('>=', 0.22), 'Neutral': ('>=', 0.17)
		}
	},
	'1D2Min': {
		'fmacd': {
			'igr': ('>=', 0.74), 'greed': ('>=', 0.33), 'bull': ('>=', 0.33), 'pos': ('>=', 0.22),
			'neutral': ('>=', 0.17), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -0.22)
		},
		'smacd': {
			'igr': ('>=', 0.47), 'greed': ('>=', 0.33), 'bull': ('>=', 0.22), 'pos': ('>=', 0.17),
			'neutral': ('>=', 0.11), 'neg': ('<', 0.0), 'bear': ('<', -0.17), 'fear': ('<', -0.33), 'panic': ('<', -0.33)
		},
		'bars': {
			'Hurricane': ('>=', 0.47), 'Storm': ('>=', 0.33), 'StrongWind': ('>=', 0.22), 'Windy': ('>=', 0.17), 'Neutral': ('>=', 0.11)
		}
	},
	'1D1Min': {
		'fmacd': {
			'igr': ('>=', 0.47), 'greed': ('>=', 0.33), 'bull': ('>=', 0.33), 'pos': ('>=', 0.22),
			'neutral': ('>=', 0.17), 'neg': ('<', 0.0), 'bear': ('<', -0.74), 'fear': ('<', -1.47), 'panic': ('<', -0.17)
		},
		'smacd': {
			'igr': ('>=', 0.33), 'greed': ('>=', 0.22), 'bull': ('>=', 0.17), 'pos': ('>=', 0.11),
			'neutral': ('>=', 0.07), 'neg': ('<', 0.0), 'bear': ('<', -0.11), 'fear': ('<', -0.22), 'panic': ('<', -0.22)
		},
		'bars': {
			'Hurricane': ('>=', 0.37), 'Storm': ('>=', 0.33), 'StrongWind': ('>=', 0.22), 'Windy': ('>=', 0.11), 'Neutral': ('>=', 0.07)
		}
	}
}

def get_or_create(s, table, name):
    row = s.execute(text(f"SELECT id FROM {table} WHERE name=:n"), {'n': name}).first()
    if row: return row[0]
    s.execute(text(f"INSERT INTO {table} (name) VALUES (:n)"), {'n': name})
    s.commit()
    return s.execute(text("SELECT LAST_INSERT_ID()")).scalar()

def main():
    with SessionLocal() as s:
        # base
        stg_id = get_or_create(s, 'trade_strategies', 'MACD Zone Strategy')
        for ind in ['fmacd','smacd','bars']:
            get_or_create(s, 'indicators', ind)
        for z in ['igr','greed','bull','pos','neutral','neg','bear','fear','panic','Hurricane','Storm','StrongWind','Windy','Neutral']:
            get_or_create(s, 'zones', z)
        for tf_name, content in DATA.items():
            tf_id = get_or_create(s, 'timeframes', tf_name)
            # upsert strategy_thresholds
            row = s.execute(text("""
              SELECT id FROM strategy_thresholds WHERE strategy_id=:sid AND timeframe_id=:tfid
            """), {'sid': stg_id, 'tfid': tf_id}).first()
            if row: th_id = row[0]
            else:
                s.execute(text("""
                  INSERT INTO strategy_thresholds (strategy_id, timeframe_id)
                  VALUES (:sid,:tfid)
                """), {'sid': stg_id, 'tfid': tf_id})
                s.commit()
                th_id = s.execute(text("SELECT LAST_INSERT_ID()")).scalar()

            # insert threshold_values
            for ind_name, zmap in content.items():
                ind_id = s.execute(text("SELECT id FROM indicators WHERE name=:n"), {'n': ind_name}).scalar()
                for zone_name, rule in zmap.items():
                    comp, val = rule[0], rule[1]
                    zone_id = s.execute(text("SELECT id FROM zones WHERE name=:n"), {'n': zone_name}).scalar()
                    s.execute(text("""
                    INSERT INTO threshold_values (threshold_id, indicator_id, zone_id, comparison, min_value)
                    VALUES (:th,:ind,:zone,:cmp,:val)
                    ON DUPLICATE KEY UPDATE comparison=:cmp, min_value=:val
                    """), {'th': th_id, 'ind': ind_id, 'zone': zone_id, 'cmp': comp, 'val': val})
            s.commit()
    print("Loaded thresholds.")

if __name__ == "__main__":
    main()
