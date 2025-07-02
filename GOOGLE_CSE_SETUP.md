# Google Custom Search Engine Setup

## Quick Setup (5 minutes)

You have the API key: `AIzaSyAT4tQKRNt1rwrqrTs2GzlXuWi-BAYJWPA`

Now you need to create a Custom Search Engine ID:

### Step 1: Create Custom Search Engine

1. Go to: https://cse.google.com/cse/create
2. **Sites to search**: Enter `*` (to search the entire web)
3. **Name**: "Pre-Funnel Lead Discovery"
4. Click **Create**

### Step 2: Get Search Engine ID

1. After creation, click **Control Panel**
2. Copy the **Search engine ID** (looks like: `017576662512468239146:omuauf_lfve`)
3. Add it to your config:

```bash
export GOOGLE_CSE_ID="your-search-engine-id-here"
```

Or add it directly to `config.py`:

```python
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', 'your-search-engine-id-here')
```

### Step 3: Test

```bash
python -c "from agents.internet_scout_real import internet_scout; print(internet_scout('AI startup founders'))"
```

## Free Tier Limits

- **100 searches per day** (free)
- **10,000 searches per day** ($5/1000 additional queries)

## Alternative: Skip Google CSE

If you prefer to skip this for now, the system will work fine with mock data for internet scouting. The other agents (Email, Twitter, LinkedIn) are more important for lead discovery.

Just comment out the Google CSE parts and it will use fallback data. 