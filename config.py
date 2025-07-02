import os

# API Keys - Set these as environment variables or update directly here for testing
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDxgwkKSHMBRrPdI0l2R2n7ln-j5slJXfY')

# Shared Backend API Keys (Free Tier)
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')  # Free: 1,500 tweets/month
GOOGLE_CSE_API_KEY = os.getenv('GOOGLE_CSE_API_KEY', 'AIzaSyAT4tQKRNt1rwrqrTs2GzlXuWi-BAYJWPA')      # Free: 100 searches/day
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '010381b2504d141f5')  # Google Custom Search Engine ID
PEOPLE_DATA_LABS_API_KEY = os.getenv('PEOPLE_DATA_LABS_API_KEY', '6fa54f9fb99d3a5a3500b61381b0ecc7813271191f2719f3e746a4c5a4a6fa1e')  # Free: 1,000/month
PHANTOMBUSTER_API_KEY = os.getenv('PHANTOMBUSTER_API_KEY', '')

# API Settings
GEMINI_MODEL = 'gemini-1.5-flash'
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30

# Rate Limiting (Free Tier Shared Limits)
RATE_LIMITS = {
    'twitter_monthly': 1500,    # Free tier limit
    'google_daily': 100,        # Free tier limit  
    'pdl_monthly': 1000,        # Free tier limit
    'linkedin_daily': 50        # Conservative web scraping limit
}

# Default values
DEFAULT_TARGET_LEADS = 20
MAX_TARGET_LEADS = 100

# Multi-tenant API Strategy
API_STRATEGY = {
    'email_scout': 'shared',      # Always use shared PDL API
    'x_scout': 'hybrid',          # User auth preferred, fallback to shared
    'internet_scout': 'shared',   # Always use shared Google CSE
    'linkedin_scout': 'hybrid'    # User auth preferred, fallback to shared
}

# Social Profile Connection (Simple URL/Handle approach)
SOCIAL_PROFILES = {
    'linkedin': {
        'enabled': True,
        'validation_pattern': r'linkedin\.com/in/[^/?]+',
        'description': 'LinkedIn profile URL (e.g., linkedin.com/in/your-profile)'
    },
    'twitter': {
        'enabled': True,
        'validation_pattern': r'^[A-Za-z0-9_]{1,15}$',
        'description': 'Twitter handle without @ (e.g., yourusername)'
    }
}

# Database settings for user tokens (SQLite for simplicity)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///prefunnel.db') 