# Pre-Funnel Testing & Implementation Plan

## 🎯 Current Status
- ✅ **Flask API structure** with error handling
- ✅ **Gemini API integration** for reasoning and message generation  
- ✅ **Mock agents** for all scout functions
- ✅ **Comprehensive test suite** ready to run
- ✅ **API testing script** for end-to-end validation

## 🧪 Testing Plan (Start Here)

### Phase 1: Core Functionality Testing (START HERE)

#### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 2: Test Individual Agents
```bash
python test_agents.py
```
**Expected Results:**
- ✅ Reasoning Agent should generate smart search queries using Gemini
- ✅ Message Generation should create personalized outreach messages
- ✅ Mock agents should return sample data
- ✅ Validation should deduplicate and rank profiles
- ✅ Full pipeline should work end-to-end

#### Step 3: Test API Endpoints
```bash
# Terminal 1: Start the Flask app
python app.py

# Terminal 2: Run API tests
python test_api.py
```
**Expected Results:**
- ✅ Health check should pass
- ✅ Valid requests should return enriched profiles with AI messages
- ✅ Invalid requests should return proper error messages
- ✅ Response time should be reasonable (under 30 seconds)

### Phase 2: Real API Integration (Next Steps)

#### Priority Order for External APIs:

1. **Google Custom Search Engine** (Free - 100 searches/day)
   - Set up: https://console.cloud.google.com/
   - Update `agents/internet_scout.py`
   - Test with real web searches

2. **Twitter API v2** (Free - 1,500 tweets/month)
   - Apply: https://developer.twitter.com/
   - Update `agents/x_scout.py` 
   - Test with real Twitter searches

3. **People Data Labs** (Paid but comprehensive)
   - Sign up: https://www.peopledatalabs.com/
   - Update `agents/email_scout.py`
   - Test with real email enrichment

4. **LinkedIn Integration** (Most complex)
   - PhantomBuster or SaleLeads
   - Update `agents/linkedin_scout.py`
   - Test with real LinkedIn searches

## 🔧 Implementation Roadmap

### Week 1: Foundation Testing
- [x] Set up Gemini API integration
- [x] Add comprehensive error handling
- [x] Create test suites
- [ ] **YOUR TASK:** Run `python test_agents.py` and verify Gemini integration
- [ ] **YOUR TASK:** Run `python test_api.py` and verify API functionality

### Week 2: Free APIs Integration
- [ ] Set up Google Custom Search Engine
- [ ] Implement real internet scouting
- [ ] Apply for Twitter Developer Account
- [ ] Implement real Twitter scouting

### Week 3: Paid APIs Integration  
- [ ] Sign up for People Data Labs
- [ ] Implement real email enrichment
- [ ] Research LinkedIn API options
- [ ] Implement LinkedIn scouting

### Week 4: Production Readiness
- [ ] Add rate limiting and caching
- [ ] Implement logging and monitoring
- [ ] Add authentication (if needed)
- [ ] Deploy to cloud (optional)

## 🚀 Quick Start Instructions

1. **Test the Gemini Integration:**
   ```bash
   python test_agents.py
   ```
   This will verify your Gemini API key works and the AI agents generate good results.

2. **Test the API:**
   ```bash
   # Terminal 1
   python app.py
   
   # Terminal 2  
   python test_api.py
   ```
   This will test the full API with realistic requests.

3. **Try a Manual API Call:**
   ```bash
   curl -X POST http://localhost:5000/api/lead-discovery \
     -H "Content-Type: application/json" \
     -d '{
       "emails": ["founder@startup.com"],
       "company_info": "VoiceFlow AI",
       "goal": "Find Bay Area SaaS founders looking for AI-powered voice solutions",
       "target": 3
     }'
   ```

## 🎯 Success Criteria

### Phase 1 (Current): ✅ Ready to Test
- Gemini API generates intelligent search strategies
- Message generation creates personalized outreach
- API returns proper JSON responses
- Error handling works correctly

### Phase 2: Real Data Integration
- Internet scout returns real web search results
- Twitter scout finds actual relevant profiles
- Email scout enriches real email addresses
- LinkedIn scout discovers real professional profiles

### Phase 3: Production Ready
- Handles 100+ requests per day reliably
- Response time under 30 seconds
- Proper error handling for API failures
- Rate limiting and cost management

## 🔍 What to Look For

### When Testing Reasoning Agent:
- Are the generated LinkedIn queries specific and relevant?
- Do the X/Twitter queries use appropriate hashtags and keywords?
- Are the internet queries likely to find relevant companies/people?

### When Testing Message Generation:
- Are messages personalized with the person's name and company?
- Do messages mention the specific goal clearly?
- Are messages professional but not too salesy?
- Are they under 50 words as requested?

### When Testing API:
- Does it handle missing required fields properly?
- Are error messages helpful and specific?
- Does it return the expected JSON structure?
- Are response times reasonable?

## 🆘 Troubleshooting

### Common Issues:
1. **Gemini API Key Error:** Make sure your API key is correct in `config.py`
2. **Import Errors:** Run `pip install -r requirements.txt`
3. **Connection Refused:** Make sure Flask app is running on port 5000
4. **Slow Responses:** Gemini API can take 5-15 seconds, this is normal

### Next Steps After Testing:
1. If tests pass → Start integrating real APIs
2. If tests fail → Check error messages and fix issues
3. If Gemini works well → You're ready for production use with mock data
4. If you want real data → Follow the API integration roadmap above 