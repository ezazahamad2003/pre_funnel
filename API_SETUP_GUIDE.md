# 🔑 API Setup Guide for Pre-Funnel

## 📋 APIs You Need to Set Up

### 1. **People Data Labs API** (Email Enrichment)
**Cost:** $0.10-0.20 per enriched profile  
**Free Tier:** 1,000 free API calls to start  
**Setup:**
1. Go to: https://www.peopledatalabs.com/
2. Sign up for an account
3. Get your API key from dashboard
4. Add to `config.py`: `PEOPLE_DATA_LABS_API_KEY = "your_key_here"`

**What it does:** Converts email → full profile (name, title, company, LinkedIn, etc.)

### 2. **Twitter API v2** (Profile Discovery)
**Cost:** Free tier: 1,500 tweets/month, $100/month for more  
**Setup:**
1. Apply at: https://developer.twitter.com/
2. Create a new project/app
3. Get your Bearer Token
4. Add to `config.py`: `TWITTER_BEARER_TOKEN = "your_token_here"`

**What it does:** Searches Twitter for relevant profiles and tweets

### 3. **Google Custom Search Engine API** (Web Search)
**Cost:** Free: 100 searches/day, $5 per 1,000 additional searches  
**Setup:**
1. Go to: https://console.cloud.google.com/
2. Enable Custom Search API
3. Create a Custom Search Engine at: https://cse.google.com/
4. Get API key and Search Engine ID
5. Add to `config.py`:
   ```python
   GOOGLE_CSE_API_KEY = "your_api_key"
   GOOGLE_CSE_ID = "your_search_engine_id"
   ```

**What it does:** Searches the web for company info, profiles, news

### 4. **LinkedIn Integration** (Professional Profiles)
**Options:**
- **PhantomBuster** (Recommended): $56/month, easy setup
- **SaleLeads**: $49/month  
- **LinkedIn Sales Navigator API**: Enterprise only

**PhantomBuster Setup:**
1. Go to: https://phantombuster.com/
2. Sign up and get API key
3. Add to `config.py`: `PHANTOMBUSTER_API_KEY = "your_key_here"`

**What it does:** Searches LinkedIn for profiles matching your criteria

## 🔧 Implementation Priority

**Start with these (easiest/cheapest):**
1. ✅ Google Custom Search Engine (100 free/day)
2. ✅ Twitter API (1,500 free/month)
3. ✅ People Data Labs (1,000 free calls)
4. ✅ PhantomBuster (paid but comprehensive)

## 💰 Cost Estimate

**Free Tier Usage (per month):**
- Google Search: 3,000 searches (100/day) = FREE
- Twitter: 1,500 profile searches = FREE  
- People Data Labs: 1,000 enrichments = FREE
- **Total Free:** ~4,500 lead discoveries per month

**Paid Usage (moderate scale):**
- Google Search: $25/month (5,000 extra searches)
- Twitter: $100/month (unlimited)
- People Data Labs: $200/month (1,000 enrichments)
- PhantomBuster: $56/month (LinkedIn)
- **Total Paid:** ~$381/month for ~10,000 leads

## 🚀 Next Steps

1. **Get API keys** from the providers above
2. **Update `config.py`** with your keys
3. **Run the real API implementations** I'll create
4. **Test with small volumes** first
5. **Scale up** once everything works

## 🔒 Security Notes

- Never commit API keys to git
- Use environment variables in production
- Set up rate limiting to avoid overages
- Monitor usage in each provider's dashboard 