from config import API_STRATEGY
from user_auth import auth_manager

def x_scout(query, user_id=None):
    """
    X/Twitter scout with hybrid API strategy:
    1. Try user's connected Twitter account (if available)
    2. Fallback to shared backend Twitter API
    3. Fallback to mock data
    """
    
    # Strategy 1: User's connected Twitter account (Enhanced OAuth)
    if user_id and API_STRATEGY['x_scout'] == 'hybrid':
        user_token = auth_manager.get_user_token(user_id, 'twitter')
        if user_token:
            try:
                from .x_scout_enhanced import x_scout_enhanced
                auth_manager.track_api_usage(user_id, 'twitter', 'search')
                profiles = x_scout_enhanced(query, user_id)
                if profiles and any(p.get('source') == 'twitter_oauth' for p in profiles):
                    return profiles
            except ImportError:
                pass
    
    # Strategy 2: Shared backend API
    try:
        from .x_scout_real import x_scout as real_scout
        # Check shared rate limits here if needed
        return real_scout(query)
    except ImportError:
        # Fallback to mock if real implementation not available
        pass
    
    # Strategy 3: Mock implementation
    return [{
        "name": "Alice X",
        "title": "Tech Lead",
        "company": "ChatVoice",
        "linkedin": None,
        "x_handle": "@alicex",
        "public_links": [],
        "source": "x_scout_mock"
    }] 