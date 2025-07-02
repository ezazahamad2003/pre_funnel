import os
from flask import Flask, request, jsonify, redirect, session, url_for
from dotenv import load_dotenv
import requests
from urllib.parse import urlencode
from agents.reasoning import interpret_goal
from agents.email_scout import scout_from_email
from agents.linkedin_scout import linkedin_scout
from agents.x_scout import x_scout
from agents.internet_scout import internet_scout
from agents.validate_rank import validate_and_rank
from agents.message_gen import generate_message
from user_auth import auth_manager
from linkedin_profile_connector import social_profile_manager

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.route('/api/lead-discovery', methods=['POST'])
def lead_discovery():
    try:
        # Input validation
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.get_json()
        
        # Required fields validation
        if not data.get('emails') or not isinstance(data.get('emails'), list):
            return jsonify({'error': 'emails field is required and must be a list'}), 400
        
        if not data.get('company_info'):
            return jsonify({'error': 'company_info field is required'}), 400
            
        if not data.get('goal'):
            return jsonify({'error': 'goal field is required'}), 400
        
        # Extract user info for multi-tenant support
        user_id = data.get('user_id')  # Optional: if provided, use user's social tokens
        user_email = data.get('user_email')  # For creating user if needed
        
        # Create user if email provided but no user_id
        if user_email and not user_id:
            user_id = auth_manager.create_user(user_email)
        
        emails = data.get('emails', [])
        linkedin_queries = data.get('linkedin_queries', [])
        x_queries = data.get('x_queries', [])
        company_info = data.get('company_info', '')
        goal = data.get('goal', '')
        n = data.get('target', 20)
        
        # Validate target number
        if not isinstance(n, int) or n <= 0:
            return jsonify({'error': 'target must be a positive integer'}), 400
        
        # 1. Reasoning Agent
        try:
            search_plan = interpret_goal(goal, company_info, emails)
        except Exception as e:
            app.logger.error(f"Error in goal interpretation: {str(e)}")
            return jsonify({'error': 'Failed to interpret goal', 'details': str(e)}), 500
        
        # 2. Scouts (with user context for social auth)
        profiles = []
        errors = []
        
        # Email scouting (always uses shared API)
        for email in emails:
            try:
                profiles.extend(scout_from_email(email, user_id=user_id))
            except Exception as e:
                app.logger.error(f"Error scouting email {email}: {str(e)}")
                errors.append(f"Email scout failed for {email}: {str(e)}")
        
        # LinkedIn scouting (hybrid: user auth preferred)
        for query in search_plan.get('linkedin_queries', []):
            try:
                profiles.extend(linkedin_scout(query, user_id=user_id))
            except Exception as e:
                app.logger.error(f"Error in LinkedIn scout for query '{query}': {str(e)}")
                errors.append(f"LinkedIn scout failed for query '{query}': {str(e)}")
        
        # X/Twitter scouting (hybrid: user auth preferred)
        for query in search_plan.get('x_queries', []):
            try:
                profiles.extend(x_scout(query, user_id=user_id))
            except Exception as e:
                app.logger.error(f"Error in X scout for query '{query}': {str(e)}")
                errors.append(f"X scout failed for query '{query}': {str(e)}")
        
        # Internet scouting (always uses shared API)
        for query in search_plan.get('internet_queries', []):
            try:
                profiles.extend(internet_scout(query, user_id=user_id))
            except Exception as e:
                app.logger.error(f"Error in internet scout for query '{query}': {str(e)}")
                errors.append(f"Internet scout failed for query '{query}': {str(e)}")
        
        if not profiles:
            return jsonify({
                'profiles': [],
                'message': 'No profiles found',
                'errors': errors,
                'user_id': user_id
            }), 200
        
        # 3. Validate & Rank
        try:
            unique_profiles = validate_and_rank(profiles, goal, company_info)
            unique_profiles = unique_profiles[:n]  # Limit to target
        except Exception as e:
            app.logger.error(f"Error in validation and ranking: {str(e)}")
            return jsonify({'error': 'Failed to validate and rank profiles', 'details': str(e)}), 500
        
        # 4. Message Generation
        for profile in unique_profiles:
            try:
                profile['message'] = generate_message(profile, goal, company_info)
            except Exception as e:
                app.logger.error(f"Error generating message for {profile.get('name', 'unknown')}: {str(e)}")
                profile['message'] = f"Hi {profile.get('name', '')}, let's connect regarding {goal}. - {company_info}"
                errors.append(f"Message generation failed for {profile.get('name', 'unknown')}: {str(e)}")
        
        response = {
            'profiles': unique_profiles,
            'total_found': len(profiles),
            'returned': len(unique_profiles),
            'user_id': user_id
        }
        
        if errors:
            response['warnings'] = errors
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"Unexpected error in lead discovery: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Social Authentication Routes

