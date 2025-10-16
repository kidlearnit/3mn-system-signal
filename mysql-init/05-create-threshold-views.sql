-- Create threshold views for symbol and market thresholds
-- This file creates the missing views that the symbol_thresholds.py service expects
-- First, create the missing tables that the views depend on
-- These tables are referenced in the symbol_thresholds.py but don't exist in the schema
-- Market threshold templates table
CREATE TABLE IF NOT EXISTS market_threshold_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_type VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    is_default TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_market_tf (market_type, timeframe)
);

-- Market threshold template values table
CREATE TABLE IF NOT EXISTS market_threshold_template_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    indicator VARCHAR(20) NOT NULL,
    zone VARCHAR(20) NOT NULL,
    comparison ENUM('>', '>=', '<', '<=', 'between') NOT NULL DEFAULT '>=',
    min_value DECIMAL(18, 6) DEFAULT NULL,
    max_value DECIMAL(18, 6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_template_indicator_zone (template_id, indicator, zone),
    CONSTRAINT fk_mttv_template FOREIGN KEY (template_id) REFERENCES market_threshold_templates(id)
);

-- Symbol thresholds table
CREATE TABLE IF NOT EXISTS symbol_thresholds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_symbol_active (symbol_id, is_active),
    CONSTRAINT fk_st_symbol FOREIGN KEY (symbol_id) REFERENCES symbols(id)
);

-- Symbol threshold values table
CREATE TABLE IF NOT EXISTS symbol_threshold_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_threshold_id INT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    indicator VARCHAR(20) NOT NULL,
    zone VARCHAR(20) NOT NULL,
    comparison ENUM('>', '>=', '<', '<=', 'between') NOT NULL DEFAULT '>=',
    min_value DECIMAL(18, 6) DEFAULT NULL,
    max_value DECIMAL(18, 6) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_stv (symbol_threshold_id, timeframe, indicator, zone),
    CONSTRAINT fk_stv_threshold FOREIGN KEY (symbol_threshold_id) REFERENCES symbol_thresholds(id)
);

-- Add market_type column to symbols table if it doesn't exist
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
                        AND COLUMN_NAME = 'market_type'
                ) = 0,
                'ALTER TABLE symbols ADD COLUMN market_type VARCHAR(20) DEFAULT "GLOBAL" AFTER exchange',
                'SELECT "Column market_type already exists" as message'
            )
    );

PREPARE stmt
FROM
    @sql;

EXECUTE stmt;

DEALLOCATE PREPARE stmt;

-- Create symbol_thresholds_view
CREATE
OR REPLACE VIEW symbol_thresholds_view AS
SELECT
    stv.symbol_threshold_id as id,
    st.symbol_id,
    stv.timeframe,
    stv.indicator,
    stv.zone,
    stv.comparison,
    stv.min_value,
    stv.max_value,
    st.is_active
FROM
    symbol_threshold_values stv
    JOIN symbol_thresholds st ON st.id = stv.symbol_threshold_id
WHERE
    st.is_active = TRUE;

-- Create market_threshold_templates_view
CREATE
OR REPLACE VIEW market_threshold_templates_view AS
SELECT
    mtv.template_id as id,
    mt.market_type,
    mt.timeframe,
    mtv.indicator,
    mtv.zone,
    mtv.comparison,
    mtv.min_value,
    mtv.max_value,
    mt.is_default
FROM
    market_threshold_template_values mtv
    JOIN market_threshold_templates mt ON mt.id = mtv.template_id
WHERE
    mt.is_default = TRUE;

-- Insert default market threshold templates
INSERT
    IGNORE INTO market_threshold_templates (market_type, timeframe, is_default)
