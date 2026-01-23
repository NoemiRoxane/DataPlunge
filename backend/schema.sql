-- DataPlunge Database Schema
-- PostgreSQL database schema for the DataPlunge project

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS performanceMetrics CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS oauth_tokens CASCADE;
DROP TABLE IF EXISTS google_ads_tokens CASCADE;
DROP TABLE IF EXISTS datasources CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Table: users
-- Stores user accounts (both email/password and OAuth users)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL for OAuth-only users
    full_name VARCHAR(255),
    google_oauth_id VARCHAR(255) UNIQUE,  -- For Google OAuth user authentication
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Table: user_sessions
-- Stores persistent user sessions
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: datasources
-- Stores data source information (Google Ads, Google Analytics, Meta, etc.)
CREATE TABLE datasources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, source_name)
);

-- Table: campaigns
-- Stores campaign information from various data sources
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(255) NOT NULL,
    data_source_id INTEGER,
    external_id VARCHAR(255),
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_source_id) REFERENCES datasources(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: google_ads_tokens
-- Stores Google Ads OAuth refresh tokens per customer per user
CREATE TABLE google_ads_tokens (
    customer_id VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL,
    refresh_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table: oauth_tokens
-- Stores OAuth tokens for Google Analytics and Meta per user
CREATE TABLE oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- 'google_analytics', 'meta'
    access_token TEXT,
    refresh_token TEXT,
    token_expiry TIMESTAMP,
    provider_user_id VARCHAR(255),  -- Provider's user ID
    provider_account_id VARCHAR(255),  -- For Meta: ad_account_id, for GA: property_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, provider)
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
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_oauth_id ON users(google_oauth_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_datasources_user_id ON datasources(user_id);
CREATE INDEX idx_datasources_source_name ON datasources(source_name);
CREATE INDEX idx_campaigns_data_source_id ON campaigns(data_source_id);
CREATE INDEX idx_campaigns_external_id ON campaigns(external_id);
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_google_ads_tokens_user_id ON google_ads_tokens(user_id);
CREATE INDEX idx_oauth_tokens_user_provider ON oauth_tokens(user_id, provider);
CREATE INDEX idx_performanceMetrics_date ON performanceMetrics(date);
CREATE INDEX idx_performanceMetrics_data_source_id ON performanceMetrics(data_source_id);
CREATE INDEX idx_performanceMetrics_campaign_id ON performanceMetrics(campaign_id);
