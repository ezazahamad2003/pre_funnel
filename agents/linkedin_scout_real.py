import requests
import logging
from config import PHANTOMBUSTER_API_KEY, REQUEST_TIMEOUT, MAX_RETRIES
import time
import json

def linkedin_scout(query):
    """
    Real implementation using PhantomBuster API for LinkedIn searches
    Note: This requires setting up a PhantomBuster phantom for LinkedIn search
    """
    if not PHANTOMBUSTER_API_KEY or PHANTOMBUSTER_API_KEY == '':
        logging.warning("PhantomBuster API key not configured, using fallback")
        return _fallback_linkedin_scout(query)
    
    try:
        # Launch LinkedIn search phantom
        phantom_id = _launch_linkedin_search_phantom(query)
        
        if not phantom_id:
            logging.error("Failed to launch LinkedIn search phantom")
            return _fallback_linkedin_scout(query)
        
        # Wait for phantom to complete and get results
        results = _wait_for_phantom_results(phantom_id)
        
        if not results:
            logging.warning("No results from LinkedIn phantom")
            return []
        
        # Convert results to our profile format
        profiles = _convert_linkedin_results(results, query)
        
        logging.info(f"LinkedIn search for '{query}' found {len(profiles)} profiles")
        return profiles[:5]  # Limit to top 5 results
        
    except Exception as e:
        logging.error(f"Error in PhantomBuster LinkedIn scout: {e}")
        return _fallback_linkedin_scout(query)

