from config import API_STRATEGY

def internet_scout(query, user_id=None):
    """
    Internet scout that always uses shared Google Custom Search API
    user_id parameter included for consistency but not used
    """
    if API_STRATEGY['internet_scout'] == 'shared':
        try:
            from .internet_scout_real import internet_scout as real_scout
            return real_scout(query)
        except ImportError:
            # Fallback to mock if real implementation not available
            pass
    
    # Mock implementation
    return [{
        "name": "Charlie Web",
        "title": "CTO",
        "company": "WebVoice",
        "linkedin": None,
        "x_handle": "@charlieweb",
        "public_links": ["https://webvoice.com/team"],
        "source": "internet_scout_mock"
    }] 