"""
Strategy Management API Routes
API endpoints để quản lý chiến lược, cấu hình tham số chỉ báo, và theo dõi real-time
"""

from flask import Blueprint, request, jsonify, render_template
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import os
from datetime import datetime

# Database connection
engine = None
SessionLocal = None

def _init_db():
    """Initialize database connection"""
    global engine, SessionLocal
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return False
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return True
    except Exception as e:
        return False

def get_session():
    """Get database session"""
    if SessionLocal is None:
        _init_db()
    return SessionLocal()

strategy_mgmt_bp = Blueprint('strategy_mgmt', __name__)

# ==============================================
# STRATEGY CRUD OPERATIONS
# ==============================================

@strategy_mgmt_bp.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Lấy danh sách tất cả chiến lược"""
    try:
        with get_session() as session:
            # Lấy danh sách strategies
            strategies_query = text("""
                SELECT s.id, s.name, s.description, 
                       COUNT(st.id) as threshold_count,
                       COUNT(sig.id) as signal_count
                FROM trade_strategies s
                LEFT JOIN strategy_thresholds st ON s.id = st.strategy_id
                LEFT JOIN signals sig ON s.id = sig.strategy_id
                GROUP BY s.id, s.name, s.description
                ORDER BY s.name
            """)
            
            result = session.execute(strategies_query)
            strategies = []
            
            for row in result:
                strategies.append({
                    'id': row.id,
                    'name': row.name,
                    'description': row.description,
                    'threshold_count': row.threshold_count,
                    'signal_count': row.signal_count,
                    'active': True  # Mock active status
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategies': strategies,
                    'total': len(strategies)
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching strategies: {str(e)}'
        }), 500

# ==============================================
# THRESHOLD TEMPLATES & ZONES (for Workflow Builder)
# ==============================================

@strategy_mgmt_bp.route('/api/threshold/templates', methods=['GET'])
def get_threshold_templates():
    """Fetch threshold templates for a given strategy and market.
    Query params: strategy=MACD|SMA, market=VN|US (optional)
    Response: [{id, name}]
    """
    strategy = request.args.get('strategy', 'MACD').upper()
    market = request.args.get('market', 'VN').upper()

    # Fallback data if table not present or error occurs
    fallback = (
        [
            {'id': 'VN_DEFAULT', 'name': 'VN MACD Default'},
            {'id': 'VN_AGGRESSIVE', 'name': 'VN MACD Aggressive'}
        ] if strategy == 'MACD' else
        [
            {'id': 'VN_SMA_DEFAULT', 'name': 'VN SMA Default'},
            {'id': 'VN_SMA_TREND', 'name': 'VN SMA Trend Focus'}
        ]
    )

    try:
        with get_session() as session:
            # Try market_threshold_templates first (if exists in schema)
            try:
                query = text(
                    """
                    SELECT id, name
                    FROM market_threshold_templates
                    WHERE (market = :market OR :market = 'VN')
                    AND (strategy = :strategy OR strategy IS NULL)
                    ORDER BY created_at DESC
                    LIMIT 100
                    """
                )
                rows = session.execute(query, {'market': market, 'strategy': strategy}).fetchall()
                templates = [{'id': r.id, 'name': r.name} for r in rows]
                if templates:
                    return jsonify(templates)
            except Exception:
                # Table might not exist; ignore and use fallback/alternative
                pass

            # Alternative: trade_strategies as templates (name only)
            try:
                alt = text(
                    """
                    SELECT id, name
                    FROM trade_strategies
                    WHERE strategy_type = :stype
                    ORDER BY updated_at DESC
                    LIMIT 50
                    """
                )
                stype = 'MACD' if strategy == 'MACD' else 'SMA'
                rows = session.execute(alt, {'stype': stype}).fetchall()
                templates = [{'id': str(r.id), 'name': r.name} for r in rows]
                if templates:
                    return jsonify(templates)
            except Exception:
                pass

            # Fallback
            return jsonify(fallback)
    except Exception:
        return jsonify(fallback)


@strategy_mgmt_bp.route('/api/threshold/zones', methods=['GET'])
def get_threshold_zones():
    """Fetch zone templates for a given market.
    Query params: market=VN|US (optional)
    Response: [{id, name}]
    """
    market = request.args.get('market', 'VN').upper()
    fallback = [
        {'id': 'VN_ZONE_V1', 'name': 'VN Zone V1'},
        {'id': 'VN_ZONE_V2', 'name': 'VN Zone V2'}
    ]

    try:
        with get_session() as session:
            try:
                query = text(
                    """
                    SELECT id, name
                    FROM zones
                    WHERE (market = :market OR :market = 'VN')
                    ORDER BY name
                    LIMIT 200
                    """
                )
                rows = session.execute(query, {'market': market}).fetchall()
                zones = [{'id': r.id, 'name': r.name} for r in rows]
                if zones:
                    return jsonify(zones)
            except Exception:
                pass

            return jsonify(fallback)
    except Exception:
        return jsonify(fallback)


# ==============================================
# TEMPLATE VALUES (per timeframe) - GET/PUT
# ==============================================

@strategy_mgmt_bp.route('/api/threshold/template-values', methods=['GET'])
def get_template_values():
    """Get template values per timeframe for a strategy/template.
    Query: strategy=MACD|SMA, templateId=..., market=VN
    Response shape: { timeframes: [{ tf, params, zone_id? }] }
    """
    strategy = request.args.get('strategy', 'MACD').upper()
    template_id = request.args.get('templateId', '')
    market = request.args.get('market', 'VN').upper()

    # Fallback with 7TF defaults
    def _default_7tf_payload():
        if strategy == 'MACD':
            params = { 'fastPeriod': 12, 'slowPeriod': 26, 'signalPeriod': 9, 'minConfidence': 0.6 }
            return {
                'timeframes': [
                    {'tf': '1m', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '2m', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '5m', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '15m', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '30m', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '1h', 'params': params, 'zone_id': 'VN_ZONE_V1'},
                    {'tf': '4h', 'params': params, 'zone_id': 'VN_ZONE_V1'}
                ]
            }
        else:
            params = { 'periods': [18,36,48,144], 'tripleConfirmation': True, 'minConfirmation': 3, 'minConfidence': 0.5 }
            return {
                'timeframes': [
                    {'tf': '1m', 'params': params},
                    {'tf': '2m', 'params': params},
                    {'tf': '5m', 'params': params},
                    {'tf': '15m', 'params': params},
                    {'tf': '30m', 'params': params},
                    {'tf': '1h', 'params': params},
                    {'tf': '4h', 'params': params}
                ]
            }

    try:
        if not template_id:
            return jsonify(_default_7tf_payload())

        with get_session() as session:
            # Try to read from market_threshold_template_values if exists
            try:
                q = text(
                    """
                    SELECT tf.name AS tf, mtv.params_json AS params, z.name AS zone_name, z.id AS zone_id
                    FROM market_threshold_template_values mtv
                    JOIN timeframes tf ON tf.id = mtv.timeframe_id
                    LEFT JOIN zones z ON z.id = mtv.zone_id
                    WHERE mtv.template_id = :tid
                    ORDER BY tf.minutes
                    """
                )
                rows = session.execute(q, {'tid': template_id}).fetchall()
                if rows:
                    items = []
                    for r in rows:
                        try:
                            import json as _json
                            p = _json.loads(r.params) if r.params else {}
                        except Exception:
                            p = {}
                        items.append({'tf': r.tf, 'params': p, 'zone_id': r.zone_id})
                    return jsonify({'timeframes': items})
            except Exception:
                pass

            # Fallback
            return jsonify(_default_7tf_payload())
    except Exception:
        return jsonify(_default_7tf_payload())


@strategy_mgmt_bp.route('/api/threshold/template-values', methods=['PUT'])
def update_template_values():
    """Update template values per timeframe.
    Body: { strategy: 'MACD'|'SMA', templateId: '...', items: [{tf, params, zone_id?}] }
    """
    try:
        data = request.get_json() or {}
        strategy = (data.get('strategy') or 'MACD').upper()
        template_id = data.get('templateId')
        items = data.get('items') or []

        if not template_id or not items:
            return jsonify({'status': 'error', 'message': 'templateId and items are required'}), 400

        with get_session() as session:
            # Upsert into market_threshold_template_values if exists; otherwise accept and return ok
            try:
                for it in items:
                    tf = it.get('tf')
                    params = it.get('params') or {}
                    zone_id = it.get('zone_id')

                    # Resolve timeframe_id
                    tf_row = session.execute(text("SELECT id FROM timeframes WHERE name = :name"), {'name': tf}).fetchone()
                    if not tf_row:
                        continue
                    timeframe_id = tf_row.id

                    import json as _json
                    params_json = _json.dumps(params)

                    # Try update, if 0 then insert
                    upd = text(
                        """
                        UPDATE market_threshold_template_values
                        SET params_json = :params_json, zone_id = :zone_id
                        WHERE template_id = :template_id AND timeframe_id = :timeframe_id
                        """
                    )
                    res = session.execute(upd, {
                        'params_json': params_json,
                        'zone_id': zone_id,
                        'template_id': template_id,
                        'timeframe_id': timeframe_id
                    })
                    if res.rowcount == 0:
                        ins = text(
                            """
                            INSERT INTO market_threshold_template_values (template_id, timeframe_id, params_json, zone_id)
                            VALUES (:template_id, :timeframe_id, :params_json, :zone_id)
                            """
                        )
                        session.execute(ins, {
                            'template_id': template_id,
                            'timeframe_id': timeframe_id,
                            'params_json': params_json,
                            'zone_id': zone_id
                        })

                session.commit()
            except Exception:
                # If table not exist, just accept
                session.rollback()

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==============================================
# SEED: MACD ZONES TABLE TEMPLATE (7 TF) - POST
# ==============================================

@strategy_mgmt_bp.route('/api/threshold/seed-macd-zones', methods=['POST'])
def seed_macd_zones_template():
    """Seed a standard MACD zones template for 7 timeframes based on provided matrix.
    Body: { market: 'VN'|'US' }
    Creates template name: MACD_ZONES_V1_<market>
    """
    try:
        payload = request.get_json() or {}
        market = (payload.get('market') or request.args.get('market') or 'VN').upper()
        template_name = f"MACD_ZONES_V1_{market}"

        # 7 TF in system
        tf_order = ['4h','1h','30m','15m','5m','2m','1m']

        # Zone matrix (strings as given). Map to each TF.
        zone_rows = {
            '4h': {
                'FMACD': ['≥3.0','≥2.2','≥1.47','≥1.0','≥0.74','≥0.47','<0.0','<–0.74','<–1.47','<–3.0','<–2.2'],
                'SMACD': ['≥2.2','≥1.47','≥1.0','≥0.74','≥0.47','≥0.33','<0.0','<–0.47','<–1.0','<–2.2','<–1.47'],
                'BARS':  ['≥3.0','≥2.0','≥1.74','≥1.47','≥1.0']
            },
            '1h': {
                'FMACD': ['≥1.74','≥1.47','≥1.0','≥0.74','≥0.47','≥0.33','<0.0','<–0.74','<–1.47','<–2.2'],
                'SMACD': ['≥1.0','≥0.74','≥0.74','≥0.47','≥0.33','≥0.33','<0.0','<–0.47','<–1.0','<–1.47'],
                'BARS':  ['≥2.0','≥1.74','≥1.0','≥0.74','≥0.47']
            },
            '30m': {
                'FMACD': ['≥1.74','≥1.47','≥1.0','≥0.74','≥0.47','≥0.33','<0.0','<–0.74','<–1.47','<–2.2'],
                'SMACD': ['≥1.0','≥0.74','≥0.74','≥0.47','≥0.33','≥0.33','<0.0','<–0.47','<–1.0','<–1.47'],
                'BARS':  ['≥1.47','≥1.14','≥1.0','≥0.74','≥0.47']
            },
            '15m': {
                'FMACD': ['≥1.14','≥0.74','≥0.74','≥0.47','≥0.33','≥0.22','<0.0','<–0.47','<–0.74','<–1.47'],
                'SMACD': ['≥0.74','≥0.47','≥0.47','≥0.33','≥0.22','≥0.22','<0.0','<–0.33','<–0.47','<–0.74'],
                'BARS':  ['≥1.0','≥0.74','≥0.47','≥0.33','≥0.22']
            },
            '5m': {
                'FMACD': ['≥1.0','≥0.74','≥0.47','≥0.33','≥0.22','≥0.17','<0.0','<–0.33','<–0.74','<–1.0'],
                'SMACD': ['≥0.74','≥0.47','≥0.33','≥0.22','≥0.17','≥0.17','<0.0','<–0.22','<–0.47','<–0.74'],
                'BARS':  ['≥0.74','≥0.47','≥0.47','≥0.33','≥0.17']
            },
            '2m': {
                'FMACD': ['≥0.74','≥0.33','≥0.33','≥0.22','≥0.17','≥0.11','<0.0','<–0.22','<–0.47','<–0.74'],
                'SMACD': ['≥0.47','≥0.33','≥0.22','≥0.17','≥0.11','≥0.11','<0.0','<–0.17','<–0.33','<–0.47'],
                'BARS':  ['≥0.47','≥0.33','≥0.33','≥0.22','≥0.11']
            },
            '1m': {
                'FMACD': ['≥0.47','≥0.33','≥0.22','≥0.17','≥0.11','≥0.07','<0.0','<–0.17','<–0.33','<–0.47'],
                'SMACD': ['≥0.33','≥0.22','≥0.17','≥0.11','≥0.07','≥0.07','<0.0','<–0.11','<–0.22','<–0.33'],
                'BARS':  ['≥0.37','≥0.33','≥0.22','≥0.11','≥0.07']
            }
        }

        with get_session() as session:
            import json as _json
            # Create template
            template_id = None
            try:
                ins_template = text("""
                    INSERT INTO market_threshold_templates (id, name, market, strategy)
                    VALUES (UUID(), :name, :market, 'MACD')
                """)
                session.execute(ins_template, {'name': template_name, 'market': market})
                # Retrieve id
                sel = text("SELECT id FROM market_threshold_templates WHERE name=:name ORDER BY created_at DESC LIMIT 1")
                template_id = session.execute(sel, {'name': template_name}).scalar()
            except Exception:
                # Fallback: use name as id
                template_id = template_name

            # Upsert zones list (names only if table minimal)
            zone_names = ['Ignorance','Greed','Bull','Positive','Neutral','Negative','Bear','Fear','Panic']
            zone_map = {}
            for zn in zone_names:
                try:
                    zsel = text("SELECT id FROM zones WHERE name=:n AND (market=:m OR :m='VN') LIMIT 1")
                    zid = session.execute(zsel, {'n': zn, 'm': market}).scalar()
                    if not zid:
                        zins = text("INSERT INTO zones (id, name, market) VALUES (UUID(), :n, :m)")
                        session.execute(zins, {'n': zn, 'm': market})
                        zid = session.execute(zsel, {'n': zn, 'm': market}).scalar()
                    zone_map[zn] = zid
                except Exception:
                    zone_map[zn] = zn

            # Insert per-timeframe params_json with full row
            for tf in tf_order:
                try:
                    tf_row = session.execute(text("SELECT id FROM timeframes WHERE name=:name"), {'name': tf}).scalar()
                    if not tf_row:
                        # create timeframe if missing
                        try:
                            session.execute(text("INSERT INTO timeframes (name, description, minutes, is_active) VALUES (:n, :d, :min, 1)"), {
                                'n': tf, 'd': f'{tf} timeframe', 'min': 1 if tf=='1m' else (2 if tf=='2m' else (5 if tf=='5m' else (15 if tf=='15m' else (30 if tf=='30m' else (60 if tf=='1h' else 240)))))
                            })
                            tf_row = session.execute(text("SELECT id FROM timeframes WHERE name=:name"), {'name': tf}).scalar()
                        except Exception:
                            pass
                    params_json = _json.dumps({'zone_thresholds': zone_rows.get(tf, {})})
                    # Upsert template values
                    upd = text("""
                        UPDATE market_threshold_template_values
                        SET params_json=:params, zone_id=NULL
                        WHERE template_id=:tid AND timeframe_id=:tfid
                    """)
                    res = session.execute(upd, {'params': params_json, 'tid': template_id, 'tfid': tf_row})
                    if res.rowcount == 0:
                        ins = text("""
                            INSERT INTO market_threshold_template_values (template_id, timeframe_id, params_json, zone_id)
                            VALUES (:tid, :tfid, :params, NULL)
                        """)
                        session.execute(ins, {'tid': template_id, 'tfid': tf_row, 'params': params_json})
                except Exception:
                    continue

            session.commit()

        return jsonify({'status': 'success', 'template': template_name})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>', methods=['GET'])
def get_strategy_detail(strategy_id):
    """Lấy chi tiết chiến lược"""
    try:
        with get_session() as session:
            # Lấy thông tin strategy
            strategy_query = text("""
                SELECT s.id, s.name, s.description
                FROM trade_strategies s
                WHERE s.id = :strategy_id
            """)
            
            result = session.execute(strategy_query, {'strategy_id': strategy_id})
            strategy_row = result.fetchone()
            
            if not strategy_row:
                return jsonify({
                    'status': 'error',
                    'message': 'Strategy not found'
                }), 404
            
            # Lấy thresholds
            thresholds_query = text("""
                SELECT st.id, tf.name as timeframe, i.name as indicator, z.name as zone,
                       tv.comparison, tv.min_value, tv.max_value
                FROM strategy_thresholds st
                JOIN timeframes tf ON st.timeframe_id = tf.id
                JOIN threshold_values tv ON st.id = tv.threshold_id
                JOIN indicators i ON tv.indicator_id = i.id
                JOIN zones z ON tv.zone_id = z.id
                WHERE st.strategy_id = :strategy_id
                ORDER BY tf.name, i.name
            """)
            
            result = session.execute(thresholds_query, {'strategy_id': strategy_id})
            thresholds = []
            
            for row in result:
                thresholds.append({
                    'id': row.id,
                    'timeframe': row.timeframe,
                    'indicator': row.indicator,
                    'zone': row.zone,
                    'comparison': row.comparison,
                    'min_value': float(row.min_value) if row.min_value else None,
                    'max_value': float(row.max_value) if row.max_value else None
                })
            
            # Lấy signals gần đây
            signals_query = text("""
                SELECT sig.id, sym.ticker, sig.timeframe, sig.ts, sig.signal_type, sig.details
                FROM signals sig
                JOIN symbols sym ON sig.symbol_id = sym.id
                WHERE sig.strategy_id = :strategy_id
                ORDER BY sig.ts DESC
                LIMIT 10
            """)
            
            result = session.execute(signals_query, {'strategy_id': strategy_id})
            recent_signals = []
            
            for row in result:
                recent_signals.append({
                    'id': row.id,
                    'symbol': row.ticker,
                    'timeframe': row.timeframe,
                    'timestamp': row.ts.isoformat(),
                    'signal_type': row.signal_type,
                    'details': json.loads(row.details) if row.details else {}
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategy': {
                        'id': strategy_row.id,
                        'name': strategy_row.name,
                        'description': strategy_row.description,
                        'thresholds': thresholds,
                        'recent_signals': recent_signals
                    }
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching strategy detail: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/strategies', methods=['POST'])
def create_strategy():
    """Tạo chiến lược mới"""
    try:
        data = request.get_json()
        
        with get_session() as session:
            # Tạo strategy mới
            strategy_query = text("""
                INSERT INTO trade_strategies (name, description)
                VALUES (:name, :description)
            """)
            
            result = session.execute(strategy_query, {
                'name': data['name'],
                'description': data.get('description', '')
            })
            
            strategy_id = result.lastrowid
            
            # Tạo thresholds nếu có
            if 'thresholds' in data:
                for threshold in data['thresholds']:
                    # Tạo strategy_threshold
                    threshold_query = text("""
                        INSERT INTO strategy_thresholds (strategy_id, timeframe_id)
                        VALUES (:strategy_id, (SELECT id FROM timeframes WHERE name = :timeframe))
                    """)
                    
                    session.execute(threshold_query, {
                        'strategy_id': strategy_id,
                        'timeframe': threshold['timeframe']
                    })
                    
                    threshold_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    
                    # Tạo threshold_values
                    for value in threshold['values']:
                        value_query = text("""
                            INSERT INTO threshold_values 
                            (threshold_id, indicator_id, zone_id, comparison, min_value, max_value)
                            VALUES (
                                :threshold_id,
                                (SELECT id FROM indicators WHERE name = :indicator),
                                (SELECT id FROM zones WHERE name = :zone),
                                :comparison, :min_value, :max_value
                            )
                        """)
                        
                        session.execute(value_query, {
                            'threshold_id': threshold_id,
                            'indicator': value['indicator'],
                            'zone': value['zone'],
                            'comparison': value['comparison'],
                            'min_value': value.get('min_value'),
                            'max_value': value.get('max_value')
                        })
            
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategy_id': strategy_id,
                    'message': 'Strategy created successfully'
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error creating strategy: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>', methods=['PUT'])
def update_strategy(strategy_id):
    """Cập nhật chiến lược"""
    try:
        data = request.get_json()
        
        with get_session() as session:
            # Cập nhật thông tin strategy
            update_query = text("""
                UPDATE trade_strategies 
                SET name = :name, description = :description
                WHERE id = :strategy_id
            """)
            
            session.execute(update_query, {
                'strategy_id': strategy_id,
                'name': data['name'],
                'description': data.get('description', '')
            })
            
            # Xóa thresholds cũ và tạo mới
            if 'thresholds' in data:
                # Xóa thresholds cũ
                delete_query = text("""
                    DELETE FROM strategy_thresholds WHERE strategy_id = :strategy_id
                """)
                session.execute(delete_query, {'strategy_id': strategy_id})
                
                # Tạo thresholds mới
                for threshold in data['thresholds']:
                    threshold_query = text("""
                        INSERT INTO strategy_thresholds (strategy_id, timeframe_id)
                        VALUES (:strategy_id, (SELECT id FROM timeframes WHERE name = :timeframe))
                    """)
                    
                    session.execute(threshold_query, {
                        'strategy_id': strategy_id,
                        'timeframe': threshold['timeframe']
                    })
                    
                    threshold_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    
                    for value in threshold['values']:
                        value_query = text("""
                            INSERT INTO threshold_values 
                            (threshold_id, indicator_id, zone_id, comparison, min_value, max_value)
                            VALUES (
                                :threshold_id,
                                (SELECT id FROM indicators WHERE name = :indicator),
                                (SELECT id FROM zones WHERE name = :zone),
                                :comparison, :min_value, :max_value
                            )
                        """)
                        
                        session.execute(value_query, {
                            'threshold_id': threshold_id,
                            'indicator': value['indicator'],
                            'zone': value['zone'],
                            'comparison': value['comparison'],
                            'min_value': value.get('min_value'),
                            'max_value': value.get('max_value')
                        })
            
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'Strategy updated successfully'
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating strategy: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    """Xóa chiến lược"""
    try:
        with get_session() as session:
            # Xóa strategy (cascade sẽ xóa các bảng liên quan)
            delete_query = text("""
                DELETE FROM trade_strategies WHERE id = :strategy_id
            """)
            
            result = session.execute(delete_query, {'strategy_id': strategy_id})
            session.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'status': 'error',
                    'message': 'Strategy not found'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'Strategy deleted successfully'
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error deleting strategy: {str(e)}'
        }), 500

# ==============================================
# INDICATOR CONFIGURATION
# ==============================================

@strategy_mgmt_bp.route('/api/indicators', methods=['GET'])
def get_indicators():
    """Lấy danh sách các chỉ báo có sẵn"""
    try:
        # Mock data for now
        indicators = [
            {'id': 1, 'name': 'MACD'},
            {'id': 2, 'name': 'RSI'},
            {'id': 3, 'name': 'Bollinger Bands'},
            {'id': 4, 'name': 'SMA'},
            {'id': 5, 'name': 'EMA'}
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'indicators': indicators
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching indicators: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/indicators/<indicator_name>/values', methods=['GET'])
def get_indicator_values(indicator_name):
    """Lấy giá trị chỉ báo real-time cho symbol"""
    symbol = request.args.get('symbol', 'AAPL')
    timeframe = request.args.get('timeframe', '5m')
    
    try:
        with get_session() as session:
            if indicator_name.upper() == 'MACD':
                # Lấy MACD values
                macd_query = text("""
                    SELECT m.ts, m.macd, m.macd_signal, m.hist
                    FROM indicators_macd m
                    JOIN symbols s ON m.symbol_id = s.id
                    WHERE s.ticker = :symbol AND m.timeframe = :timeframe
                    ORDER BY m.ts DESC
                    LIMIT 1
                """)
                
                result = session.execute(macd_query, {
                    'symbol': symbol,
                    'timeframe': timeframe
                })
                
                row = result.fetchone()
                if row:
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'indicator': 'MACD',
                            'timestamp': row.ts.isoformat(),
                            'values': {
                                'macd': float(row.macd),
                                'macd_signal': float(row.macd_signal),
                                'histogram': float(row.hist)
                            }
                        }
                    })
            
            elif indicator_name.upper() == 'BARS':
                # Lấy Bars values
                bars_query = text("""
                    SELECT b.ts, b.bars
                    FROM indicators_bars b
                    JOIN symbols s ON b.symbol_id = s.id
                    WHERE s.ticker = :symbol AND b.timeframe = :timeframe
                    ORDER BY b.ts DESC
                    LIMIT 1
                """)
                
                result = session.execute(bars_query, {
                    'symbol': symbol,
                    'timeframe': timeframe
                })
                
                row = result.fetchone()
                if row:
                    return jsonify({
                        'status': 'success',
                        'data': {
                            'indicator': 'BARS',
                            'timestamp': row.ts.isoformat(),
                            'values': {
                                'bars': float(row.bars)
                            }
                        }
                    })
            
            return jsonify({
                'status': 'error',
                'message': f'Indicator {indicator_name} not found or no data available'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching indicator values: {str(e)}'
        }), 500

# ==============================================
# LIVE MONITORING & PARAMETER UPDATES
# ==============================================

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>/monitor', methods=['GET'])
def get_strategy_monitoring(strategy_id):
    """Lấy dữ liệu monitoring real-time cho chiến lược"""
    symbol = request.args.get('symbol', 'AAPL')
    
    try:
        with get_session() as session:
            # Lấy thông tin strategy
            strategy_query = text("""
                SELECT s.name, s.description
                FROM trade_strategies s
                WHERE s.id = :strategy_id
            """)
            
            result = session.execute(strategy_query, {'strategy_id': strategy_id})
            strategy_row = result.fetchone()
            
            if not strategy_row:
                return jsonify({
                    'status': 'error',
                    'message': 'Strategy not found'
                }), 404
            
            # Lấy thresholds
            thresholds_query = text("""
                SELECT tf.name as timeframe, i.name as indicator, z.name as zone,
                       tv.comparison, tv.min_value, tv.max_value
                FROM strategy_thresholds st
                JOIN timeframes tf ON st.timeframe_id = tf.id
                JOIN threshold_values tv ON st.id = tv.threshold_id
                JOIN indicators i ON tv.indicator_id = i.id
                JOIN zones z ON tv.zone_id = z.id
                WHERE st.strategy_id = :strategy_id
                ORDER BY tf.name, i.name
            """)
            
            result = session.execute(thresholds_query, {'strategy_id': strategy_id})
            thresholds = []
            
            for row in result:
                thresholds.append({
                    'timeframe': row.timeframe,
                    'indicator': row.indicator,
                    'zone': row.zone,
                    'comparison': row.comparison,
                    'min_value': float(row.min_value) if row.min_value else None,
                    'max_value': float(row.max_value) if row.max_value else None
                })
            
            # Lấy giá trị chỉ báo hiện tại
            current_values = {}
            timeframes = ['1m', '5m', '15m', '1h', '1D']
            
            for tf in timeframes:
                # MACD values
                macd_query = text("""
                    SELECT m.macd, m.macd_signal, m.hist
                    FROM indicators_macd m
                    JOIN symbols s ON m.symbol_id = s.id
                    WHERE s.ticker = :symbol AND m.timeframe = :timeframe
                    ORDER BY m.ts DESC
                    LIMIT 1
                """)
                
                result = session.execute(macd_query, {
                    'symbol': symbol,
                    'timeframe': tf
                })
                
                row = result.fetchone()
                if row:
                    current_values[tf] = {
                        'MACD': {
                            'macd': float(row.macd),
                            'macd_signal': float(row.macd_signal),
                            'histogram': float(row.hist)
                        }
                    }
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategy': {
                        'id': strategy_id,
                        'name': strategy_row.name,
                        'description': strategy_row.description
                    },
                    'thresholds': thresholds,
                    'current_values': current_values,
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error fetching monitoring data: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>/update-parameters', methods=['POST'])
def update_strategy_parameters(strategy_id):
    """Cập nhật tham số chiến lược real-time"""
    try:
        data = request.get_json()
        
        with get_session() as session:
            # Cập nhật thresholds
            if 'thresholds' in data:
                for threshold in data['thresholds']:
                    update_query = text("""
                        UPDATE threshold_values tv
                        JOIN strategy_thresholds st ON tv.threshold_id = st.id
                        JOIN timeframes tf ON st.timeframe_id = tf.id
                        JOIN indicators i ON tv.indicator_id = i.id
                        JOIN zones z ON tv.zone_id = z.id
                        SET tv.min_value = :min_value, tv.max_value = :max_value, tv.comparison = :comparison
                        WHERE st.strategy_id = :strategy_id 
                        AND tf.name = :timeframe 
                        AND i.name = :indicator 
                        AND z.name = :zone
                    """)
                    
                    session.execute(update_query, {
                        'strategy_id': strategy_id,
                        'timeframe': threshold['timeframe'],
                        'indicator': threshold['indicator'],
                        'zone': threshold['zone'],
                        'min_value': threshold.get('min_value'),
                        'max_value': threshold.get('max_value'),
                        'comparison': threshold.get('comparison', '>=')
                    })
            
            session.commit()
            
            return jsonify({
                'status': 'success',
                'data': {
                    'message': 'Parameters updated successfully',
                    'timestamp': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error updating parameters: {str(e)}'
        }), 500

# ==============================================
# STRATEGY TESTING & BACKTESTING
# ==============================================

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>/test', methods=['POST'])
def test_strategy(strategy_id):
    """Test chiến lược với dữ liệu hiện tại"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL')
        
        with get_session() as session:
            # Lấy thresholds
            thresholds_query = text("""
                SELECT tf.name as timeframe, i.name as indicator, z.name as zone,
                       tv.comparison, tv.min_value, tv.max_value
                FROM strategy_thresholds st
                JOIN timeframes tf ON st.timeframe_id = tf.id
                JOIN threshold_values tv ON st.id = tv.threshold_id
                JOIN indicators i ON tv.indicator_id = i.id
                JOIN zones z ON tv.zone_id = z.id
                WHERE st.strategy_id = :strategy_id
            """)
            
            result = session.execute(thresholds_query, {'strategy_id': strategy_id})
            thresholds = []
            
            for row in result:
                thresholds.append({
                    'timeframe': row.timeframe,
                    'indicator': row.indicator,
                    'zone': row.zone,
                    'comparison': row.comparison,
                    'min_value': float(row.min_value) if row.min_value else None,
                    'max_value': float(row.max_value) if row.max_value else None
                })
            
            # Test logic (simplified)
            test_results = []
            for threshold in thresholds:
                # Mock test result
                test_results.append({
                    'timeframe': threshold['timeframe'],
                    'indicator': threshold['indicator'],
                    'zone': threshold['zone'],
                    'condition_met': True,  # Mock result
                    'current_value': 1.5,   # Mock current value
                    'threshold_value': threshold['min_value'],
                    'signal': 'BUY' if threshold['zone'] == 'Bull' else 'SELL'
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'strategy_id': strategy_id,
                    'symbol': symbol,
                    'test_results': test_results,
                    'overall_signal': 'BUY',  # Mock overall signal
                    'confidence': 85,  # Mock confidence
                    'timestamp': datetime.now().isoformat()
                }
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error testing strategy: {str(e)}'
        }), 500

@strategy_mgmt_bp.route('/api/strategies/<int:strategy_id>/backtest', methods=['POST'])
def backtest_strategy(strategy_id):
    """Chạy backtest cho chiến lược"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL')
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-12-31')
        
        # Mock backtest results
        backtest_results = {
            'strategy_id': strategy_id,
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'total_return': 12.5,
            'win_rate': 85.0,
            'sharpe_ratio': 1.45,
            'max_drawdown': -5.2,
            'total_trades': 24,
            'winning_trades': 20,
            'losing_trades': 4,
            'avg_win': 2.1,
            'avg_loss': -1.8,
            'profit_factor': 2.33,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': backtest_results
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error running backtest: {str(e)}'
        }), 500

# ==============================================
# UI ROUTES
# ==============================================

@strategy_mgmt_bp.route('/symbol-strategy-config')
def symbol_strategy_config():
    """Hiển thị màn hình cài đặt chiến lược cho từng symbol"""
    return render_template('pages/symbol_strategy_config.html')