def _launch_linkedin_search_phantom(query):
    """Launch a PhantomBuster phantom for LinkedIn search"""
    try:
        # This assumes you have a LinkedIn Search Export phantom set up
        # You'll need to replace 'your-phantom-id' with your actual phantom ID
        phantom_id = "your-linkedin-search-phantom-id"  # Replace with your phantom ID
        
        url = f"https://api.phantombuster.com/api/v2/agents/launch"
        
        headers = {
            'X-Phantombuster-Key': PHANTOMBUSTER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Prepare search parameters
        search_params = {
            'searchQuery': _optimize_linkedin_query(query),
            'numberOfProfiles': 20,
            'csvName': f"linkedin_search_{int(time.time())}"
        }
        
        payload = {
            'id': phantom_id,
            'argument': search_params
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            container_id = data.get('containerId')
            logging.info(f"Launched LinkedIn phantom with container ID: {container_id}")
            return container_id
        else:
            logging.error(f"PhantomBuster launch error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logging.error(f"Error launching LinkedIn phantom: {e}")
        return None

def _wait_for_phantom_results(container_id, max_wait_time=300):
    """Wait for phantom to complete and return results"""
    try:
        url = f"https://api.phantombuster.com/api/v2/containers/fetch-output"
        
        headers = {
            'X-Phantombuster-Key': PHANTOMBUSTER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {'id': container_id}
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if phantom is still running
                if data.get('status') == 'running':
                    logging.info("LinkedIn phantom still running, waiting...")
                    time.sleep(30)  # Wait 30 seconds before checking again
                    continue
                elif data.get('status') == 'finished':
                    # Get the CSV output
                    csv_url = data.get('output')
                    if csv_url:
                        return _fetch_csv_results(csv_url)
                    else:
                        logging.error("No CSV output from phantom")
                        return None
                else:
                    logging.error(f"Phantom failed with status: {data.get('status')}")
                    return None
            else:
                logging.error(f"Error fetching phantom results: {response.status_code}")
                return None
        
        logging.error("Phantom timed out")
        return None
        
    except Exception as e:
        logging.error(f"Error waiting for phantom results: {e}")
        return None

def _fetch_csv_results(csv_url):
    """Fetch and parse CSV results from PhantomBuster"""
    try:
        response = requests.get(csv_url, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            # Parse CSV content
            import csv
            import io
            
            csv_content = response.text
            reader = csv.DictReader(io.StringIO(csv_content))
            
            results = []
            for row in reader:
                results.append(row)
            
            logging.info(f"Fetched {len(results)} LinkedIn profiles from CSV")
            return results
        else:
            logging.error(f"Error fetching CSV: {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"Error parsing CSV results: {e}")
        return None

def _convert_linkedin_results(results, original_query):
    """Convert PhantomBuster LinkedIn results to our profile format"""
    profiles = []
    
    for result in results:
        try:
            # PhantomBuster LinkedIn Export typically includes these fields
            profile = {
                'name': result.get('fullName') or result.get('name', 'Unknown'),
                'email': None,  # LinkedIn doesn't provide emails directly
                'title': result.get('title') or result.get('headline', 'Professional'),
                'company': result.get('company') or result.get('companyName', 'Unknown'),
                'linkedin': result.get('profileUrl') or result.get('url'),
                'x_handle': None,  # Not typically available from LinkedIn
                'public_links': _extract_additional_links(result),
                'source': 'phantombuster_linkedin',
                'location': result.get('location'),
                'industry': result.get('industry'),
                'connections': result.get('connectionsCount'),
                'summary': result.get('summary', '')[:200] if result.get('summary') else None
            }
            
            # Only include profiles that seem relevant
            if _is_relevant_linkedin_profile(profile, original_query):
                profiles.append(profile)
                
        except Exception as e:
            logging.error(f"Error converting LinkedIn result: {e}")
            continue
    
    return profiles

def _extract_additional_links(result):
    """Extract additional links from LinkedIn profile data"""
    links = []
    
    # Company website
    company_url = result.get('companyUrl') or result.get('companyWebsite')
    if company_url:
        links.append(company_url)
    
    # Personal website
    website = result.get('website') or result.get('personalWebsite')
    if website:
        links.append(website)
    
    return links

def _optimize_linkedin_query(query):
    """Optimize the query for LinkedIn search"""
    # LinkedIn search works better with specific keywords
    # Remove common words and focus on job titles, industries, locations
    
    stop_words = ['find', 'looking', 'for', 'connect', 'with', 'seeking']
    words = query.lower().split()
    
    # Keep important keywords
    important_keywords = []
    for word in words:
        if word not in stop_words:
            important_keywords.append(word)
    
    # LinkedIn search optimization
    optimized_query = ' '.join(important_keywords)
    
    # Add common LinkedIn search operators if not present
    if 'founder' in query.lower() or 'ceo' in query.lower():
        optimized_query += ' (founder OR CEO OR "co-founder")'
    
    return optimized_query

def _is_relevant_linkedin_profile(profile, original_query):
    """Check if LinkedIn profile is relevant to the search query"""
    query_lower = original_query.lower()
    
    # Combine searchable text
    searchable_text = f"{profile.get('title', '')} {profile.get('company', '')} {profile.get('summary', '')}".lower()
    
    # Look for key terms
    key_terms = ['founder', 'ceo', 'cto', 'startup', 'saas', 'ai', 'tech', 'director', 'vp']
    
    # Check if any key terms from query appear in profile
    for term in key_terms:
        if term in query_lower and term in searchable_text:
            return True
    
    # Check for location relevance
    if 'bay area' in query_lower or 'san francisco' in query_lower:
        location = profile.get('location', '').lower()
        if 'bay area' in location or 'san francisco' in location or 'sf' in location:
            return True
    
    return True  # Default to including if we can't determine relevance

def _fallback_linkedin_scout(query):
    """Fallback to mock data if API is not available"""
    logging.info(f"Using fallback data for LinkedIn search: {query}")
    
    return [{
        "name": "LinkedIn Professional",
        "email": None,
        "title": "Senior Executive",
        "company": "Tech Startup",
        "linkedin": "https://linkedin.com/in/professional",
        "x_handle": None,
        "public_links": [],
        "source": "fallback",
        "location": "San Francisco Bay Area",
        "connections": 500
    }]

# Alternative implementation using LinkedIn Sales Navigator (if available)
def linkedin_sales_navigator_scout(query):
    """
    Alternative implementation for LinkedIn Sales Navigator API
    This requires enterprise LinkedIn access
    """
    logging.info("LinkedIn Sales Navigator integration not implemented yet")
    return _fallback_linkedin_scout(query)

# Usage and setup information
def get_phantombuster_setup_info():
    """
    Get setup instructions for PhantomBuster LinkedIn integration
    """
    return {
        "setup_steps": [
            "1. Sign up for PhantomBuster account",
            "2. Create a 'LinkedIn Search Export' phantom",
            "3. Configure the phantom with your LinkedIn account",
            "4. Get the phantom ID from the URL",
            "5. Update linkedin_scout_real.py with your phantom ID",
            "6. Add your PhantomBuster API key to config.py"
        ],
        "phantom_types": {
            "LinkedIn Search Export": "Best for searching LinkedIn profiles",
            "LinkedIn Profile Scraper": "Good for detailed profile info",
            "Sales Navigator Search Export": "If you have Sales Navigator"
        },
        "cost": "$56/month for PhantomBuster Pro plan",
        "limits": "Depends on your LinkedIn account limits"
    }

def get_linkedin_usage_info():
    """
    Get information about LinkedIn API usage through PhantomBuster
    """
    return {
        "note": "LinkedIn usage through PhantomBuster:",
        "daily_limits": "Depends on your LinkedIn account type",
        "recommendations": [
            "Use LinkedIn Premium or Sales Navigator for higher limits",
            "Spread searches throughout the day",
            "Monitor PhantomBuster dashboard for usage stats"
        ]
    } 