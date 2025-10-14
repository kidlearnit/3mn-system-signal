"""
HTMX API endpoints for dynamic content loading
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import os

logger = logging.getLogger(__name__)

htmx_bp = Blueprint('htmx_api', __name__, url_prefix='/api/htmx')

# Database connection
engine = None
SessionLocal = None

def _init_db():
    """Initialize database connection"""
    global engine, SessionLocal
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Database connection initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def get_session():
    """Get database session"""
    if SessionLocal is None:
        _init_db()
    return SessionLocal()

@htmx_bp.route('/symbols/stats')
def symbols_stats():
    """Get symbols statistics for HTMX loading"""
    try:
        with get_session() as s:
            # Get total symbols count
            total_symbols = s.execute(text("SELECT COUNT(*) FROM symbols")).scalar()
            
            # Get active symbols count
            active_symbols = s.execute(text("SELECT COUNT(*) FROM symbols WHERE active = 1")).scalar()
            
            # Get symbols by exchange
            exchange_stats = s.execute(text("""
                SELECT exchange, COUNT(*) as count 
                FROM symbols 
                WHERE active = 1 
                GROUP BY exchange 
                ORDER BY count DESC
            """)).fetchall()
            
            # Get symbols with signals count
            symbols_with_signals = s.execute(text("""
                SELECT COUNT(DISTINCT symbol_id) 
                FROM signals 
                WHERE symbol_id IN (SELECT id FROM symbols WHERE active = 1)
            """)).scalar()
            
            return render_template('components/symbols_stats.html', 
                                 total_symbols=total_symbols,
                                 active_symbols=active_symbols,
                                 symbols_with_signals=symbols_with_signals,
                                 exchange_stats=exchange_stats)
    except Exception as e:
        logger.error(f"Error getting symbols stats: {e}")
        return render_template('components/symbols_stats.html', 
                             total_symbols=0,
                             active_symbols=0,
                             symbols_with_signals=0,
                             exchange_stats=[])

@htmx_bp.route('/symbols/list')
def symbols_list():
    """Get symbols list for HTMX loading"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        exchange = request.args.get('exchange', '')
        status = request.args.get('status', '')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        with get_session() as s:
            # Build query
            where_conditions = []
            params = {}
            
            if search:
                where_conditions.append("ticker LIKE :search")
                params['search'] = f"%{search}%"
            
            if exchange:
                where_conditions.append("exchange = :exchange")
                params['exchange'] = exchange
            
            if status == 'active':
                where_conditions.append("active = 1")
            elif status == 'inactive':
                where_conditions.append("active = 0")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get symbols with signal counts
            query = f"""
                SELECT s.id, s.ticker, s.exchange, s.currency, s.active, s.created_at,
                       COUNT(sig.id) as signal_count
                FROM symbols s
                LEFT JOIN signals sig ON s.id = sig.symbol_id
                {where_clause}
                GROUP BY s.id, s.ticker, s.exchange, s.currency, s.active, s.created_at
                ORDER BY s.ticker ASC
                LIMIT %(limit)s OFFSET %(offset)s
            """
            
            params['limit'] = limit
            params['offset'] = offset
            
            symbols = s.execute(text(query), params).fetchall()
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) FROM symbols s {where_clause}
            """
            total_count = s.execute(text(count_query), params).scalar()
            
            return render_template('components/symbols_table.html', 
                                 symbols=symbols,
                                 total_count=total_count,
                                 limit=limit,
                                 offset=offset,
                                 search=search,
                                 exchange=exchange,
                                 status=status)
    except Exception as e:
        logger.error(f"Error getting symbols list: {e}")
        return render_template('components/symbols_table.html', 
                             symbols=[],
                             total_count=0,
                             limit=limit,
                             offset=0,
                             search=search,
                             exchange=exchange,
                             status=status)

@htmx_bp.route('/symbols/exchanges')
def symbols_exchanges():
    """Get available exchanges for dropdown"""
    try:
        with get_session() as s:
            exchanges = s.execute(text("""
                SELECT DISTINCT exchange 
                FROM symbols 
                WHERE exchange IS NOT NULL 
                ORDER BY exchange
            """)).fetchall()
            
            return render_template('components/exchanges_dropdown.html', 
                                 exchanges=exchanges)
    except Exception as e:
        logger.error(f"Error getting exchanges: {e}")
        return render_template('components/exchanges_dropdown.html', 
                             exchanges=[])

@htmx_bp.route('/signals/stats')
def signals_stats():
    """Get signals statistics for HTMX loading"""
    try:
        with get_session() as s:
            # Get total signals count
            total_signals = s.execute(text("SELECT COUNT(*) FROM signals")).scalar()
            
            # Get signals by type
            signal_types = s.execute(text("""
                SELECT signal_type, COUNT(*) as count 
                FROM signals 
                GROUP BY signal_type 
                ORDER BY count DESC
            """)).fetchall()
            
            # Get recent signals (last 24 hours)
            recent_signals = s.execute(text("""
                SELECT COUNT(*) 
                FROM signals 
                WHERE ts >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)).scalar()
            
            # Get signals by timeframe
            timeframe_stats = s.execute(text("""
                SELECT timeframe, COUNT(*) as count 
                FROM signals 
                GROUP BY timeframe 
                ORDER BY count DESC
            """)).fetchall()
            
            return render_template('components/signals_stats.html', 
                                 total_signals=total_signals,
                                 recent_signals=recent_signals,
                                 signal_types=signal_types,
                                 timeframe_stats=timeframe_stats)
    except Exception as e:
        logger.error(f"Error getting signals stats: {e}")
        return render_template('components/signals_stats.html', 
                             total_signals=0,
                             recent_signals=0,
                             signal_types=[],
                             timeframe_stats=[])

