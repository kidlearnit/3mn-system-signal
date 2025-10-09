-- Symbols
CREATE TABLE IF NOT EXISTS symbols (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticker VARCHAR(20) NOT NULL UNIQUE,
  company_name VARCHAR(255),
  exchange VARCHAR(20) NOT NULL,
  currency VARCHAR(10) DEFAULT 'USD',
  weight DECIMAL(5, 2) DEFAULT NULL,
  sector VARCHAR(100) DEFAULT NULL,
  active TINYINT(1) DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Ensure all required columns exist (for existing databases)
-- Note: MySQL doesn't support multiple ADD COLUMN IF NOT EXISTS in one statement
-- So we use separate statements for each column
-- Add company_name column if it doesn't exist
SET
  @sql = (
    SELECT
      IF(
        (
          SELECT
            COUNT(*)
          FROM
            INFORMATION_SCHEMA.COLUMNS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'symbols'
            AND COLUMN_NAME = 'company_name'
        ) = 0,
        'ALTER TABLE symbols ADD COLUMN company_name VARCHAR(255) AFTER ticker',
        'SELECT "Column company_name already exists" as message'
      )
  );

PREPARE stmt
FROM
  @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

-- Add weight column if it doesn't exist
SET
  @sql = (
    SELECT
      IF(
        (
          SELECT
            COUNT(*)
          FROM
            INFORMATION_SCHEMA.COLUMNS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'symbols'
            AND COLUMN_NAME = 'weight'
        ) = 0,
        'ALTER TABLE symbols ADD COLUMN weight DECIMAL(5, 2) DEFAULT NULL AFTER currency',
        'SELECT "Column weight already exists" as message'
      )
  );

PREPARE stmt
FROM
  @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

-- Add sector column if it doesn't exist
SET
  @sql = (
    SELECT
      IF(
        (
          SELECT
            COUNT(*)
          FROM
            INFORMATION_SCHEMA.COLUMNS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'symbols'
            AND COLUMN_NAME = 'sector'
        ) = 0,
        'ALTER TABLE symbols ADD COLUMN sector VARCHAR(100) DEFAULT NULL AFTER weight',
        'SELECT "Column sector already exists" as message'
      )
  );

PREPARE stmt
FROM
  @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

-- Add created_at column if it doesn't exist
SET
  @sql = (
    SELECT
      IF(
        (
          SELECT
            COUNT(*)
          FROM
            INFORMATION_SCHEMA.COLUMNS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'symbols'
            AND COLUMN_NAME = 'created_at'
        ) = 0,
        'ALTER TABLE symbols ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER active',
        'SELECT "Column created_at already exists" as message'
      )
  );

PREPARE stmt
FROM
  @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

-- Add updated_at column if it doesn't exist
SET
  @sql = (
    SELECT
      IF(
        (
          SELECT
            COUNT(*)
          FROM
            INFORMATION_SCHEMA.COLUMNS
          WHERE
            TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'symbols'
            AND COLUMN_NAME = 'updated_at'
        ) = 0,
        'ALTER TABLE symbols ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at',
        'SELECT "Column updated_at already exists" as message'
      )
  );

PREPARE stmt
FROM
  @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

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
  hist DECIMAL(18, 6) NOT NULL,
  UNIQUE KEY uniq_macd (symbol_id, timeframe, ts),
  INDEX idx_macd (symbol_id, timeframe, ts),
  CONSTRAINT fk_macd_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Bars (tuỳ định nghĩa)
CREATE TABLE IF NOT EXISTS indicators_bars (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  symbol_id INT NOT NULL,
  timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
  ts TIMESTAMP NOT NULL,
  bars DECIMAL(18, 6) NOT NULL,
  UNIQUE KEY uniq_bars (symbol_id, timeframe, ts),
  CONSTRAINT fk_bars_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Strategies/thresholds normalized
CREATE TABLE IF NOT EXISTS trade_strategies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE IF NOT EXISTS timeframes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS indicators (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS zones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS strategy_thresholds (
  id INT AUTO_INCREMENT PRIMARY KEY,
  strategy_id INT NOT NULL,
  timeframe_id INT NOT NULL,
  UNIQUE KEY uniq_strategy_tf (strategy_id, timeframe_id),
  CONSTRAINT fk_stg FOREIGN KEY (strategy_id) REFERENCES trade_strategies(id),
  CONSTRAINT fk_stf FOREIGN KEY (timeframe_id) REFERENCES timeframes(id)
);

CREATE TABLE IF NOT EXISTS threshold_values (
  id INT AUTO_INCREMENT PRIMARY KEY,
  threshold_id INT NOT NULL,
  indicator_id INT NOT NULL,
  zone_id INT NOT NULL,
  comparison ENUM('>', '>=', '<', '<=', 'between') NOT NULL DEFAULT '>=',
  min_value DECIMAL(18, 6) DEFAULT NULL,
  max_value DECIMAL(18, 6) DEFAULT NULL,
  UNIQUE KEY uniq_threshold (threshold_id, indicator_id, zone_id),
  CONSTRAINT fk_tv_th FOREIGN KEY (threshold_id) REFERENCES strategy_thresholds(id),
  CONSTRAINT fk_tv_ind FOREIGN KEY (indicator_id) REFERENCES indicators(id),
  CONSTRAINT fk_tv_zone FOREIGN KEY (zone_id) REFERENCES zones(id)
);

-- Signals
CREATE TABLE IF NOT EXISTS signals (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  symbol_id INT NOT NULL,
  timeframe ENUM('1m', '2m', '5m', '15m', '30m', '1h', '4h', '1D') NOT NULL,
  ts TIMESTAMP NOT NULL,
  strategy_id INT NOT NULL,
  signal_type VARCHAR(30) NOT NULL,
  details JSON,
  UNIQUE KEY uniq_signal (
    symbol_id,
    timeframe,
    ts,
    strategy_id,
    signal_type
  ),
  CONSTRAINT fk_sig_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id),
  CONSTRAINT fk_sig_strategy FOREIGN KEY (strategy_id) REFERENCES trade_strategies(id)
);

CREATE TABLE IF NOT EXISTS workflows (
  id VARCHAR(36) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description VARCHAR(1000),
  nodes JSON NOT NULL,
  connections JSON NOT NULL,
  properties JSON,
  metadata JSON,
  status ENUM('active', 'inactive', 'draft') DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

ALTER TABLE
  candles_1m
ADD
  CONSTRAINT uq_candles_1m UNIQUE (symbol_id, ts);

ALTER TABLE
  candles_tf
ADD
  CONSTRAINT uq_candles_tf UNIQUE (symbol_id, timeframe, ts);

-- Workflows (for workflow builder + scheduler)
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
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- SMA indicators (for SMA pipeline storage)
CREATE TABLE IF NOT EXISTS indicators_sma (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol_id INT NOT NULL,
  timeframe VARCHAR(10) NOT NULL,
  ts DATETIME NOT NULL,
  close DECIMAL(18, 8) NOT NULL,
  m1 DECIMAL(18, 8),
  m2 DECIMAL(18, 8),
  m3 DECIMAL(18, 8),
  ma144 DECIMAL(18, 8),
  avg_m1_m2_m3 DECIMAL(18, 8),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_sma_symbol_tf_ts (symbol_id, timeframe, ts),
  CONSTRAINT fk_sma_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- SMA signals (for SMA alerts/results)
CREATE TABLE IF NOT EXISTS sma_signals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  symbol_id INT NOT NULL,
  timeframe VARCHAR(10) NOT NULL,
  timestamp DATETIME NOT NULL,
  signal_type VARCHAR(50) NOT NULL,
  signal_direction VARCHAR(10) NOT NULL,
  signal_strength DECIMAL(5, 2),
  current_price DECIMAL(18, 8),
  ma18 DECIMAL(18, 8),
  ma36 DECIMAL(18, 8),
  ma48 DECIMAL(18, 8),
  ma144 DECIMAL(18, 8),
  avg_ma DECIMAL(18, 8),
  is_sent_telegram TINYINT(1) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_sma_sig_symbol_tf_ts (symbol_id, timeframe, timestamp),
  CONSTRAINT fk_sma_sig_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);