-- =====================================================
-- DATABASE MIGRATION SCRIPT
-- Gộp tất cả schema, tables, views vào 1 file duy nhất
-- =====================================================
-- =====================================================
-- 1. MAIN SCHEMA (từ schema.sql)
-- =====================================================
-- Symbols
CREATE TABLE IF NOT EXISTS symbols (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    exchange VARCHAR(20) NOT NULL,
    currency VARCHAR(10) DEFAULT 'VND',
    market_type ENUM('US', 'VN', 'GLOBAL') DEFAULT 'GLOBAL',
    active TINYINT(1) DEFAULT 1,
    INDEX idx_market_type (market_type)
);

-- 1m candles
CREATE TABLE IF NOT EXISTS candles_1m (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    ts TIMESTAMP NOT NULL,
    open DECIMAL(18, 6) NOT NULL,
    high DECIMAL(18, 6) NOT NULL,
    low DECIMAL(18, 6) NOT NULL,
    close DECIMAL(18, 6) NOT NULL,
    volume DECIMAL(20, 2),
    UNIQUE KEY uniq_symbol_ts (symbol_id, ts),
    INDEX idx_symbol_ts (symbol_id, ts),
    CONSTRAINT fk_c1m_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Aggregated candles (multi-timeframe)
CREATE TABLE IF NOT EXISTS candles_tf (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    ts TIMESTAMP NOT NULL,
    open DECIMAL(18, 6) NOT NULL,
    high DECIMAL(18, 6) NOT NULL,
    low DECIMAL(18, 6) NOT NULL,
    close DECIMAL(18, 6) NOT NULL,
    volume DECIMAL(20, 2),
    UNIQUE KEY uniq_symbol_tf_ts (symbol_id, timeframe, ts),
    INDEX idx_symbol_tf_ts (symbol_id, timeframe, ts),
    CONSTRAINT fk_ctf_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Indicators MACD
CREATE TABLE IF NOT EXISTS indicators_macd (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    ts TIMESTAMP NOT NULL,
    macd DECIMAL(18, 6) NOT NULL,
    macd_signal DECIMAL(18, 6) NOT NULL,
    macd_histogram DECIMAL(18, 6) NOT NULL,
    UNIQUE KEY uniq_symbol_tf_ts (symbol_id, timeframe, ts),
    INDEX idx_symbol_tf_ts (symbol_id, timeframe, ts),
    CONSTRAINT fk_imacd_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Signals
CREATE TABLE IF NOT EXISTS signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    ts TIMESTAMP NOT NULL,
    strategy_id INT DEFAULT 1,
    signal_type ENUM('BUY', 'SELL', 'HOLD') NOT NULL,
    strength DECIMAL(5, 2) DEFAULT 1.0 COMMENT 'Signal strength: 1.0=normal, >1.0=strong, <1.0=weak',
    confidence DECIMAL(5, 2) DEFAULT 0.5 COMMENT 'Confidence score: 0.0-1.0',
    expires_at TIMESTAMP NULL COMMENT 'Signal expiration time (NULL = never expires)',
    source ENUM('auto', 'manual', 'backtest') DEFAULT 'auto' COMMENT 'Signal source type',
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active' COMMENT 'Signal status',
    priority TINYINT DEFAULT 3 COMMENT 'Signal priority: 1-5 (5=highest)',
    details JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_signal (
        symbol_id,
        timeframe,
        ts,
        strategy_id,
        signal_type
    ),
    INDEX idx_symbol_tf_ts (symbol_id, timeframe, ts),
    INDEX idx_signals_type_ts (signal_type, ts),
    INDEX idx_signals_strategy_ts (strategy_id, ts),
    CONSTRAINT fk_signals_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Timeframes
CREATE TABLE IF NOT EXISTS timeframes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,
    description VARCHAR(100),
    minutes INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Trade Strategies
CREATE TABLE IF NOT EXISTS trade_strategies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type ENUM('MACD', 'SMA', 'RSI', 'BOLLINGER') DEFAULT 'MACD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Workflows table for workflow builder
CREATE TABLE IF NOT EXISTS workflows (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    nodes JSON NOT NULL,
    connections JSON NOT NULL,
    properties JSON,
    metadata JSON,
    status ENUM('active', 'inactive', 'draft') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflow_status (status),
    INDEX idx_workflow_created (created_at)
);

-- MACD Multi-TF Signals table (for new unanimous logic)
CREATE TABLE IF NOT EXISTS macd_multi_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    market_type ENUM('US', 'VN', 'GLOBAL') NOT NULL,
    signal_type ENUM('BULL', 'BEAR', 'NEUTRAL') NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    strength DECIMAL(18, 6) NOT NULL,
    unanimous BOOLEAN NOT NULL DEFAULT FALSE,
    timeframe_results JSON NOT NULL,
    overall_signal JSON NOT NULL,
    fast_period INT NOT NULL,
    slow_period INT NOT NULL,
    signal_period INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_macd_multi_symbol (symbol_id),
    INDEX idx_macd_multi_exchange (exchange),
    INDEX idx_macd_multi_market (market_type),
    INDEX idx_macd_multi_signal (signal_type),
    INDEX idx_macd_multi_unanimous (unanimous),
    INDEX idx_macd_multi_created (created_at),
    CONSTRAINT fk_macd_multi_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Workflow Runs (execution tracking)
CREATE TABLE IF NOT EXISTS workflow_runs (
    run_id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    status ENUM('running', 'success', 'error', 'stopped') NOT NULL DEFAULT 'running',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    duration VARCHAR(32) NULL,
    meta JSON NULL,
    INDEX idx_runs_workflow (workflow_id),
    INDEX idx_runs_status (status),
    INDEX idx_runs_started (started_at),
    CONSTRAINT fk_runs_workflow FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

-- =====================================================
-- 2. SMA SYSTEM (từ sma_schema.sql)
-- =====================================================
-- Table for SMA indicators data
CREATE TABLE IF NOT EXISTS indicators_sma (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    ts TIMESTAMP NOT NULL,
    -- Price data
    close DECIMAL(18, 6) NOT NULL,
    high DECIMAL(18, 6),
    low DECIMAL(18, 6),
    volume BIGINT,
    -- SMA values
    m1 DECIMAL(18, 6),
    -- SMA 18
    m2 DECIMAL(18, 6),
    -- SMA 36
    m3 DECIMAL(18, 6),
    -- SMA 48
    ma144 DECIMAL(18, 6),
    -- SMA 144
    avg_m1_m2_m3 DECIMAL(18, 6),
    -- (M1+M2+M3)/3
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_symbol_timeframe_ts (symbol_id, timeframe, ts),
    INDEX idx_symbol_timeframe (symbol_id, timeframe),
    INDEX idx_ts (ts),
    -- Foreign key
    FOREIGN KEY (symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
);

-- Table for SMA signals
CREATE TABLE IF NOT EXISTS sma_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    -- Signal data
    signal_type VARCHAR(50) NOT NULL,
    signal_direction VARCHAR(10) NOT NULL,
    signal_strength DECIMAL(5, 2) NOT NULL,
    -- Price and MA data
    current_price DECIMAL(18, 8) NOT NULL,
    ma18 DECIMAL(18, 8),
    ma36 DECIMAL(18, 8),
    ma48 DECIMAL(18, 8),
    ma144 DECIMAL(18, 8),
    avg_ma DECIMAL(18, 8),
    -- Status
    is_sent_telegram TINYINT(1) DEFAULT 0,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_symbol_timeframe_ts (symbol_id, timeframe, timestamp),
    INDEX idx_signal_type (signal_type),
    INDEX idx_signal_direction (signal_direction),
    INDEX idx_ts (timestamp),
    -- Foreign key
    FOREIGN KEY (symbol_id) REFERENCES symbols(id) ON DELETE CASCADE
);

-- =====================================================
-- 3. SYMBOL THRESHOLDS SYSTEM (từ create_symbol_thresholds_schema.sql)
-- =====================================================
-- Bảng lưu trữ thresholds riêng cho từng cổ phiếu
CREATE TABLE IF NOT EXISTS symbol_thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    market_type ENUM('US', 'VN', 'GLOBAL') NOT NULL DEFAULT 'GLOBAL',
    strategy_name VARCHAR(100) NOT NULL DEFAULT 'MACD Zone Strategy',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_strategy (symbol_id, strategy_name),
    FOREIGN KEY (symbol_id) REFERENCES symbols(id) ON DELETE CASCADE,
    INDEX idx_symbol_id (symbol_id),
    INDEX idx_market_type (market_type),
    INDEX idx_is_active (is_active)
);

-- Bảng lưu trữ chi tiết thresholds cho từng symbol
CREATE TABLE IF NOT EXISTS symbol_threshold_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_threshold_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    indicator ENUM('fmacd', 'smacd', 'bars') NOT NULL,
    zone ENUM(
        'igr',
        'greed',
        'bull',
        'pos',
        'neutral',
        'neg',
        'bear',
        'fear',
        'panic',
        'Hurricane',
        'Storm',
        'StrongWind',
        'Windy',
        'Neutral'
    ) NOT NULL,
    comparison ENUM('>', '>=', '<', '<=', 'between') NOT NULL DEFAULT '>=',
    min_value DECIMAL(18, 6) DEFAULT NULL,
    max_value DECIMAL(18, 6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_symbol_threshold (symbol_threshold_id, timeframe, indicator, zone),
    FOREIGN KEY (symbol_threshold_id) REFERENCES symbol_thresholds(id) ON DELETE CASCADE,
    INDEX idx_timeframe (timeframe),
    INDEX idx_indicator (indicator),
    INDEX idx_zone (zone)
);

-- Bảng lưu trữ template thresholds cho từng thị trường
CREATE TABLE IF NOT EXISTS market_threshold_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_type ENUM('US', 'VN', 'GLOBAL') NOT NULL,
    strategy_name VARCHAR(100) NOT NULL DEFAULT 'MACD Zone Strategy',
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_market_strategy (market_type, strategy_name),
    INDEX idx_market_type (market_type),
    INDEX idx_is_default (is_default)
);

-- Bảng lưu trữ chi tiết template thresholds
CREATE TABLE IF NOT EXISTS market_threshold_template_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    indicator ENUM('fmacd', 'smacd', 'bars') NOT NULL,
    zone ENUM(
        'igr',
        'greed',
        'bull',
        'pos',
        'neutral',
        'neg',
        'bear',
        'fear',
        'panic',
        'Hurricane',
        'Storm',
        'StrongWind',
        'Windy',
        'Neutral'
    ) NOT NULL,
    comparison ENUM('>', '>=', '<', '<=', 'between') NOT NULL DEFAULT '>=',
    min_value DECIMAL(18, 6) DEFAULT NULL,
    max_value DECIMAL(18, 6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_template_threshold (template_id, timeframe, indicator, zone),
    FOREIGN KEY (template_id) REFERENCES market_threshold_templates(id) ON DELETE CASCADE,
    INDEX idx_timeframe (timeframe),
    INDEX idx_indicator (indicator),
    INDEX idx_zone (zone)
);

-- =====================================================
-- 3. HYBRID SIGNALS TABLE
-- =====================================================
-- Table for hybrid signals (SMA + MACD combination)
CREATE TABLE IF NOT EXISTS hybrid_signals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    hybrid_signal ENUM(
        'strong_buy',
        'buy',
        'weak_buy',
        'neutral',
        'weak_sell',
        'sell',
        'strong_sell'
    ) NOT NULL,
    hybrid_direction ENUM('BUY', 'SELL', 'NEUTRAL') NOT NULL,
    hybrid_strength DECIMAL(5, 2) DEFAULT 0.0 COMMENT 'Signal strength: 0.0-1.0',
    confidence DECIMAL(5, 2) DEFAULT 0.0 COMMENT 'Confidence score: 0.0-1.0',
    sma_signal JSON COMMENT 'SMA signal details',
    macd_signal JSON COMMENT 'MACD signal details',
    details JSON COMMENT 'Additional signal details',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_hybrid_signal (symbol_id, timeframe, timestamp),
    INDEX idx_hybrid_symbol_tf_ts (symbol_id, timeframe, timestamp),
    INDEX idx_hybrid_signal_ts (hybrid_signal, timestamp),
    INDEX idx_hybrid_direction_ts (hybrid_direction, timestamp),
    CONSTRAINT fk_hybrid_signals_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- =====================================================
-- 4. DATABASE VIEWS (từ db_improvements.sql)
-- =====================================================
-- View để dễ dàng query thresholds
CREATE
OR REPLACE VIEW symbol_thresholds_view AS
SELECT
    s.id as symbol_id,
    s.ticker,
    s.exchange,
    s.market_type,
    st.id as symbol_threshold_id,
    st.strategy_name,
    st.is_active,
    stv.timeframe,
    stv.indicator,
    stv.zone,
    stv.comparison,
    stv.min_value,
    stv.max_value
FROM
    symbols s
    LEFT JOIN symbol_thresholds st ON s.id = st.symbol_id
    AND st.is_active = TRUE
    LEFT JOIN symbol_threshold_values stv ON st.id = stv.symbol_threshold_id
WHERE
    s.active = TRUE;

-- View để query template thresholds
CREATE
OR REPLACE VIEW market_threshold_templates_view AS
SELECT
    mt.id as template_id,
    mt.market_type,
    mt.strategy_name,
    mt.description,
    mt.is_default,
    mtv.timeframe,
    mtv.indicator,
    mtv.zone,
    mtv.comparison,
    mtv.min_value,
    mtv.max_value
FROM
    market_threshold_templates mt
    LEFT JOIN market_threshold_template_values mtv ON mt.id = mtv.template_id
WHERE
    mt.is_default = TRUE;

-- View cho active signals
CREATE
OR REPLACE VIEW v_active_signals AS
SELECT
    s.*,
    sym.ticker,
    sym.exchange,
    ts.name as strategy_name
FROM
    signals s
    JOIN symbols sym ON s.symbol_id = sym.id
    LEFT JOIN trade_strategies ts ON s.strategy_id = ts.id
WHERE
    s.status = 'active'
    AND (
        s.expires_at IS NULL
        OR s.expires_at > NOW()
    )
ORDER BY
    s.ts DESC;

-- View cho signal statistics
CREATE
OR REPLACE VIEW v_signal_stats AS
SELECT
    sym.ticker,
    s.signal_type,
    COUNT(*) as signal_count,
    AVG(s.strength) as avg_strength,
    AVG(s.confidence) as avg_confidence,
    MAX(s.ts) as last_signal_time
FROM
    signals s
    JOIN symbols sym ON s.symbol_id = sym.id
WHERE
    s.ts >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY
    sym.ticker,
    s.signal_type
ORDER BY
    signal_count DESC;

-- =====================================================
-- 5. INITIAL DATA
-- =====================================================
-- Insert timeframes
INSERT
    IGNORE INTO timeframes (name, description, minutes)
VALUES
    ('1m', '1 minute', 1),
    ('2m', '2 minutes', 2),
    ('5m', '5 minutes', 5),
    ('15m', '15 minutes', 15),
    ('30m', '30 minutes', 30),
    ('1h', '1 hour', 60),
    ('4h', '4 hours', 240),
    ('1D', '1 day', 1440);

-- Insert default strategies
INSERT
    IGNORE INTO trade_strategies (name, description, strategy_type)
VALUES
    (
        'MACD Zone Strategy',
        'Default MACD zone-based strategy',
        'MACD'
    ),
    (
        'SMA Strategy',
        'Simple Moving Average strategy',
        'SMA'
    );

-- Insert default market templates
INSERT
    IGNORE INTO market_threshold_templates (
        market_type,
        strategy_name,
        description,
        is_default
    )
VALUES
    (
        'US',
        'MACD Zone Strategy',
        'Default thresholds for US market stocks',
        TRUE
    ),
    (
        'VN',
        'MACD Zone Strategy',
        'Default thresholds for VN market stocks',
        TRUE
    );

-- =====================================================
-- 6. INDEXES FOR PERFORMANCE
-- =====================================================
-- Additional indexes for better performance
-- Note: MySQL doesn't support IF NOT EXISTS for indexes, so these will be created or ignored
CREATE INDEX idx_signals_symbol_ts ON signals(symbol_id, ts);

CREATE INDEX idx_signals_timeframe_ts ON signals(timeframe, ts);

CREATE INDEX idx_candles_symbol_ts ON candles_1m(symbol_id, ts);

CREATE INDEX idx_candles_tf_symbol_ts ON candles_tf(symbol_id, timeframe, ts);

CREATE INDEX idx_indicators_macd_symbol_ts ON indicators_macd(symbol_id, timeframe, ts);

CREATE INDEX idx_indicators_sma_symbol_ts ON indicators_sma(symbol_id, timeframe, ts);