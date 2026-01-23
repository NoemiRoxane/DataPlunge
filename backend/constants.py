"""
Constants used throughout the DataPlunge backend.
"""

# Data source names (must match database entries)
DATASOURCE_GOOGLE_ADS = "Google Ads"
DATASOURCE_GOOGLE_ANALYTICS = "Google Analytics"
DATASOURCE_META = "Meta"

# All available data sources
ALL_DATASOURCES = [
    DATASOURCE_GOOGLE_ADS,
    DATASOURCE_GOOGLE_ANALYTICS,
    DATASOURCE_META,
]

# OAuth providers
OAUTH_PROVIDER_GOOGLE_ADS = "google_ads"
OAUTH_PROVIDER_GOOGLE_ANALYTICS = "google_analytics"
OAUTH_PROVIDER_META = "meta"

# Google OAuth scopes
GOOGLE_USER_AUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

GOOGLE_ADS_SCOPES = [
    "https://www.googleapis.com/auth/adwords",
]

GOOGLE_ANALYTICS_SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/analytics.edit",
    "https://www.googleapis.com/auth/analytics.manage.users",
    "https://www.googleapis.com/auth/analytics",
    "https://www.googleapis.com/auth/adwords",
]

# Meta OAuth scopes
META_SCOPES = "ads_read,ads_management"

# API versions
META_API_VERSION = "v19.0"
GOOGLE_ADS_API_VERSION = "v22"
