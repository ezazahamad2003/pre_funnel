import requests
import logging
import json
from typing import List, Dict, Optional
from user_auth import auth_manager
from config import PHANTOMBUSTER_API_KEY

def linkedin_scout_enhanced(query: str, user_id: Optional[str] = None, company_handle: Optional[str] = None) -> List[Dict]:
    """
    Enhanced LinkedIn scout with user OAuth tokens for deep search
    
    Features:
    - User's LinkedIn token for authenticated searches
    - Company employee searches
    - Advanced profile filtering
    - Connection insights
    - Fallback to PhantomBuster/mock data
    """
    
    # Try user's LinkedIn token first
    if user_id:
        user_token = auth_manager.get_user_token(user_id, 'linkedin')
        if user_token:
            profiles = _search_with_user_token(query, user_token, company_handle)
            if profiles:
                return profiles
    
    # Fallback to PhantomBuster or mock
    return _fallback_linkedin_search(query)

def _search_with_user_token(query: str, token_data: Dict, company_handle: Optional[str]) -> List[Dict]:
    """Search LinkedIn using user's OAuth token"""
    access_token = token_data['access_token']
    profiles = []
    
    try:
        # Track API usage
        auth_manager.track_api_usage(token_data.get('user_id'), 'linkedin', 'profile_search')
        
        # LinkedIn API v2 - People Search
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Search for people
        search_url = 'https://api.linkedin.com/v2/people-search'
        params = {
            'keywords': query,
            'start': 0,
            'count': 10
        }
        
        # Add company filter if handle provided
        if company_handle:
            params['currentCompany'] = company_handle
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            for person in data.get('elements', []):
                profile = _parse_linkedin_profile(person)
                if profile:
                    profiles.append(profile)
                    
        elif response.status_code == 403:
            logging.warning("LinkedIn API access denied - insufficient permissions")
            
        # Also search company employees if company_handle provided
        if company_handle and len(profiles) < 5:
            company_profiles = _search_company_employees(access_token, company_handle)
            profiles.extend(company_profiles)
            
    except Exception as e:
        logging.error(f"Error in LinkedIn user token search: {e}")
    
    return profiles

def _search_company_employees(access_token: str, company_handle: str) -> List[Dict]:
    """Search for company employees using LinkedIn API"""
    profiles = []
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get company info first
        company_url = f'https://api.linkedin.com/v2/companies/{company_handle}'
        company_response = requests.get(company_url, headers=headers, timeout=10)
        
        if company_response.status_code == 200:
            company_data = company_response.json()
            company_name = company_data.get('name', company_handle)
            
            # Search for employees
            search_url = 'https://api.linkedin.com/v2/people-search'
            params = {
                'currentCompany': company_handle,
                'start': 0,
                'count': 10,
                'facets': ['currentCompany']
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for person in data.get('elements', []):
                    profile = _parse_linkedin_profile(person, company_name)
                    if profile:
                        profiles.append(profile)
                        
    except Exception as e:
        logging.error(f"Error searching company employees: {e}")
    
    return profiles

def _parse_linkedin_profile(person_data: Dict, default_company: str = None) -> Optional[Dict]:
    """Parse LinkedIn API person data into our profile format"""
    try:
        # Extract basic info
        first_name = person_data.get('firstName', {}).get('localized', {}).get('en_US', '')
        last_name = person_data.get('lastName', {}).get('localized', {}).get('en_US', '')
        name = f"{first_name} {last_name}".strip()
        
        if not name:
            return None
        
        # Extract current position
        positions = person_data.get('positions', {}).get('values', [])
        current_position = None
        current_company = default_company
        
        if positions:
            current_position = positions[0]  # Most recent position
            title = current_position.get('title', 'Professional')
            
            company_info = current_position.get('company', {})
            if company_info:
                current_company = company_info.get('name', default_company)
        
        # Build LinkedIn URL
        public_profile = person_data.get('publicProfileUrl', '')
        linkedin_url = public_profile if public_profile else None
        
        profile = {
            'name': name,
            'title': title if 'title' in locals() else 'Professional',
            'company': current_company or 'Unknown Company',
            'linkedin': linkedin_url,
            'source': 'linkedin_oauth',
            'confidence': 0.9,  # High confidence for OAuth data
            'x_handle': None,
            'email': None,
            'public_links': []
        }
        
        # Add industry if available
        if person_data.get('industry'):
            profile['industry'] = person_data['industry']
        
        # Add location if available
        location = person_data.get('location', {})
        if location:
            profile['location'] = location.get('name', '')
        
        return profile
        
    except Exception as e:
        logging.error(f"Error parsing LinkedIn profile: {e}")
        return None

def _fallback_linkedin_search(query: str) -> List[Dict]:
    """Fallback to PhantomBuster or mock data"""
    # Try PhantomBuster first
    if PHANTOMBUSTER_API_KEY:
        return _phantombuster_search(query)
    
    # Mock data fallback
    logging.info(f"Using mock data for LinkedIn query: {query}")
    return [{
        "name": "LinkedIn Professional",
        "title": "Senior Executive", 
        "company": "Tech Startup",
        "linkedin": "https://linkedin.com/in/professional",
        "source": "fallback",
        "confidence": 0.3,
        "x_handle": None,
        "email": None,
        "public_links": []
    }]

def _phantombuster_search(query: str) -> List[Dict]:
    """PhantomBuster LinkedIn search (existing functionality)"""
    # This would be the existing PhantomBuster integration
    # For now, return mock data
    logging.warning("PhantomBuster integration not implemented yet")
    return []

# Company handle extraction utilities
def extract_linkedin_company_handle(company_info: str, linkedin_url: str = None) -> Optional[str]:
    """
    Extract LinkedIn company handle from company info or LinkedIn URL
    
    Examples:
    - "VoiceFlow AI" -> search for company and return handle
    - LinkedIn URL -> extract handle from URL
    """
    
    if linkedin_url and 'linkedin.com/company/' in linkedin_url:
        # Extract handle from URL
        handle = linkedin_url.split('linkedin.com/company/')[-1].split('/')[0]
        return handle
    
    # For company name, would need LinkedIn Company Search API
    # This requires additional API permissions
    return None

def get_company_linkedin_handle(company_name: str, user_token: Dict) -> Optional[str]:
    """Search for company's LinkedIn handle using user token"""
    try:
        access_token = user_token['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # LinkedIn Company Search
        search_url = 'https://api.linkedin.com/v2/companySearch'
        params = {
            'keywords': company_name,
            'start': 0,
            'count': 5
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            companies = data.get('elements', [])
            
            if companies:
                # Return the first match
                company = companies[0]
                return str(company.get('id', ''))
                
    except Exception as e:
        logging.error(f"Error searching for company LinkedIn handle: {e}")
    
    return None 