VALUES
    ('US', '1m', 1),
    ('US', '2m', 1),
    ('US', '5m', 1),
    ('US', '15m', 1),
    ('US', '30m', 1),
    ('US', '1h', 1),
    ('US', '4h', 1),
    ('VN', '1m', 1),
    ('VN', '2m', 1),
    ('VN', '5m', 1),
    ('VN', '15m', 1),
    ('VN', '30m', 1),
    ('VN', '1h', 1),
    ('VN', '4h', 1),
    ('GLOBAL', '1m', 1),
    ('GLOBAL', '2m', 1),
    ('GLOBAL', '5m', 1),
    ('GLOBAL', '15m', 1),
    ('GLOBAL', '30m', 1),
    ('GLOBAL', '1h', 1),
    ('GLOBAL', '4h', 1);

-- Insert default market threshold template values for US market
INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'igr',
    '>=',
    0.5,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'greed',
    '>=',
    0.3,
    0.5
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bull',
    '>=',
    0.1,
    0.3
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'pos',
    '>=',
    0.05,
    0.1
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neutral',
    'between',
    -0.05,
    0.05
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neg',
    '<=',
    -0.05,
    -0.1
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bear',
    '<=',
    -0.1,
    -0.3
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'fear',
    '<=',
    -0.3,
    -0.5
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'panic',
    '<=',
    -0.5,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'US'
    AND mt.timeframe = '5m';

-- Insert default market threshold template values for VN market (more volatile)
INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'igr',
    '>=',
    0.8,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'greed',
    '>=',
    0.5,
    0.8
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bull',
    '>=',
    0.2,
    0.5
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'pos',
    '>=',
    0.1,
    0.2
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neutral',
    'between',
    -0.1,
    0.1
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neg',
    '<=',
    -0.1,
    -0.2
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bear',
    '<=',
    -0.2,
    -0.5
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'fear',
    '<=',
    -0.5,
    -0.8
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'panic',
    '<=',
    -0.8,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'VN'
    AND mt.timeframe = '5m';

-- Insert default market threshold template values for GLOBAL market
INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'igr',
    '>=',
    0.6,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'greed',
    '>=',
    0.4,
    0.6
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bull',
    '>=',
    0.15,
    0.4
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'pos',
    '>=',
    0.08,
    0.15
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neutral',
    'between',
    -0.08,
    0.08
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'neg',
    '<=',
    -0.08,
    -0.15
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'bear',
    '<=',
    -0.15,
    -0.4
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'fear',
    '<=',
    -0.4,
    -0.6
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

INSERT
    IGNORE INTO market_threshold_template_values (
        template_id,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    mt.id,
    'fmacd',
    'panic',
    '<=',
    -0.6,
    NULL
FROM
    market_threshold_templates mt
WHERE
    mt.market_type = 'GLOBAL'
    AND mt.timeframe = '5m';

-- Update symbols table to set market_type based on exchange
UPDATE
    symbols
SET
    market_type = 'US'
WHERE
    exchange IN ('NASDAQ', 'NYSE', 'AMEX');

UPDATE
    symbols
SET
    market_type = 'VN'
WHERE
    exchange IN ('HOSE', 'HNX', 'UPCOM');

UPDATE
    symbols
SET
    market_type = 'GLOBAL'
WHERE
    market_type IS NULL
    OR market_type = '';

-- Create default symbol thresholds for all active symbols
INSERT
    IGNORE INTO symbol_thresholds (symbol_id, is_active)
SELECT
    id,
    1
FROM
    symbols
WHERE
    active = 1;

-- Copy market threshold template values to symbol threshold values for all symbols
INSERT
    IGNORE INTO symbol_threshold_values (
        symbol_threshold_id,
        timeframe,
        indicator,
        zone,
        comparison,
        min_value,
        max_value
    )
SELECT
    st.id,
    mt.timeframe,
    mtv.indicator,
    mtv.zone,
    mtv.comparison,
    mtv.min_value,
    mtv.max_value
FROM
    symbol_thresholds st
    JOIN symbols s ON s.id = st.symbol_id
    JOIN market_threshold_templates mt ON mt.market_type = s.market_type
    JOIN market_threshold_template_values mtv ON mtv.template_id = mt.id
WHERE
    st.is_active = TRUE
    AND mt.is_default = TRUE;