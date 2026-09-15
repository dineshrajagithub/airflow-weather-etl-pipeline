-- 1. Rolling 7-day average temperature per city (window function)
SELECT city, obs_date, temp_avg_c,
       ROUND(AVG(temp_avg_c) OVER (PARTITION BY city ORDER BY obs_date
             ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS temp_avg_7d
FROM fact_daily_weather
ORDER BY city, obs_date;

-- 2. Longest consecutive rainy-day streak per city (gaps & islands)
WITH rainy AS (
    SELECT city, obs_date,
           obs_date - (ROW_NUMBER() OVER (PARTITION BY city ORDER BY obs_date))::int AS grp
    FROM fact_daily_weather
    WHERE is_rainy_day
)
SELECT city, MAX(streak) AS longest_rainy_streak
FROM (SELECT city, grp, COUNT(*) AS streak FROM rainy GROUP BY city, grp) s
GROUP BY city
ORDER BY longest_rainy_streak DESC;

-- 3. Rank cities by temperature volatility each month
SELECT month, city, stddev_temp,
       RANK() OVER (PARTITION BY month ORDER BY stddev_temp DESC) AS volatility_rank
FROM (
    SELECT DATE_TRUNC('month', obs_date)::date AS month, city,
           ROUND(STDDEV(temp_avg_c), 2) AS stddev_temp
    FROM fact_daily_weather
    GROUP BY 1, 2
) m;
