-- Insert Vietnamese stock symbols for SMA trading system
-- This script adds VN30 stocks for Vietnamese market analysis
-- Clear existing symbols (optional - remove if you want to keep existing data)
-- DELETE FROM symbols;
-- Insert VN30 major stocks
INSERT INTO
    symbols (
        ticker,
        company_name,
        exchange,
        currency,
        weight,
        sector,
        active
    )
VALUES
    -- Banking & Financial Services
    (
        'VCB',
        'Vietcombank',
        'HOSE',
        'VND',
        15.2,
        'Financial Services',
        1
    ),
    (
        'BID',
        'BIDV',
        'HOSE',
        'VND',
        8.5,
        'Financial Services',
        1
    ),
    (
        'CTG',
        'VietinBank',
        'HOSE',
        'VND',
        7.8,
        'Financial Services',
        1
    ),
    (
        'MBB',
        'MB Bank',
        'HOSE',
        'VND',
        6.2,
        'Financial Services',
        1
    ),
    (
        'TCB',
        'Techcombank',
        'HOSE',
        'VND',
        5.9,
        'Financial Services',
        1
    ),
    (
        'VPB',
        'VPBank',
        'HOSE',
        'VND',
        4.8,
        'Financial Services',
        1
    ),
    (
        'ACB',
        'ACB Bank',
        'HOSE',
        'VND',
        3.5,
        'Financial Services',
        1
    ),
    (
        'HDB',
        'HDBank',
        'HOSE',
        'VND',
        2.8,
        'Financial Services',
        1
    ),
    (
        'TPB',
        'TPBank',
        'HOSE',
        'VND',
        2.1,
        'Financial Services',
        1
    ),
    (
        'STB',
        'Sacombank',
        'HOSE',
        'VND',
        1.9,
        'Financial Services',
        1
    ),
    -- Technology & Telecommunications
    (
        'FPT',
        'FPT Corporation',
        'HOSE',
        'VND',
        4.2,
        'Technology',
        1
    ),
    (
        'VHM',
        'Vinhomes',
        'HOSE',
        'VND',
        3.8,
        'Real Estate',
        1
    ),
    (
        'VIC',
        'Vingroup',
        'HOSE',
        'VND',
        3.5,
        'Real Estate',
        1
    ),
    (
        'VRE',
        'Vincom Retail',
        'HOSE',
        'VND',
        2.9,
        'Real Estate',
        1
    ),
    (
        'VNM',
        'Vinamilk',
        'HOSE',
        'VND',
        2.6,
        'Consumer Staples',
        1
    ),
    -- Industrial & Manufacturing
    (
        'HPG',
        'Hoa Phat Group',
        'HOSE',
        'VND',
        3.2,
        'Industrials',
        1
    ),
    (
        'HSG',
        'Hoa Sen Group',
        'HOSE',
        'VND',
        2.4,
        'Industrials',
        1
    ),
    (
        'GAS',
        'PetroVietnam Gas',
        'HOSE',
        'VND',
        2.1,
        'Energy',
        1
    ),
    (
        'PLX',
        'Petrolimex',
        'HOSE',
        'VND',
        1.8,
        'Energy',
        1
    ),
    (
        'POW',
        'PetroVietnam Power',
        'HOSE',
        'VND',
        1.5,
        'Energy',
        1
    ),
    -- Consumer & Retail
    (
        'MWG',
        'Mobile World',
        'HOSE',
        'VND',
        2.7,
        'Consumer Discretionary',
        1
    ),
    (
        'MSN',
        'Masan Group',
        'HOSE',
        'VND',
        2.3,
        'Consumer Staples',
        1
    ),
    (
        'VGC',
        'Viglacera',
        'HOSE',
        'VND',
        1.6,
        'Materials',
        1
    ),
    (
        'PNJ',
        'Phu Nhuan Jewelry',
        'HOSE',
        'VND',
        1.4,
        'Consumer Discretionary',
        1
    ),
    (
        'SAB',
        'Sabeco',
        'HOSE',
        'VND',
        1.2,
        'Consumer Staples',
        1
    ),
    -- Real Estate & Construction
    (
        'NVL',
        'Novaland',
        'HOSE',
        'VND',
        2.8,
        'Real Estate',
        1
    ),
    (
        'KDH',
        'Khang Dien House',
        'HOSE',
        'VND',
        2.1,
        'Real Estate',
        1
    ),
    (
        'DXG',
        'Dat Xanh Group',
        'HOSE',
        'VND',
        1.9,
        'Real Estate',
        1
    ),
    (
        'PDR',
        'Phat Dat Real Estate',
        'HOSE',
        'VND',
        1.7,
        'Real Estate',
        1
    ),
    (
        'VPI',
        'Van Phu Invest',
        'HOSE',
        'VND',
        1.3,
        'Real Estate',
        1
    ) ON DUPLICATE KEY
UPDATE
    company_name =
VALUES
    (company_name),
    exchange =
VALUES
    (exchange),
    currency =
VALUES
    (currency),
    weight =
VALUES
    (weight),
    sector =
VALUES
    (sector),
    active =
VALUES
    (active),
    updated_at = CURRENT_TIMESTAMP;

-- Verify the insertion
SELECT
    COUNT(*) as total_symbols,
    COUNT(
        CASE
            WHEN active = 1 THEN 1
        END
    ) as active_symbols,
    COUNT(
        CASE
            WHEN exchange = 'HOSE' THEN 1
        END
    ) as hose_symbols,
    COUNT(
        CASE
            WHEN currency = 'VND' THEN 1
        END
    ) as vnd_symbols
FROM
    symbols
WHERE
    exchange = 'HOSE';

-- Show symbols by sector
SELECT
    sector,
    COUNT(*) as symbol_count,
    ROUND(SUM(weight), 2) as total_weight,
    GROUP_CONCAT(
        ticker
        ORDER BY
            weight DESC SEPARATOR ', '
    ) as tickers
FROM
    symbols
WHERE
    active = 1
    AND weight IS NOT NULL
    AND exchange = 'HOSE'
GROUP BY
    sector
ORDER BY
    total_weight DESC;

-- Show all Vietnamese symbols
SELECT
    id,
    ticker,
    company_name,
    exchange,
    currency,
    weight,
    sector,
    active,
    created_at
FROM
    symbols
WHERE
    exchange = 'HOSE'
ORDER BY
    weight DESC,
    ticker;