@app.route('/auth/twitter')
def twitter_auth():
    """Initiate Twitter OAuth flow"""
    if not SOCIAL_AUTH['twitter']['client_id']:
        return jsonify({'error': 'Twitter OAuth not configured'}), 400
    
    # Generate OAuth URL
    params = {
        'response_type': 'code',
        'client_id': SOCIAL_AUTH['twitter']['client_id'],
        'redirect_uri': SOCIAL_AUTH['twitter']['redirect_uri'],
        'scope': 'tweet.read users.read follows.read',
        'state': request.args.get('user_id', 'anonymous'),
        'code_challenge': 'challenge',  # In production, use proper PKCE
        'code_challenge_method': 'plain'
    }
    
    auth_url = 'https://twitter.com/i/oauth2/authorize?' + urlencode(params)
    return redirect(auth_url)

@app.route('/auth/twitter/callback')
def twitter_callback():
    """Handle Twitter OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')  # user_id
    
    if not code:
        return jsonify({'error': 'Authorization failed'}), 400
    
    # Exchange code for token
    try:
        response = requests.post('https://api.twitter.com/2/oauth2/token', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SOCIAL_AUTH['twitter']['redirect_uri'],
            'code_verifier': 'challenge',
            'client_id': SOCIAL_AUTH['twitter']['client_id']
        }, auth=(
            SOCIAL_AUTH['twitter']['client_id'],
            SOCIAL_AUTH['twitter']['client_secret']
        ))
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Store token for user
            if state and state != 'anonymous':
                auth_manager.store_social_token(state, 'twitter', token_data)
            
            return jsonify({
                'message': 'Twitter connected successfully',
                'user_id': state,
                'platform': 'twitter'
            })
        else:
            return jsonify({'error': 'Failed to get access token'}), 400
            
    except Exception as e:
        return jsonify({'error': f'OAuth error: {str(e)}'}), 500

@app.route('/auth/linkedin')
def linkedin_auth():
    """Initiate LinkedIn OAuth flow"""
    if not SOCIAL_AUTH['linkedin']['client_id']:
        return jsonify({'error': 'LinkedIn OAuth not configured'}), 400
    
    params = {
        'response_type': 'code',
        'client_id': SOCIAL_AUTH['linkedin']['client_id'],
        'redirect_uri': SOCIAL_AUTH['linkedin']['redirect_uri'],
        'scope': 'r_liteprofile r_emailaddress',
        'state': request.args.get('user_id', 'anonymous')
    }
    
    auth_url = 'https://www.linkedin.com/oauth/v2/authorization?' + urlencode(params)
    return redirect(auth_url)

@app.route('/auth/linkedin/callback')
def linkedin_callback():
    """Handle LinkedIn OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')  # user_id
    
    if not code:
        return jsonify({'error': 'Authorization failed'}), 400
    
    try:
        response = requests.post('https://www.linkedin.com/oauth/v2/accessToken', data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SOCIAL_AUTH['linkedin']['redirect_uri'],
            'client_id': SOCIAL_AUTH['linkedin']['client_id'],
            'client_secret': SOCIAL_AUTH['linkedin']['client_secret']
        })
        
        if response.status_code == 200:
            token_data = response.json()
            
            # Store token for user
            if state and state != 'anonymous':
                auth_manager.store_social_token(state, 'linkedin', token_data)
            
            return jsonify({
                'message': 'LinkedIn connected successfully',
                'user_id': state,
                'platform': 'linkedin'
            })
        else:
            return jsonify({'error': 'Failed to get access token'}), 400
            
    except Exception as e:
        return jsonify({'error': f'OAuth error: {str(e)}'}), 500