@htmx_bp.route('/signals/list')
def signals_list():
    """Get signals list for HTMX loading"""
    try:
        # Get query parameters
        symbol_id = request.args.get('symbol_id', '')
        timeframe = request.args.get('timeframe', '')
        signal_type = request.args.get('signal_type', '')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        with get_session() as s:
            # Build query
            where_conditions = []
            params = {}
            
            if symbol_id:
                where_conditions.append("s.symbol_id = :symbol_id")
                params['symbol_id'] = symbol_id
            
            if timeframe:
                where_conditions.append("s.timeframe = :timeframe")
                params['timeframe'] = timeframe
            
            if signal_type:
                where_conditions.append("s.signal_type = :signal_type")
                params['signal_type'] = signal_type
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get signals with symbol info
            query = f"""
                SELECT s.id, s.symbol_id, s.timeframe, s.ts, s.signal_type, s.details,
                       sym.ticker, sym.exchange, st.name as strategy_name
                FROM signals s
                JOIN symbols sym ON s.symbol_id = sym.id
                LEFT JOIN trade_strategies st ON s.strategy_id = st.id
                {where_clause}
                ORDER BY s.ts DESC
                LIMIT :limit OFFSET :offset
            """
            
            params['limit'] = limit
            params['offset'] = offset
            
            signals = s.execute(text(query), params).fetchall()
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(*) 
                FROM signals s
                JOIN symbols sym ON s.symbol_id = sym.id
                {where_clause}
            """
            total_count = s.execute(text(count_query), params).scalar()
            
            return render_template('components/signals_table.html', 
                                 signals=signals,
                                 total_count=total_count,
                                 limit=limit,
                                 offset=offset,
                                 symbol_id=symbol_id,
                                 timeframe=timeframe,
                                 signal_type=signal_type)
    except Exception as e:
        logger.error(f"Error getting signals list: {e}")
        return render_template('components/signals_table.html', 
                             signals=[],
                             total_count=0,
                             limit=limit,
                             offset=0,
                             symbol_id=symbol_id,
                             timeframe=timeframe,
                             signal_type=signal_type)
