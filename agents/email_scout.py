from config import API_STRATEGY

def scout_from_email(email, user_id=None):
    """
    Email scout that always uses shared People Data Labs API
    user_id parameter included for consistency but not used
    """
    if API_STRATEGY['email_scout'] == 'shared':
        try:
            from .email_scout_real import scout_from_email as real_scout
            return real_scout(email)
        except ImportError:
            # Fallback to mock if real implementation not available
            pass
    
    # Mock implementation
    return [{
        "name": "John Doe",
        "title": "Founder",
        "company": "TechStart",
        "linkedin": "https://linkedin.com/in/johndoe",
        "x_handle": "@johndoe",
        "public_links": [],
        "source": "email_scout_mock"
    }] 