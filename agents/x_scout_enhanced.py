import requests
import logging
import json
import re
from typing import List, Dict, Optional
from user_auth import auth_manager
from config import TWITTER_BEARER_TOKEN

def x_scout_enhanced(query: str, user_id: Optional[str] = None, company_handle: Optional[str] = None) -> List[Dict]:
    """
    Enhanced Twitter/X scout with user OAuth tokens for deep search
    
    Features:
    - User's Twitter token for authenticated searches
    - Company/brand mention tracking
    - Follower analysis
    - Real-time engagement data
    - Advanced filtering and targeting
    - Fallback to shared API/mock data
    """
    
    # Try user's Twitter token first
    if user_id:
        user_token = auth_manager.get_user_token(user_id, 'twitter')
        if user_token:
            profiles = _search_with_user_token(query, user_token, company_handle)
            if profiles:
                return profiles
    
    # Fallback to shared Twitter API or mock
    return _fallback_twitter_search(query)

def _search_with_user_token(query: str, token_data: Dict, company_handle: Optional[str]) -> List[Dict]:
    """Search Twitter using user's OAuth token"""
    access_token = token_data['access_token']
    profiles = []
    
    try:
        # Track API usage
        auth_manager.track_api_usage(token_data.get('user_id'), 'twitter', 'user_search')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # 1. User Search - Find users matching query
        user_profiles = _search_twitter_users(query, headers)
        profiles.extend(user_profiles)
        
        # 2. Tweet Search - Find users from relevant tweets
        if len(profiles) < 5:
            tweet_profiles = _search_twitter_tweets(query, headers, company_handle)
            profiles.extend(tweet_profiles)
        
        # 3. Company mention search if company handle provided
        if company_handle and len(profiles) < 10:
            mention_profiles = _search_company_mentions(company_handle, headers)
            profiles.extend(mention_profiles)
            
    except Exception as e:
        logging.error(f"Error in Twitter user token search: {e}")
    
    return profiles

