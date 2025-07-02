import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import requests
from config import DATABASE_URL

class UserAuthManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for user tokens"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Social tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                platform TEXT,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                token_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # API usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                platform TEXT,
                endpoint TEXT,
                usage_count INTEGER DEFAULT 1,
                date DATE DEFAULT (date('now')),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        

        
        conn.commit()
        conn.close()
    
    def create_user(self, email: str) -> str:
        """Create a new user and return user_id"""
        user_id = str(uuid.uuid4())
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (user_id, email) VALUES (?, ?)', (user_id, email))
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            # User already exists
            cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()
    
    def store_social_token(self, user_id: str, platform: str, token_data: Dict[str, Any]):
        """Store social media token for user"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        # Calculate expiry
        expires_at = None
        if 'expires_in' in token_data:
            expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
        
        cursor.execute('''
            INSERT OR REPLACE INTO social_tokens 
            (user_id, platform, access_token, refresh_token, expires_at, token_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            platform,
            token_data.get('access_token'),
            token_data.get('refresh_token'),
            expires_at,
            json.dumps(token_data)
        ))
        
        conn.commit()
        conn.close()
    
    def get_user_token(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Get valid social token for user"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT access_token, refresh_token, expires_at, token_data
            FROM social_tokens
            WHERE user_id = ? AND platform = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id, platform))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        access_token, refresh_token, expires_at, token_data = result
        
        # Check if token is expired
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            # Try to refresh token
            refreshed = self.refresh_token(user_id, platform, refresh_token)
            if refreshed:
                return refreshed
            return None
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at,
            'token_data': json.loads(token_data) if token_data else {}
        }
    
    def refresh_token(self, user_id: str, platform: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh expired social token"""
        if platform == 'twitter':
            return self._refresh_twitter_token(user_id, refresh_token)
        elif platform == 'linkedin':
            return self._refresh_linkedin_token(user_id, refresh_token)
        return None
    
    def _refresh_twitter_token(self, user_id: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Twitter OAuth 2.0 token (simplified - no OAuth credentials needed)"""
        # Note: With simple profile connection, we don't use OAuth tokens
        # This method is kept for backward compatibility but will return None
        print("Token refresh not needed with simple profile connection approach")
        return None
    
    def _refresh_linkedin_token(self, user_id: str, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh LinkedIn OAuth 2.0 token (simplified - no OAuth credentials needed)"""
        # Note: With simple profile connection, we don't use OAuth tokens
        # This method is kept for backward compatibility but will return None
        print("Token refresh not needed with simple profile connection approach")
        return None
    
    def track_api_usage(self, user_id: str, platform: str, endpoint: str):
        """Track API usage for rate limiting"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO api_usage (user_id, platform, endpoint, usage_count, date)
            VALUES (?, ?, ?, 1, date('now'))
        ''', (user_id, platform, endpoint))
        
        cursor.execute('''
            UPDATE api_usage 
            SET usage_count = usage_count + 1
            WHERE user_id = ? AND platform = ? AND endpoint = ? AND date = date('now')
        ''', (user_id, platform, endpoint))
        
        conn.commit()
        conn.close()
    
    def get_user_usage(self, user_id: str, platform: str, days: int = 1) -> Dict[str, int]:
        """Get user's API usage for rate limiting"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT endpoint, SUM(usage_count) as total
            FROM api_usage
            WHERE user_id = ? AND platform = ? 
            AND date >= date('now', '-{} days')
            GROUP BY endpoint
        '''.format(days), (user_id, platform))
        
        results = cursor.fetchall()
        conn.close()
        
        return {endpoint: total for endpoint, total in results}
    
    def get_user_connections(self, user_id: str) -> Dict[str, Any]:
        """Get user's social connections"""
        conn = sqlite3.connect('prefunnel.db')
        cursor = conn.cursor()
        
        # Get social tokens
        cursor.execute('''
            SELECT platform, access_token, expires_at, created_at
            FROM social_tokens
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        social_tokens = cursor.fetchall()
        conn.close()
        
        connections = {
            'social_platforms': []
        }
        
        # Process social tokens
        for platform, access_token, expires_at, created_at in social_tokens:
            is_valid = True
            if expires_at:
                try:
                    expiry_date = datetime.fromisoformat(expires_at)
                    is_valid = expiry_date > datetime.now()
                except:
                    is_valid = False
            
            connections['social_platforms'].append({
                'platform': platform,
                'connected': bool(access_token),
                'valid': is_valid,
                'connected_at': created_at
            })
        
        return connections

# Global instance
auth_manager = UserAuthManager() 