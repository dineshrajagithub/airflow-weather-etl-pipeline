-- Monthly city summary consumed by the BI layer.
DROP TABLE IF EXISTS mart_city_monthly_weather;
CREATE TABLE mart_city_monthly_weather AS
SELECT
    city,
    country,
    DATE_TRUNC('month', obs_date)::date          AS month,
    COUNT(*)                                     AS days_observed,
    ROUND(AVG(temp_avg_c), 2)                    AS avg_temp_c,
    MAX(temp_max_c)                              AS hottest_temp_c,
    MIN(temp_min_c)                              AS coldest_temp_c,
    ROUND(SUM(precipitation_mm), 1)              AS total_precip_mm,
    SUM(CASE WHEN is_rainy_day THEN 1 ELSE 0 END) AS rainy_days,
    SUM(CASE WHEN heat_category = 'very_hot' THEN 1 ELSE 0 END) AS very_hot_days
FROM fact_daily_weather
GROUP BY city, country, DATE_TRUNC('month', obs_date);
