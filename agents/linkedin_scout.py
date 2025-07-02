from config import API_STRATEGY
from user_auth import auth_manager

def linkedin_scout(query, user_id=None):
    """
    LinkedIn scout with hybrid API strategy:
    1. Try user's connected LinkedIn account (if available)
    2. Fallback to shared backend LinkedIn scraping
    3. Fallback to mock data
    """
    
    # Strategy 1: User's connected LinkedIn account (Enhanced OAuth)
    if user_id and API_STRATEGY['linkedin_scout'] == 'hybrid':
        user_token = auth_manager.get_user_token(user_id, 'linkedin')
        if user_token:
            try:
                from .linkedin_scout_enhanced import linkedin_scout_enhanced
                auth_manager.track_api_usage(user_id, 'linkedin', 'search')
                profiles = linkedin_scout_enhanced(query, user_id)
                if profiles and any(p.get('source') == 'linkedin_oauth' for p in profiles):
                    return profiles
            except ImportError:
                pass
    
    # Strategy 2: Shared backend API (PhantomBuster or web scraping)
    try:
        from .linkedin_scout_real import linkedin_scout as real_scout
        # Check shared rate limits here if needed
        return real_scout(query)
    except ImportError:
        # Fallback to mock if real implementation not available
        pass
    
    # Strategy 3: Mock implementation
    return [{
        "name": "Bob LinkedIn",
        "title": "VP Sales",
        "company": "VoiceAI Corp",
        "linkedin": "https://linkedin.com/in/boblinkedin",
        "x_handle": None,
        "public_links": [],
        "source": "linkedin_scout_mock"
    }] 