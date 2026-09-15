CREATE TABLE IF NOT EXISTS fact_daily_weather (
    city                VARCHAR(64)   NOT NULL,
    country             CHAR(2)       NOT NULL,
    obs_date            DATE          NOT NULL,
    temp_max_c          NUMERIC(5,2),
    temp_min_c          NUMERIC(5,2),
    temp_avg_c          NUMERIC(5,2),
    temp_range_c        NUMERIC(5,2),
    precipitation_mm    NUMERIC(7,2)  NOT NULL DEFAULT 0,
    wind_speed_max_kmh  NUMERIC(6,2),
    is_rainy_day        BOOLEAN       NOT NULL,
    heat_category       VARCHAR(16)   NOT NULL,
    loaded_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (city, obs_date)
);

CREATE INDEX IF NOT EXISTS ix_fact_daily_weather_date ON fact_daily_weather (obs_date);
