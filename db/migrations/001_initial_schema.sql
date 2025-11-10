-- Initial schema for Solar×Price Explorer

-- Prices table
CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    area VARCHAR(50) NOT NULL,
    system_price_jpy_kwh FLOAT,
    area_price_jpy_kwh FLOAT NOT NULL,
    volume_total_kwh FLOAT,
    volume_sell_kwh FLOAT,
    volume_buy_kwh FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_prices_timestamp ON prices(timestamp);
CREATE INDEX IF NOT EXISTS ix_prices_area ON prices(area);
CREATE INDEX IF NOT EXISTS ix_prices_area_timestamp ON prices(area, timestamp);

-- Radiation table
CREATE TABLE IF NOT EXISTS radiation (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    station VARCHAR(50) NOT NULL,
    area VARCHAR(50) NOT NULL,
    ghi FLOAT,
    dni FLOAT,
    dhi FLOAT,
    quality_flag VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_radiation_timestamp ON radiation(timestamp);
CREATE INDEX IF NOT EXISTS ix_radiation_station ON radiation(station);
CREATE INDEX IF NOT EXISTS ix_radiation_area ON radiation(area);
CREATE INDEX IF NOT EXISTS ix_radiation_area_timestamp ON radiation(area, timestamp);
CREATE INDEX IF NOT EXISTS ix_radiation_station_timestamp ON radiation(station, timestamp);

-- Features table
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    area VARCHAR(50) NOT NULL,
    target_price FLOAT,
    ghi FLOAT,
    dni FLOAT,
    dhi FLOAT,
    volume_kwh FLOAT,
    price_lag_1h FLOAT,
    price_lag_24h FLOAT,
    ghi_lag_1h FLOAT,
    ghi_roll3h FLOAT,
    hour INTEGER,
    dow INTEGER,
    month INTEGER,
    is_weekend INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_features_timestamp ON features(timestamp);
CREATE INDEX IF NOT EXISTS ix_features_area ON features(area);
CREATE INDEX IF NOT EXISTS ix_features_area_timestamp ON features(area, timestamp);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE NOT NULL,
    area VARCHAR(50) NOT NULL,
    target VARCHAR(50) NOT NULL,
    features TEXT,
    mae FLOAT,
    trained_at TIMESTAMPTZ NOT NULL,
    model_path VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_models_model_id ON models(model_id);
CREATE INDEX IF NOT EXISTS ix_models_area ON models(area);

-- Add unique constraints to prevent duplicates
ALTER TABLE prices ADD CONSTRAINT unique_price_record
    UNIQUE(timestamp, area);

ALTER TABLE radiation ADD CONSTRAINT unique_radiation_record
    UNIQUE(timestamp, station, area);

ALTER TABLE features ADD CONSTRAINT unique_feature_record
    UNIQUE(timestamp, area);