@app.route('/api/user/create', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user_id = auth_manager.create_user(email)
    return jsonify({'user_id': user_id, 'email': email})

@app.route('/api/user/<user_id>/connections')
def get_user_connections(user_id):
    """Get user's connected social accounts"""
    twitter_token = auth_manager.get_user_token(user_id, 'twitter')
    linkedin_token = auth_manager.get_user_token(user_id, 'linkedin')
    
    connections = {
        'twitter': bool(twitter_token),
        'linkedin': bool(linkedin_token)
    }
    
    return jsonify({'user_id': user_id, 'connections': connections})

@app.route('/api/usage/<user_id>')
def get_user_usage(user_id):
    """Get user's API usage statistics"""
    twitter_usage = auth_manager.get_user_usage(user_id, 'twitter', days=30)
    linkedin_usage = auth_manager.get_user_usage(user_id, 'linkedin', days=1)
    
    return jsonify({
        'user_id': user_id,
        'usage': {
            'twitter': twitter_usage,
            'linkedin': linkedin_usage
        }
    })



@app.route('/api/connect-social-profiles', methods=['POST'])
def connect_social_profiles():
    """Connect user's LinkedIn and Twitter profiles for enhanced scouting"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        profiles = data.get('profiles', {})
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Validate input profiles
        linkedin_url = profiles.get('linkedin_url', '').strip()
        twitter_handle = profiles.get('twitter_handle', '').strip()
        
        if not linkedin_url and not twitter_handle:
            return jsonify({'error': 'At least one social profile required'}), 400
        
        # Connect profiles
        result = social_profile_manager.connect_social_profiles(user_id, {
            'linkedin_url': linkedin_url,
            'twitter_handle': twitter_handle
        })
        
        # Store in database
        if result['connected_profiles'].get('linkedin'):
            auth_manager.store_social_token(user_id, 'linkedin', {
                'profile_url': linkedin_url,
                'profile_id': result['connected_profiles']['linkedin']['profile_id'],
                'connection_type': 'manual',
                'data_source': 'user_provided'
            })
        
        if result['connected_profiles'].get('twitter'):
            auth_manager.store_social_token(user_id, 'twitter', {
                'handle': twitter_handle.lstrip('@'),
                'connection_type': 'manual', 
                'data_source': 'user_provided'
            })
        
        return jsonify({
            'success': True,
            'connected_profiles': list(result['connected_profiles'].keys()),
            'errors': result['errors'],
            'message': f"Connected {len(result['connected_profiles'])} social profile(s)"
        })
        
    except Exception as e:
        app.logger.error(f"Social profile connection error: {str(e)}")
        return jsonify({'error': 'Failed to connect social profiles', 'details': str(e)}), 500

@app.route('/api/enhanced-search-strategies/<user_id>/<target_company>')
def get_enhanced_search_strategies(user_id: str, target_company: str):
    """Get enhanced search strategies based on user's social connections"""
    try:
        # Get user's social tokens
        linkedin_token = auth_manager.get_user_token(user_id, 'linkedin')
        twitter_token = auth_manager.get_user_token(user_id, 'twitter')
        
        strategies = {
            'linkedin_strategies': [],
            'twitter_strategies': [],
            'network_insights': {
                'has_linkedin': bool(linkedin_token),
                'has_twitter': bool(twitter_token),
                'enhanced_scouting_available': bool(linkedin_token or twitter_token)
            }
        }
        
        # Generate LinkedIn-based strategies
        if linkedin_token:
            linkedin_profile = {
                'profile_id': linkedin_token.get('token_data', {}).get('profile_id', ''),
                'profile_url': linkedin_token.get('token_data', {}).get('profile_url', '')
            }
            strategies['linkedin_strategies'] = social_profile_manager.linkedin_connector.suggest_connection_searches(
                linkedin_profile, target_company
            )
        
        # Generate Twitter-based strategies
        if twitter_token:
            twitter_handle = twitter_token.get('token_data', {}).get('handle', '')
            strategies['twitter_strategies'] = [
                {
                    'type': 'twitter_followers',
                    'description': f'Find @{twitter_handle} followers at {target_company}',
                    'search_query': f'site:twitter.com followers:{twitter_handle} "{target_company}"',
                    'confidence': 0.7,
                    'reasoning': 'Your Twitter followers who work at target company'
                },
                {
                    'type': 'twitter_mentions',
                    'description': f'People who mention @{twitter_handle} and work at {target_company}',
                    'search_query': f'@{twitter_handle} "{target_company}" -from:{twitter_handle}',
                    'confidence': 0.6,
                    'reasoning': 'People who engage with you on Twitter'
                }
            ]
        
        return jsonify(strategies)
        
    except Exception as e:
        app.logger.error(f"Enhanced search strategies error: {str(e)}")
        return jsonify({'error': 'Failed to generate search strategies', 'details': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Pre-Funnel API is running'}), 200

if __name__ == '__main__':
    app.run(debug=True) 