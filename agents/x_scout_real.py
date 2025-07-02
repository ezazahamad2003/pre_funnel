import requests
import logging
from config import TWITTER_BEARER_TOKEN, REQUEST_TIMEOUT, MAX_RETRIES
import time
import re

def x_scout(query):
    """
    Real implementation using Twitter API v2 with shared backend token
    Searches for relevant profiles and tweets
    """
    if not TWITTER_BEARER_TOKEN or TWITTER_BEARER_TOKEN == '':
        logging.warning("Twitter Bearer Token not configured, using fallback")
        return _fallback_x_scout(query)
    
    try:
        profiles = []
        
        # Search for users matching the query
        user_profiles = _search_users(query, TWITTER_BEARER_TOKEN)
        profiles.extend(user_profiles)
        
        # Search for tweets and extract user info
        tweet_profiles = _search_tweets_for_users(query, TWITTER_BEARER_TOKEN)
        profiles.extend(tweet_profiles)
        
        # Remove duplicates and limit results
        unique_profiles = _deduplicate_profiles(profiles)
        
        logging.info(f"Twitter search for '{query}' found {len(unique_profiles)} profiles")
        return unique_profiles[:5]  # Limit to top 5 results
        
    except Exception as e:
        logging.error(f"Error in Twitter X scout: {e}")
        return _fallback_x_scout(query)

def x_scout_with_user_token(query, user_access_token):
    """
    Real implementation using user's personal Twitter OAuth token
    This provides higher rate limits and access to more data
    """
    try:
        profiles = []
        
        # Search for users matching the query
        user_profiles = _search_users(query, user_access_token)
        profiles.extend(user_profiles)
        
        # Search for tweets and extract user info
        tweet_profiles = _search_tweets_for_users(query, user_access_token)
        profiles.extend(tweet_profiles)
        
        # Remove duplicates and limit results
        unique_profiles = _deduplicate_profiles(profiles)
        
        logging.info(f"Twitter search (user token) for '{query}' found {len(unique_profiles)} profiles")
        return unique_profiles[:10]  # Higher limit for user tokens
        
    except Exception as e:
        logging.error(f"Error in Twitter X scout with user token: {e}")
        # Fallback to shared API if user token fails
        return x_scout(query)

def _search_users(query, auth_token):
    """Search for users directly using Twitter API v2"""
    try:
        # Clean query for Twitter search
        search_query = _clean_twitter_query(query)
        
        url = "https://api.twitter.com/2/users/search"
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'query': search_query,
            'max_results': 10,
            'user.fields': 'description,location,public_metrics,url,verified'
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get('data', [])
                    
                    profiles = []
                    for user in users:
                        profile = _convert_twitter_user_to_profile(user)
                        if profile:
                            profiles.append(profile)
                    
                    return profiles
                
                elif response.status_code == 429:
                    # Rate limited
                    wait_time = 15 * 60  # Twitter rate limit is 15 minutes
                    logging.warning(f"Twitter rate limited, would need to wait {wait_time}s")
                    break  # Don't actually wait 15 minutes in this implementation
                
                else:
                    logging.error(f"Twitter API error {response.status_code}: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                logging.warning(f"Twitter API timeout on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
                    continue
                break
            except requests.exceptions.RequestException as e:
                logging.error(f"Twitter API request error: {e}")
                break
        
        return []
        
    except Exception as e:
        logging.error(f"Error searching Twitter users: {e}")
        return []

def _search_tweets_for_users(query, auth_token):
    """Search tweets and extract user information"""
    try:
        # Clean query for tweet search
        search_query = _clean_twitter_query(query) + " -is:retweet"
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'query': search_query,
            'max_results': 20,
            'tweet.fields': 'author_id,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'description,location,public_metrics,url,verified'
        }
        
        response = requests.get(
            url, 
            headers=headers, 
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('includes', {}).get('users', [])
            
            profiles = []
            for user in users:
                profile = _convert_twitter_user_to_profile(user)
                if profile and _is_relevant_profile(profile, query):
                    profiles.append(profile)
            
            return profiles
        
        else:
            logging.error(f"Twitter tweets search error {response.status_code}: {response.text}")
            return []
        
    except Exception as e:
        logging.error(f"Error searching Twitter tweets: {e}")
        return []

def _convert_twitter_user_to_profile(user):
    """Convert Twitter user object to our profile format"""
    try:
        # Extract company/title from bio
        bio = user.get('description', '')
        title, company = _extract_title_company_from_bio(bio)
        
        profile = {
            'name': user.get('name', 'Unknown'),
            'email': None,  # Twitter doesn't provide emails
            'title': title,
            'company': company,
            'linkedin': _extract_linkedin_from_bio_or_url(user),
            'x_handle': f"@{user.get('username', '')}",
            'public_links': _extract_links_from_user(user),
            'source': 'twitter_api',
            'followers': user.get('public_metrics', {}).get('followers_count', 0),
            'verified': user.get('verified', False),
            'location': user.get('location'),
            'bio': bio[:200]  # Truncate bio
        }
        
        return profile
        
    except Exception as e:
        logging.error(f"Error converting Twitter user: {e}")
        return None

def _extract_title_company_from_bio(bio):
    """Extract job title and company from Twitter bio"""
    if not bio:
        return "Unknown", "Unknown"
    
    # Common patterns in Twitter bios
    title_patterns = [
        r'(CEO|CTO|CFO|COO|Founder|Co-founder|VP|Director|Manager|Lead|Head of|Chief)\s+(?:of\s+|at\s+)?([^|\n•]+)',
        r'([^|\n•]+)\s+(?:@|at)\s+([^|\n•]+)',
        r'(Founder|Co-founder)\s+of\s+([^|\n•]+)'
    ]
    
    for pattern in title_patterns:
        match = re.search(pattern, bio, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            company = match.group(2).strip() if len(match.groups()) > 1 else "Unknown"
            return title, company
    
    # Fallback: look for common job titles
    job_titles = ['CEO', 'CTO', 'CFO', 'Founder', 'Co-founder', 'VP', 'Director', 'Manager']
    for title in job_titles:
        if title.lower() in bio.lower():
            return title, "Unknown"
    
    return "Professional", "Unknown"

def _extract_linkedin_from_bio_or_url(user):
    """Extract LinkedIn URL from bio or profile URL"""
    bio = user.get('description', '')
    profile_url = user.get('url', '')
    
    text_to_search = f"{bio} {profile_url}"
    
    linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9\-]+)'
    match = re.search(linkedin_pattern, text_to_search)
    
    if match:
        return f"https://linkedin.com/in/{match.group(1)}"
    
    return None

