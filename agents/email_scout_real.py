import requests
import logging
from config import PEOPLE_DATA_LABS_API_KEY, REQUEST_TIMEOUT, MAX_RETRIES
import time

def scout_from_email(email):
    """
    Real implementation using People Data Labs API
    Converts email address to enriched profile data
    """
    if not PEOPLE_DATA_LABS_API_KEY or PEOPLE_DATA_LABS_API_KEY == '':
        logging.warning("People Data Labs API key not configured, using fallback")
        return _fallback_email_scout(email)
    
    try:
        # People Data Labs Person Enrichment API
        url = "https://api.peopledatalabs.com/v5/person/enrich"
        
        headers = {
            'X-Api-Key': PEOPLE_DATA_LABS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        params = {
            'email': email,
            'required': 'emails',
            'min_likelihood': 6  # High confidence matches only
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
                    
                    if data.get('status') == 200 and data.get('data'):
                        person = data['data']
                        
                        # Extract profile information
                        profile = {
                            'name': _get_full_name(person),
                            'email': email,
                            'title': _get_job_title(person),
                            'company': _get_company_name(person),
                            'linkedin': _get_linkedin_url(person),
                            'x_handle': _get_twitter_handle(person),
                            'public_links': _get_public_links(person),
                            'source': 'people_data_labs',
                            'confidence': person.get('likelihood', 0)
                        }
                        
                        logging.info(f"Successfully enriched email: {email}")
                        return [profile]
                
                elif response.status_code == 404:
                    logging.info(f"No profile found for email: {email}")
                    return []
                
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt
                    logging.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                
                else:
                    logging.error(f"PDL API error {response.status_code}: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                logging.warning(f"PDL API timeout on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                break
            except requests.exceptions.RequestException as e:
                logging.error(f"PDL API request error: {e}")
                break
        
        # If all retries failed, return empty
        return []
        
    except Exception as e:
        logging.error(f"Error in People Data Labs email scout: {e}")
        return _fallback_email_scout(email)

def _get_full_name(person):
    """Extract full name from PDL response"""
    if person.get('full_name'):
        return person['full_name']
    
    first = person.get('first_name', '')
    last = person.get('last_name', '')
    
    if first and last:
        return f"{first} {last}"
    elif first:
        return first
    elif last:
        return last
    else:
        return "Unknown"

def _get_job_title(person):
    """Extract current job title from PDL response"""
    experience = person.get('experience', [])
    
    if experience:
        # Get the most recent job (first in the list)
        current_job = experience[0]
        title = current_job.get('title')
        if title:
            return title
    
    return "Unknown"

def _get_company_name(person):
    """Extract current company from PDL response"""
    experience = person.get('experience', [])
    
    if experience:
        current_job = experience[0]
        company = current_job.get('company', {})
        company_name = company.get('name')
        if company_name:
            return company_name
    
    return "Unknown"

def _get_linkedin_url(person):
    """Extract LinkedIn URL from PDL response"""
    profiles = person.get('profiles', [])
    
    for profile in profiles:
        if profile.get('network') == 'linkedin':
            return profile.get('url')
    
    return None

def _get_twitter_handle(person):
    """Extract Twitter handle from PDL response"""
    profiles = person.get('profiles', [])
    
    for profile in profiles:
        if profile.get('network') == 'twitter':
            url = profile.get('url', '')
            # Extract handle from URL
            if 'twitter.com/' in url:
                handle = url.split('twitter.com/')[-1].split('?')[0].split('/')[0]
                return f"@{handle}" if not handle.startswith('@') else handle
    
    return None

def _get_public_links(person):
    """Extract other public profile links"""
    profiles = person.get('profiles', [])
    links = []
    
    excluded_networks = ['linkedin', 'twitter', 'email']
    
    for profile in profiles:
        network = profile.get('network', '').lower()
        url = profile.get('url')
        
        if url and network not in excluded_networks:
            links.append(url)
    
    return links[:3]  # Limit to top 3 additional links

def _fallback_email_scout(email):
    """Fallback to mock data if API is not available"""
    logging.info(f"Using fallback data for email: {email}")
    
    return [{
        "name": "Unknown User",
        "email": email,
        "title": "Professional",
        "company": "Unknown Company",
        "linkedin": None,
        "x_handle": None,
        "public_links": [],
        "source": "fallback",
        "confidence": 0
    }]

# Usage tracking
def get_usage_stats():
    """
    Check your People Data Labs usage
    Call this periodically to monitor API consumption
    """
    if not PEOPLE_DATA_LABS_API_KEY:
        return {"error": "API key not configured"}
    
    try:
        url = "https://api.peopledatalabs.com/v5/stats"
        headers = {'X-Api-Key': PEOPLE_DATA_LABS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}: {response.text}"}
            
    except Exception as e:
        return {"error": str(e)} 