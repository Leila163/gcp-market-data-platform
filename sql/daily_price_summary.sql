SELECT
    symbol,
    COUNT(*) AS trading_days,
    MIN(trading_date) AS first_trading_date,
    MAX(trading_date) AS latest_trading_date,
    ROUND(AVG(close), 2) AS average_close,
    MIN(close) AS minimum_close,
    MAX(close) AS maximum_close
FROM `marketpulse-lrcx-2026.marketpulse_analytics.daily_prices`
WHERE trading_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
GROUP BY symbol
ORDER BY symbol;