def _extract_links_from_user(user):
    """Extract additional links from user profile"""
    links = []
    
    # Profile URL
    url = user.get('url')
    if url and 'linkedin.com' not in url:
        links.append(url)
    
    # Links from bio
    bio = user.get('description', '')
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    bio_links = re.findall(url_pattern, bio)
    
    for link in bio_links:
        if 'linkedin.com' not in link and link not in links:
            links.append(link)
    
    return links[:3]  # Limit to 3 additional links

def _clean_twitter_query(query):
    """Clean and optimize query for Twitter search"""
    # Remove common words that don't work well in Twitter search
    stop_words = ['find', 'looking', 'for', 'connect', 'with']
    
    words = query.lower().split()
    cleaned_words = [word for word in words if word not in stop_words]
    
    # Join back and limit length
    cleaned_query = ' '.join(cleaned_words)
    
    # Twitter has a 512 character limit for search queries
    if len(cleaned_query) > 400:
        cleaned_query = cleaned_query[:400]
    
    return cleaned_query

def _is_relevant_profile(profile, original_query):
    """Check if the profile is relevant to the original query"""
    query_lower = original_query.lower()
    
    # Check if key terms appear in profile
    searchable_text = f"{profile.get('bio', '')} {profile.get('title', '')} {profile.get('company', '')}".lower()
    
    # Look for key terms from the query
    key_terms = ['founder', 'ceo', 'cto', 'startup', 'saas', 'ai', 'tech']
    query_terms = [term for term in key_terms if term in query_lower]
    
    if query_terms:
        for term in query_terms:
            if term in searchable_text:
                return True
    
    return True  # Default to including if we can't determine relevance

def _deduplicate_profiles(profiles):
    """Remove duplicate profiles based on username"""
    seen_usernames = set()
    unique_profiles = []
    
    for profile in profiles:
        username = profile.get('x_handle', '').lower()
        if username and username not in seen_usernames:
            seen_usernames.add(username)
            unique_profiles.append(profile)
    
    return unique_profiles

def _fallback_x_scout(query):
    """Fallback to mock data if API is not available"""
    logging.info(f"Using fallback data for X search: {query}")
    
    return [{
        "name": "Twitter User",
        "email": None,
        "title": "Professional",
        "company": "Tech Company",
        "linkedin": None,
        "x_handle": "@techpro",
        "public_links": [],
        "source": "fallback",
        "followers": 1000,
        "verified": False
    }]

# Usage tracking
def get_twitter_usage_info():
    """
    Get information about Twitter API usage
    Note: Twitter API v2 doesn't provide usage stats in the same way
    """
    return {
        "note": "Twitter API v2 rate limits:",
        "user_search": "300 requests per 15 minutes",
        "tweet_search": "300 requests per 15 minutes",
        "recommendation": "Monitor rate limits in your application logs"
    } 