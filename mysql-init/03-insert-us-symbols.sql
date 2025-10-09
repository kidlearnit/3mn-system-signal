-- Insert US stock symbols for SMA trading system
-- This script contains 25 major US stocks with weight and sector information
-- Clear existing symbols (optional - remove if you want to keep existing data)
-- DELETE FROM symbols;
-- Insert 25 major US stocks from the table
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
    -- Top Technology Stocks
    (
        'NVDA',
        'NVIDIA Corporation',
        'NASDAQ',
        'USD',
        10.08,
        'Technology',
        1
    ),
    (
        'MSFT',
        'Microsoft Corporation',
        'NASDAQ',
        'USD',
        8.98,
        'Technology',
        1
    ),
    (
        'AAPL',
        'Apple Inc.',
        'NASDAQ',
        'USD',
        7.33,
        'Technology',
        1
    ),
    (
        'AMZN',
        'Amazon.com, Inc.',
        'NASDAQ',
        'USD',
        5.43,
        'Consumer Discretionary',
        1
    ),
    (
        'AVGO',
        'Broadcom Inc.',
        'NASDAQ',
        'USD',
        5.40,
        'Technology',
        1
    ),
    -- Communication Services
    (
        'META',
        'Meta Platforms, Inc.',
        'NASDAQ',
        'USD',
        3.86,
        'Communication Services',
        1
    ),
    (
        'NFLX',
        'Netflix, Inc.',
        'NASDAQ',
        'USD',
        2.84,
        'Communication Services',
        1
    ),
    (
        'GOOGL',
        'Alphabet Inc. (Class A)',
        'NASDAQ',
        'USD',
        2.63,
        'Communication Services',
        1
    ),
    (
        'GOOG',
        'Alphabet Inc. (Class C)',
        'NASDAQ',
        'USD',
        2.47,
        'Communication Services',
        1
    ),
    (
        'TMUS',
        'T-Mobile US, Inc.',
        'NASDAQ',
        'USD',
        1.54,
        'Communication Services',
        1
    ),
    -- Consumer & Retail
    (
        'TSLA',
        'Tesla, Inc.',
        'NASDAQ',
        'USD',
        2.68,
        'Consumer Discretionary',
        1
    ),
    (
        'COST',
        'Costco Wholesale Corporation',
        'NASDAQ',
        'USD',
        2.43,
        'Consumer Staples',
        1
    ),
    (
        'BKNG',
        'Booking Holdings Inc.',
        'NASDAQ',
        'USD',
        1.02,
        'Consumer Discretionary',
        1
    ),
    (
        'PEP',
        'PepsiCo, Inc.',
        'NASDAQ',
        'USD',
        1.09,
        'Consumer Staples',
        1
    ),
    -- Technology & Software
    (
        'PLTR',
        'Palantir Technologies Inc.',
        'NYSE',
        'USD',
        2.30,
        'Technology',
        1
    ),
    (
        'CSCO',
        'Cisco Systems, Inc.',
        'NASDAQ',
        'USD',
        1.55,
        'Technology',
        1
    ),
    (
        'AMD',
        'Advanced Micro Devices, Inc.',
        'NASDAQ',
        'USD',
        1.50,
        'Technology',
        1
    ),
    (
        'INTU',
        'Intuit Inc.',
        'NASDAQ',
        'USD',
        1.23,
        'Technology',
        1
    ),
    (
        'SHOP',
        'Shopify Inc.',
        'NYSE',
        'USD',
        1.07,
        'Technology',
        1
    ),
    (
        'TXN',
        'Texas Instruments',
        'NASDAQ',
        'USD',
        0.96,
        'Technology',
        1
    ),
    (
        'QCOM',
        'QUALCOMM Incorporated',
        'NASDAQ',
        'USD',
        0.91,
        'Technology',
        1
    ),
    (
        'ADBE',
        'Adobe Inc.',
        'NASDAQ',
        'USD',
        0.83,
        'Technology',
        1
    ),
    -- Healthcare & Industrial
    (
        'ISRG',
        'Intuitive Surgical, Inc.',
        'NASDAQ',
        'USD',
        0.96,
        'Healthcare',
        1
    ),
    (
        'AMGN',
        'Amgen Inc.',
        'NASDAQ',
        'USD',
        0.87,
        'Healthcare',
        1
    ),
    (
        'LIN',
        'Linde plc',
        'NYSE',
        'USD',
        1.26,
        'Industrials',
        1
    ),
    -- ETF
    (
        'TQQQ',
        'QQQ Triple Index',
        'NASDAQ',
        'USD',
        NULL,
        'QQQ triple long',
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
            WHEN exchange = 'NASDAQ' THEN 1
        END
    ) as nasdaq_symbols,
    COUNT(
        CASE
            WHEN exchange = 'NYSE' THEN 1
        END
    ) as nyse_symbols
FROM
    symbols
WHERE
    exchange IN ('NASDAQ', 'NYSE');

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
    AND exchange IN ('NASDAQ', 'NYSE')
GROUP BY
    sector
ORDER BY
    total_weight DESC;

-- Show all US symbols with details
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
    exchange IN ('NASDAQ', 'NYSE')
ORDER BY
    weight DESC,
    ticker;