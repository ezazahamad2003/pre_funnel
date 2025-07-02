# Multi-Tenant Pre-Funnel Guide

## Overview

Pre-Funnel now supports a **hybrid multi-tenant architecture** that allows users to either:

1. **Use shared backend APIs** (free tier with rate limits)
2. **Connect their own social accounts** (unlimited personal rate limits)

This approach dramatically reduces costs while providing better scalability and user experience.

## Architecture

### API Strategy

| Agent | Strategy | Shared API | User Auth | Fallback |
|-------|----------|------------|-----------|----------|
| Email Scout | Shared | People Data Labs | ❌ | Mock |
| X/Twitter Scout | Hybrid | Twitter API | ✅ OAuth 2.0 | Shared → Mock |
| LinkedIn Scout | Hybrid | PhantomBuster | ✅ OAuth 2.0 | Shared → Mock |
| Internet Scout | Shared | Google CSE | ❌ | Mock |

### Rate Limits (Free Tier)

- **Twitter API Free**: 1,500 tweets/month
- **Google Custom Search**: 100 searches/day  
- **People Data Labs**: 1,000 enrichments/month
- **LinkedIn Scraping**: 50 searches/day (conservative)

## Usage Examples

### 1. Basic Usage (Shared APIs Only)

```json
POST /api/lead-discovery
{
  "emails": ["founder@startup.com"],
  "company_info": "VoiceFlow AI",
  "goal": "Find Bay Area SaaS founders",
  "target": 5
}
```

### 2. With User Account (No Social Auth)

```json
POST /api/lead-discovery
{
  "user_email": "user@company.com",
  "emails": ["founder@startup.com"],
  "company_info": "VoiceFlow AI", 
  "goal": "Find Bay Area SaaS founders",
  "target": 5
}
```

### 3. With Connected Social Accounts

```json
POST /api/lead-discovery
{
  "user_id": "uuid-from-user-creation",
  "emails": ["founder@startup.com"],
  "company_info": "VoiceFlow AI",
  "goal": "Find Bay Area SaaS founders", 
  "target": 10
}
```

## User Management API

### Create User

```bash
POST /api/user/create
{
  "email": "user@company.com"
}

Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@company.com"
}
```

### Check User Connections

```bash
GET /api/user/{user_id}/connections

Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "connections": {
    "twitter": true,
    "linkedin": false
  }
}
```

### Check Usage Statistics

```bash
GET /api/usage/{user_id}

Response:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "usage": {
    "twitter": {
      "search": 45
    },
    "linkedin": {
      "search": 12
    }
  }
}
```

## Social Authentication Flow

### Twitter OAuth

1. **Initiate OAuth**: `GET /auth/twitter?user_id={user_id}`
2. **User authorizes** on Twitter
3. **Callback**: `GET /auth/twitter/callback?code=...&state={user_id}`
4. **Token stored** for user

### LinkedIn OAuth

1. **Initiate OAuth**: `GET /auth/linkedin?user_id={user_id}`
2. **User authorizes** on LinkedIn  
3. **Callback**: `GET /auth/linkedin/callback?code=...&state={user_id}`
4. **Token stored** for user

## Setup Instructions

### 1. Free Tier Setup (No OAuth)

```bash
# Set only the Gemini API key
export GEMINI_API_KEY="your-gemini-key"

# Optional: Set free tier API keys
export GOOGLE_CSE_API_KEY="your-google-key"
export GOOGLE_CSE_ID="your-search-engine-id"
```

### 2. Twitter OAuth Setup

```bash
# Create Twitter App at https://developer.twitter.com/
export TWITTER_CLIENT_ID="your-twitter-client-id"
export TWITTER_CLIENT_SECRET="your-twitter-client-secret"
export TWITTER_REDIRECT_URI="http://localhost:5000/auth/twitter/callback"
```

### 3. LinkedIn OAuth Setup

```bash
# Create LinkedIn App at https://www.linkedin.com/developers/
export LINKEDIN_CLIENT_ID="your-linkedin-client-id"
export LINKEDIN_CLIENT_SECRET="your-linkedin-client-secret"
export LINKEDIN_REDIRECT_URI="http://localhost:5000/auth/linkedin/callback"
```

## Benefits of Multi-Tenant Architecture

### For Startups (Your Clients)

✅ **Higher Rate Limits**: Personal Twitter accounts get 300 requests/15min vs shared 1,500/month  
✅ **Better Data Access**: Can access private profiles they follow  
✅ **No Usage Conflicts**: Personal quotas don't compete with other users  
✅ **Direct Messaging**: Can send messages through their own accounts  

### For You (Platform Owner)

✅ **Reduced API Costs**: Users provide their own API access  
✅ **Better Scaling**: No shared rate limit bottlenecks  
✅ **Compliance**: Users authenticate with their own accounts  
✅ **Fallback Security**: Always has shared APIs as backup  

## Cost Comparison

### Old Approach (Paid APIs Only)
- **Monthly Cost**: ~$405/month
- **Limits**: Shared across all users
- **Scaling**: Expensive per user

### New Approach (Hybrid)
- **Monthly Cost**: ~$0-50/month (free tiers)
- **User Limits**: Personal quotas (much higher)
- **Scaling**: Users provide their own API access

## Production Deployment

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your-gemini-key
SECRET_KEY=your-flask-secret-key

# Free Tier APIs (Optional)
GOOGLE_CSE_API_KEY=your-google-key
GOOGLE_CSE_ID=your-search-engine-id
PEOPLE_DATA_LABS_API_KEY=your-pdl-key

# Social OAuth (Optional)
TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
```

### Database

The system uses SQLite by default (`prefunnel.db`). For production, consider PostgreSQL:

```bash
export DATABASE_URL="postgresql://user:pass@localhost/prefunnel"
```

## Implementation Priority

### Phase 1: Free Tier (Week 1)
- ✅ Gemini API integration
- ✅ Mock data fallbacks
- ✅ Basic user management
- 🔄 Google Custom Search setup
- 🔄 People Data Labs free tier

### Phase 2: Twitter OAuth (Week 2)
- ✅ Twitter OAuth flow
- ✅ User token storage
- ✅ Hybrid API switching
- 🔄 Rate limit tracking

### Phase 3: LinkedIn OAuth (Week 3)
- ✅ LinkedIn OAuth flow
- 🔄 LinkedIn API integration
- 🔄 Usage analytics

### Phase 4: Production (Week 4)
- 🔄 PostgreSQL migration
- 🔄 Error monitoring
- 🔄 Usage dashboards

## Testing

```bash
# Test with mock data
python test_agents.py

# Test API endpoints
python test_api.py

# Test real APIs (when configured)
python test_real_apis.py
```

This architecture provides the best of both worlds: **cost-effective scaling** through user social auth while maintaining **reliable fallbacks** through shared APIs. 