def _search_twitter_users(query: str, headers: Dict) -> List[Dict]:
    """Search for Twitter users matching query"""
    profiles = []
    
    try:
        # Twitter API v2 - User Search
        search_url = 'https://api.twitter.com/2/users/search'
        params = {
            'query': query,
            'max_results': 10,
            'user.fields': 'description,location,public_metrics,verified,url,profile_image_url'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            for user in data.get('data', []):
                profile = _parse_twitter_user(user)
                if profile:
                    profiles.append(profile)
                    
        elif response.status_code == 429:
            logging.warning("Twitter API rate limit exceeded")
        elif response.status_code == 403:
            logging.warning("Twitter API access denied - insufficient permissions")
            
    except Exception as e:
        logging.error(f"Error searching Twitter users: {e}")
    
    return profiles

def _search_twitter_tweets(query: str, headers: Dict, company_handle: Optional[str] = None) -> List[Dict]:
    """Search tweets and extract user profiles from relevant tweets"""
    profiles = []
    
    try:
        # Twitter API v2 - Tweet Search
        search_url = 'https://api.twitter.com/2/tweets/search/recent'
        
        # Build search query
        search_query = query
        if company_handle:
            search_query += f' OR @{company_handle} OR #{company_handle}'
        
        params = {
            'query': search_query,
            'max_results': 20,
            'tweet.fields': 'author_id,public_metrics,context_annotations',
            'expansions': 'author_id',
            'user.fields': 'description,location,public_metrics,verified,url,profile_image_url'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract users from tweet authors
            users = data.get('includes', {}).get('users', [])
            for user in users:
                profile = _parse_twitter_user(user)
                if profile and _is_relevant_profile(profile, query):
                    profiles.append(profile)
                    
    except Exception as e:
        logging.error(f"Error searching Twitter tweets: {e}")
    
    return profiles

def _search_company_mentions(company_handle: str, headers: Dict) -> List[Dict]:
    """Search for users who mention or interact with company"""
    profiles = []
    
    try:
        # Search for mentions of the company
        search_url = 'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': f'@{company_handle} OR #{company_handle}',
            'max_results': 15,
            'tweet.fields': 'author_id,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'description,location,public_metrics,verified,url'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract users who mentioned the company
            users = data.get('includes', {}).get('users', [])
            for user in users:
                profile = _parse_twitter_user(user)
                if profile:
                    profile['engagement_type'] = 'company_mention'
                    profiles.append(profile)
                    
    except Exception as e:
        logging.error(f"Error searching company mentions: {e}")
    
    return profiles

def _parse_twitter_user(user_data: Dict) -> Optional[Dict]:
    """Parse Twitter API user data into our profile format"""
    try:
        name = user_data.get('name', '')
        username = user_data.get('username', '')
        
        if not name and not username:
            return None
        
        # Extract job title and company from bio
        bio = user_data.get('description', '')
        title, company = _extract_title_company_from_bio(bio)
        
        # Extract LinkedIn URL from bio if present
        linkedin_url = _extract_linkedin_from_bio(bio)
        
        # Build Twitter URL
        twitter_url = f"https://twitter.com/{username}" if username else None
        
        profile = {
            'name': name or username,
            'title': title,
            'company': company,
            'linkedin': linkedin_url,
            'x_handle': f"@{username}" if username else None,
            'source': 'twitter_oauth',
            'confidence': 0.8,  # High confidence for OAuth data
            'email': None,
            'public_links': [twitter_url] if twitter_url else []
        }
        
        # Add metrics if available
        metrics = user_data.get('public_metrics', {})
        if metrics:
            profile['twitter_metrics'] = {
                'followers': metrics.get('followers_count', 0),
                'following': metrics.get('following_count', 0),
                'tweets': metrics.get('tweet_count', 0)
            }
        
        # Add location if available
        if user_data.get('location'):
            profile['location'] = user_data['location']
        
        # Add verification status
        if user_data.get('verified'):
            profile['verified'] = True
            profile['confidence'] = 0.9  # Higher confidence for verified accounts
        
        return profile
        
    except Exception as e:
        logging.error(f"Error parsing Twitter user: {e}")
        return None

def _extract_title_company_from_bio(bio: str) -> tuple:
    """Extract job title and company from Twitter bio"""
    if not bio:
        return "Professional", "Unknown Company"
    
    # Common patterns for job titles
    title_patterns = [
        r'(CEO|CTO|CFO|COO|VP|Director|Manager|Lead|Head of|Founder|Co-founder)',
        r'(Engineer|Developer|Designer|Analyst|Consultant|Specialist)',
        r'(Senior|Principal|Staff|Lead)\s+\w+',
    ]
    
    # Look for company indicators
    company_patterns = [
        r'@(\w+)',  # @company
        r'at\s+([A-Z][a-zA-Z\s&]+)',  # at Company Name
        r'(\w+\s+Inc\.?|\w+\s+LLC|\w+\s+Corp\.?)',  # Company Inc/LLC/Corp
    ]
    
    title = "Professional"
    company = "Unknown Company"
    
    # Extract title
    for pattern in title_patterns:
        match = re.search(pattern, bio, re.IGNORECASE)
        if match:
            title = match.group(0)
            break
    
    # Extract company
    for pattern in company_patterns:
        match = re.search(pattern, bio, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break
    
    return title, company

def _extract_linkedin_from_bio(bio: str) -> Optional[str]:
    """Extract LinkedIn URL from Twitter bio"""
    if not bio:
        return None
    
    # Look for LinkedIn URLs
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
    match = re.search(linkedin_pattern, bio)
    
    return match.group(0) if match else None

def _is_relevant_profile(profile: Dict, query: str) -> bool:
    """Check if profile is relevant to the search query"""
    query_lower = query.lower()
    
    # Check if query terms appear in name, title, or company
    searchable_text = f"{profile.get('name', '')} {profile.get('title', '')} {profile.get('company', '')}".lower()
    
    # Look for key terms
    query_terms = query_lower.split()
    relevant_terms = ['ceo', 'cto', 'founder', 'director', 'manager', 'lead', 'head']
    
    # Check for direct matches
    for term in query_terms:
        if term in searchable_text:
            return True
    
    # Check for relevant job titles
    for term in relevant_terms:
        if term in searchable_text:
            return True
    
    return False

def _fallback_twitter_search(query: str) -> List[Dict]:
    """Fallback to shared Twitter API or mock data"""
    # Try shared Twitter API first
    if TWITTER_BEARER_TOKEN:
        return _shared_api_search(query)
    
    # Mock data fallback
    logging.info(f"Using mock data for Twitter query: {query}")
    return [{
        "name": "Twitter User",
        "title": "Professional",
        "company": "Tech Company",
        "linkedin": None,
        "x_handle": "@twitteruser",
        "source": "fallback",
        "confidence": 0.3,
        "email": None,
        "public_links": ["https://twitter.com/twitteruser"]
    }]

def _shared_api_search(query: str) -> List[Dict]:
    """Search using shared Twitter Bearer Token"""
    profiles = []
    
    try:
        headers = {
            'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Use the same search logic but with shared token
        user_profiles = _search_twitter_users(query, headers)
        profiles.extend(user_profiles)
        
        if len(profiles) < 5:
            tweet_profiles = _search_twitter_tweets(query, headers)
            profiles.extend(tweet_profiles)
            
    except Exception as e:
        logging.error(f"Error in shared Twitter API search: {e}")
    
    return profiles

# Company handle utilities
def extract_twitter_handle(company_info: str, twitter_url: str = None) -> Optional[str]:
    """
    Extract Twitter handle from company info or Twitter URL
    
    Examples:
    - "VoiceFlow AI @voiceflowai" -> "voiceflowai"
    - Twitter URL -> extract handle from URL
    """
    
    if twitter_url and 'twitter.com/' in twitter_url:
        # Extract handle from URL
        handle = twitter_url.split('twitter.com/')[-1].split('?')[0].split('/')[0]
        return handle.replace('@', '')
    
    # Look for @handle in company info
    handle_match = re.search(r'@(\w+)', company_info)
    if handle_match:
        return handle_match.group(1)
    
    return None

def search_company_twitter_handle(company_name: str, user_token: Dict) -> Optional[str]:
    """Search for company's Twitter handle using user token"""
    try:
        access_token = user_token['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Search for company account
        search_url = 'https://api.twitter.com/2/users/search'
        params = {
            'query': company_name,
            'max_results': 5,
            'user.fields': 'description,verified,public_metrics'
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('data', [])
            
            # Look for official company account (verified or high followers)
            for user in users:
                if (user.get('verified') or 
                    user.get('public_metrics', {}).get('followers_count', 0) > 1000):
                    return user.get('username')
                    
    except Exception as e:
        logging.error(f"Error searching for company Twitter handle: {e}")
    
    return None 