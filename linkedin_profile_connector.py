import requests
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
import logging

class LinkedInProfileConnector:
    """
    Custom LinkedIn profile connector for Pre-Funnel
    
    Since Firebase doesn't support LinkedIn auth, this allows users to:
    1. Input their LinkedIn profile URL
    2. Extract their company and connections info
    3. Use this for enhanced 1st/2nd degree scouting
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def validate_linkedin_url(self, url: str) -> bool:
        """Validate if URL is a valid LinkedIn profile"""
        try:
            parsed = urlparse(url)
            return (parsed.netloc in ['linkedin.com', 'www.linkedin.com'] and 
                   '/in/' in parsed.path)
        except:
            return False
    
    def extract_profile_info(self, linkedin_url: str) -> Dict:
        """
        Extract basic profile information from LinkedIn URL
        
        Note: This uses public data only, respecting LinkedIn's terms
        """
        if not self.validate_linkedin_url(linkedin_url):
            return {'error': 'Invalid LinkedIn URL'}
        
        try:
            # Extract profile identifier from URL
            profile_match = re.search(r'/in/([^/?]+)', linkedin_url)
            if not profile_match:
                return {'error': 'Could not extract profile ID'}
            
            profile_id = profile_match.group(1)
            
            # Basic profile info (this would be enhanced with actual scraping)
            profile_info = {
                'profile_id': profile_id,
                'profile_url': linkedin_url,
                'status': 'connected',
                'connection_type': 'self',
                'data_source': 'user_provided'
            }
            
            logging.info(f"LinkedIn profile connected: {profile_id}")
            return profile_info
            
        except Exception as e:
            logging.error(f"Error extracting LinkedIn profile: {e}")
            return {'error': str(e)}
    
    def suggest_connection_searches(self, profile_info: Dict, target_company: str) -> List[Dict]:
        """
        Generate search suggestions based on user's LinkedIn profile
        
        This creates enhanced search queries for finding 1st/2nd degree connections
        """
        profile_id = profile_info.get('profile_id', '')
        
        # Enhanced search strategies based on LinkedIn profile
        search_suggestions = [
            {
                'type': '1st_degree',
                'description': f'Direct connections from {profile_id}',
                'search_query': f'site:linkedin.com/in/ "{target_company}" -"{profile_id}"',
                'confidence': 0.8,
                'reasoning': 'People who work at target company and might be connected'
            },
            {
                'type': '2nd_degree', 
                'description': f'Connections of connections from {profile_id}',
                'search_query': f'linkedin.com "{target_company}" "mutual connections"',
                'confidence': 0.6,
                'reasoning': 'Potential 2nd degree connections through mutual contacts'
            },
            {
                'type': 'company_employees',
                'description': f'Current employees at {target_company}',
                'search_query': f'site:linkedin.com/in/ "{target_company}" "current"',
                'confidence': 0.9,
                'reasoning': 'Current employees who might be reachable through network'
            }
        ]
        
        return search_suggestions

class TwitterProfileConnector:
    """
    Enhanced Twitter profile connector for social graph analysis
    """
    
    def __init__(self):
        self.api_key = None  # Will be set from Firebase auth or manual input
    
    def validate_twitter_handle(self, handle: str) -> bool:
        """Validate Twitter handle format"""
        # Remove @ if present
        handle = handle.lstrip('@')
        return bool(re.match(r'^[A-Za-z0-9_]{1,15}$', handle))
    
    def extract_social_graph_searches(self, twitter_handle: str, target_company: str) -> List[Dict]:
        """
        Generate social graph search strategies based on Twitter profile
        """
        handle = twitter_handle.lstrip('@')
        
        search_strategies = [
            {
                'type': 'followers_at_company',
                'description': f'Followers of @{handle} who work at {target_company}',
                'search_query': f'from:{handle} followers "{target_company}"',
                'confidence': 0.8,
                'reasoning': 'Your followers who work at target company'
            },
            {
                'type': 'following_at_company', 
                'description': f'People @{handle} follows at {target_company}',
                'search_query': f'to:{handle} following "{target_company}"',
                'confidence': 0.7,
                'reasoning': 'People you follow who work at target company'
            },
            {
                'type': 'mentions_analysis',
                'description': f'People who mention @{handle} and work at {target_company}',
                'search_query': f'@{handle} "{target_company}" -from:{handle}',
                'confidence': 0.6,
                'reasoning': 'People who engage with you and work at target company'
            },
            {
                'type': 'industry_conversations',
                'description': f'Industry conversations @{handle} participates in',
                'search_query': f'from:{handle} OR to:{handle} "CEO" OR "founder" OR "startup"',
                'confidence': 0.5,
                'reasoning': 'Industry connections through conversations'
            }
        ]
        
        return search_strategies

class SocialProfileManager:
    """
    Manages both LinkedIn and Twitter profile connections for enhanced scouting
    """
    
    def __init__(self):
        self.linkedin_connector = LinkedInProfileConnector()
        self.twitter_connector = TwitterProfileConnector()
    
    def connect_social_profiles(self, user_id: str, profiles: Dict) -> Dict:
        """
        Connect user's social profiles and generate enhanced search strategies
        
        Args:
            user_id: Pre-Funnel user ID
            profiles: Dict with 'linkedin_url' and 'twitter_handle'
        """
        results = {
            'user_id': user_id,
            'connected_profiles': {},
            'search_strategies': {},
            'errors': []
        }
        
        # Connect LinkedIn profile
        if profiles.get('linkedin_url'):
            linkedin_info = self.linkedin_connector.extract_profile_info(profiles['linkedin_url'])
            if 'error' not in linkedin_info:
                results['connected_profiles']['linkedin'] = linkedin_info
                logging.info(f"LinkedIn profile connected for user {user_id}")
            else:
                results['errors'].append(f"LinkedIn: {linkedin_info['error']}")
        
        # Connect Twitter profile  
        if profiles.get('twitter_handle'):
            twitter_handle = profiles['twitter_handle']
            if self.twitter_connector.validate_twitter_handle(twitter_handle):
                results['connected_profiles']['twitter'] = {
                    'handle': twitter_handle.lstrip('@'),
                    'status': 'connected',
                    'data_source': 'user_provided'
                }
                logging.info(f"Twitter profile connected for user {user_id}")
            else:
                results['errors'].append("Twitter: Invalid handle format")
        
        return results
    
    def generate_enhanced_searches(self, user_id: str, target_company: str) -> Dict:
        """
        Generate enhanced search strategies based on user's connected profiles
        """
        # Get user's connected profiles (from database)
        from user_auth import auth_manager
        
        # This would get the stored profile info
        user_profiles = self.get_user_profiles(user_id)
        
        enhanced_searches = {
            'linkedin_strategies': [],
            'twitter_strategies': [],
            'combined_strategies': []
        }
        
        # LinkedIn-based searches
        if user_profiles.get('linkedin'):
            linkedin_searches = self.linkedin_connector.suggest_connection_searches(
                user_profiles['linkedin'], target_company
            )
            enhanced_searches['linkedin_strategies'] = linkedin_searches
        
        # Twitter-based searches
        if user_profiles.get('twitter'):
            twitter_searches = self.twitter_connector.extract_social_graph_searches(
                user_profiles['twitter']['handle'], target_company
            )
            enhanced_searches['twitter_strategies'] = twitter_searches
        
        # Combined strategies
        if user_profiles.get('linkedin') and user_profiles.get('twitter'):
            combined_searches = self.generate_cross_platform_searches(
                user_profiles, target_company
            )
            enhanced_searches['combined_strategies'] = combined_searches
        
        return enhanced_searches
    
    def generate_cross_platform_searches(self, profiles: Dict, target_company: str) -> List[Dict]:
        """Generate search strategies that combine LinkedIn and Twitter data"""
        linkedin_id = profiles['linkedin']['profile_id']
        twitter_handle = profiles['twitter']['handle']
        
        cross_platform_searches = [
            {
                'type': 'cross_platform_verification',
                'description': 'Find people with both LinkedIn and Twitter profiles',
                'search_query': f'site:linkedin.com/in/ "{target_company}" twitter.com',
                'confidence': 0.9,
                'reasoning': 'People with both platforms are more likely to be active and reachable'
            },
            {
                'type': 'social_proof_leads',
                'description': 'Find leads who follow similar people on both platforms',
                'search_query': f'"{target_company}" linkedin twitter "following @{twitter_handle}"',
                'confidence': 0.7,
                'reasoning': 'Social proof through mutual connections increases response rates'
            }
        ]
        
        return cross_platform_searches
    
    def get_user_profiles(self, user_id: str) -> Dict:
        """Get user's stored social profiles"""
        # This would query the database for stored profile info
        # For now, return empty dict
        return {}

# Global instance
social_profile_manager = SocialProfileManager() 