import requests
import logging
from config import GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID, REQUEST_TIMEOUT, MAX_RETRIES
import time
import re
from urllib.parse import urlparse

def internet_scout(query):
    """
    Real implementation using Google Custom Search Engine API
    Searches the web for relevant company and profile information
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID or GOOGLE_CSE_API_KEY == '' or GOOGLE_CSE_ID == '':
        logging.warning("Google CSE API key or ID not configured, using fallback")
        return _fallback_internet_scout(query)
    
    try:
        profiles = []
        
        # Search for company websites and profiles
        company_results = _search_companies(query)
        profiles.extend(company_results)
        
        # Search for individual profiles and bios
        profile_results = _search_profiles(query)
        profiles.extend(profile_results)
        
        # Remove duplicates and limit results
        unique_profiles = _deduplicate_by_domain(profiles)
        
        logging.info(f"Google search for '{query}' found {len(unique_profiles)} profiles")
        return unique_profiles[:5]  # Limit to top 5 results
        
    except Exception as e:
        logging.error(f"Error in Google internet scout: {e}")
        return _fallback_internet_scout(query)

def _search_companies(query):
    """Search for company websites and team pages"""
    try:
        # Focus on company websites and team pages
        search_query = f"{query} site:angel.co OR site:crunchbase.com OR \"team\" OR \"about us\" OR \"leadership\""
        
        results = _perform_google_search(search_query)
        profiles = []
        
        for result in results:
            profile = _extract_company_info(result, query)
            if profile:
                profiles.append(profile)
        
        return profiles
        
    except Exception as e:
        logging.error(f"Error searching companies: {e}")
        return []

def _search_profiles(query):
    """Search for individual profiles and bios"""
    try:
        # Focus on individual profiles
        search_query = f"{query} \"founder\" OR \"CEO\" OR \"CTO\" site:linkedin.com OR site:about.me OR \"bio\""
        
        results = _perform_google_search(search_query)
        profiles = []
        
        for result in results:
            profile = _extract_profile_info(result, query)
            if profile:
                profiles.append(profile)
        
        return profiles
        
    except Exception as e:
        logging.error(f"Error searching profiles: {e}")
        return []

def _perform_google_search(query):
    """Perform the actual Google Custom Search API call"""
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            'key': GOOGLE_CSE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': 10,  # Number of results per query
            'fields': 'items(title,link,snippet,displayLink)'
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('items', [])
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt
                    logging.warning(f"Google CSE rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 403:
                    logging.error("Google CSE quota exceeded or API key invalid")
                    break
                
                else:
                    logging.error(f"Google CSE API error {response.status_code}: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                logging.warning(f"Google CSE timeout on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                break
            except requests.exceptions.RequestException as e:
                logging.error(f"Google CSE request error: {e}")
                break
        
        return []
        
    except Exception as e:
        logging.error(f"Error performing Google search: {e}")
        return []

def _extract_company_info(result, original_query):
    """Extract company information from search result"""
    try:
        title = result.get('title', '')
        link = result.get('link', '')
        snippet = result.get('snippet', '')
        domain = result.get('displayLink', '')
        
        # Determine if this is a company page
        company_indicators = ['about', 'team', 'leadership', 'founders', 'company']
        is_company_page = any(indicator in title.lower() or indicator in link.lower() 
                             for indicator in company_indicators)
        
        if not is_company_page and 'crunchbase.com' not in domain and 'angel.co' not in domain:
            return None
        
        # Extract company name
        company_name = _extract_company_name_from_result(title, link, domain)
        
        # Try to extract founder/leader info from snippet
        name, title_role = _extract_person_from_snippet(snippet)
        
        if not name:
            name = "Company Representative"
            title_role = "Team Member"
        
        profile = {
            'name': name,
            'email': None,
            'title': title_role,
            'company': company_name,
            'linkedin': _extract_linkedin_from_text(snippet),
            'x_handle': _extract_twitter_from_text(snippet),
            'public_links': [link],
            'source': 'google_search',
            'domain': domain,
            'snippet': snippet[:200]
        }
        
        return profile
        
    except Exception as e:
        logging.error(f"Error extracting company info: {e}")
        return None

def _extract_profile_info(result, original_query):
    """Extract individual profile information from search result"""
    try:
        title = result.get('title', '')
        link = result.get('link', '')
        snippet = result.get('snippet', '')
        domain = result.get('displayLink', '')
        
        # Extract person name and title
        name, title_role = _extract_person_from_snippet(f"{title} {snippet}")
        
        if not name or name == "Unknown":
            # Try to extract from title
            name = _extract_name_from_title(title)
        
        # Extract company from snippet or title
        company = _extract_company_from_text(f"{title} {snippet}")
        
        profile = {
            'name': name or "Professional",
            'email': None,
            'title': title_role or "Professional",
            'company': company or "Unknown",
            'linkedin': link if 'linkedin.com' in link else _extract_linkedin_from_text(snippet),
            'x_handle': _extract_twitter_from_text(snippet),
            'public_links': [link] if 'linkedin.com' not in link else [],
            'source': 'google_search',
            'domain': domain,
            'snippet': snippet[:200]
        }
        
        return profile
        
    except Exception as e:
        logging.error(f"Error extracting profile info: {e}")
        return None

def _extract_company_name_from_result(title, link, domain):
    """Extract company name from search result"""
    # Try domain first
    if domain and domain not in ['linkedin.com', 'twitter.com', 'facebook.com']:
        # Clean up domain name
        company = domain.replace('www.', '').replace('.com', '').replace('.co', '').replace('.io', '')
        return company.title()
    
    # Try to extract from title
    if 'about' in title.lower():
        # "About XYZ Company" -> "XYZ Company"
        match = re.search(r'about\s+(.+?)(?:\s*-|\s*\||\s*$)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Fallback to domain
    return domain or "Unknown Company"

def _extract_person_from_snippet(text):
    """Extract person name and title from text"""
    if not text:
        return None, None
    
    # Common patterns for name and title
    patterns = [
        r'([\w\s]+),\s*(CEO|CTO|CFO|COO|Founder|Co-founder|VP|Director|Manager|Lead|Head of)',
        r'(CEO|CTO|CFO|COO|Founder|Co-founder|VP|Director|Manager|Lead|Head of)\s+([\w\s]+)',
        r'([\w\s]+)\s+is\s+(?:the\s+)?(CEO|CTO|CFO|COO|Founder|Co-founder|VP|Director)',
        r'([\w\s]+)\s+-\s+(CEO|CTO|CFO|COO|Founder|Co-founder|VP|Director)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                # Determine which group is name vs title
                if any(title in groups[0].lower() for title in ['ceo', 'cto', 'founder', 'director']):
                    return groups[1].strip(), groups[0].strip()
                else:
                    return groups[0].strip(), groups[1].strip()
    
    return None, None

def _extract_name_from_title(title):
    """Extract person name from page title"""
    # Remove common suffixes
    title = re.sub(r'\s*-\s*LinkedIn.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\|\s*.*$', '', title)
    
    # Look for name patterns
    name_pattern = r'^([A-Z][a-z]+\s+[A-Z][a-z]+)'
    match = re.search(name_pattern, title)
    
    if match:
        return match.group(1)
    
    return None

def _extract_company_from_text(text):
    """Extract company name from text"""
    if not text:
        return None
    
    # Common patterns
    patterns = [
        r'at\s+([A-Z][a-zA-Z\s&]+?)(?:\s*-|\s*\||\s*,|\s*$)',
        r'works?\s+at\s+([A-Z][a-zA-Z\s&]+?)(?:\s*-|\s*\||\s*,|\s*$)',
        r'founder\s+of\s+([A-Z][a-zA-Z\s&]+?)(?:\s*-|\s*\||\s*,|\s*$)',
        r'CEO\s+of\s+([A-Z][a-zA-Z\s&]+?)(?:\s*-|\s*\||\s*,|\s*$)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 50:  # Reasonable company name length
                return company
    
    return None

def _extract_linkedin_from_text(text):
    """Extract LinkedIn URL from text"""
    if not text:
        return None
    
    pattern = r'linkedin\.com/in/([a-zA-Z0-9\-]+)'
    match = re.search(pattern, text)
    
    if match:
        return f"https://linkedin.com/in/{match.group(1)}"
    
    return None

def _extract_twitter_from_text(text):
    """Extract Twitter handle from text"""
    if not text:
        return None
    
    patterns = [
        r'@([a-zA-Z0-9_]+)',
        r'twitter\.com/([a-zA-Z0-9_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            handle = match.group(1)
            return f"@{handle}" if not handle.startswith('@') else handle
    
    return None

def _deduplicate_by_domain(profiles):
    """Remove duplicate profiles based on domain"""
    seen_domains = set()
    unique_profiles = []
    
    for profile in profiles:
        domain = profile.get('domain', '')
        link = profile.get('public_links', [])
        
        # Create a unique key
        key = domain
        if link:
            parsed = urlparse(link[0])
            key = parsed.netloc
        
        if key and key not in seen_domains:
            seen_domains.add(key)
            unique_profiles.append(profile)
    
    return unique_profiles

def _fallback_internet_scout(query):
    """Fallback to mock data if API is not available"""
    logging.info(f"Using fallback data for internet search: {query}")
    
    return [{
        "name": "Web Professional",
        "email": None,
        "title": "Industry Expert",
        "company": "Tech Company",
        "linkedin": None,
        "x_handle": None,
        "public_links": ["https://example.com"],
        "source": "fallback",
        "domain": "example.com"
    }]

# Usage tracking
def get_google_usage_info():
    """
    Get information about Google CSE usage
    """
    return {
        "note": "Google Custom Search Engine limits:",
        "free_tier": "100 searches per day",
        "paid_tier": "$5 per 1,000 queries after free limit",
        "recommendation": "Monitor usage in Google Cloud Console"
    } 