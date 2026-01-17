-- DataPlunge Database Schema
-- PostgreSQL database schema for the DataPlunge project

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS performanceMetrics CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS datasources CASCADE;
DROP TABLE IF EXISTS google_ads_tokens CASCADE;

-- Table: datasources
-- Stores data source information (Google Ads, Google Analytics, Meta, etc.)
CREATE TABLE datasources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, source_name)
);

-- Table: campaigns
-- Stores campaign information from various data sources
-- Note: id can be manually set (for Google Ads campaigns) or auto-generated (for GA/Meta campaigns)
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    data_source_id INTEGER,
    external_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_source_id) REFERENCES datasources(id) ON DELETE CASCADE
);

-- Table: google_ads_tokens
-- Stores Google Ads OAuth refresh tokens per customer
CREATE TABLE google_ads_tokens (
    customer_id VARCHAR(255) PRIMARY KEY,
    refresh_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: performanceMetrics
-- Stores performance metrics for campaigns by date
CREATE TABLE performanceMetrics (
    id SERIAL PRIMARY KEY,
    data_source_id INTEGER NOT NULL,
    campaign_id INTEGER NOT NULL,
    date DATE NOT NULL,
    costs NUMERIC(15, 6) DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    cost_per_click NUMERIC(15, 6) DEFAULT 0,
    sessions INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    cost_per_conversion NUMERIC(15, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_source_id) REFERENCES datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    UNIQUE(data_source_id, campaign_id, date)
);

-- Create indexes for better query performance
CREATE INDEX idx_performanceMetrics_date ON performanceMetrics(date);
CREATE INDEX idx_performanceMetrics_data_source_id ON performanceMetrics(data_source_id);
CREATE INDEX idx_performanceMetrics_campaign_id ON performanceMetrics(campaign_id);
CREATE INDEX idx_campaigns_data_source_id ON campaigns(data_source_id);
CREATE INDEX idx_campaigns_external_id ON campaigns(external_id);
CREATE INDEX idx_datasources_user_id ON datasources(user_id);
CREATE INDEX idx_datasources_source_name ON datasources(source_name);

