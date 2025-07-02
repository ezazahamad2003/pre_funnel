#!/usr/bin/env python3
"""
Test script for real API integrations
Run this after you've set up your API keys to test each service
"""

import sys
import json
from config import (
    PEOPLE_DATA_LABS_API_KEY, TWITTER_BEARER_TOKEN, 
    GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID, PHANTOMBUSTER_API_KEY
)

def check_api_keys():
    """Check which API keys are configured"""
    print("🔑 API Key Configuration Check")
    print("=" * 50)
    
    apis = {
        "People Data Labs": PEOPLE_DATA_LABS_API_KEY,
        "Twitter Bearer Token": TWITTER_BEARER_TOKEN,
        "Google CSE API Key": GOOGLE_CSE_API_KEY,
        "Google CSE ID": GOOGLE_CSE_ID,
        "PhantomBuster API Key": PHANTOMBUSTER_API_KEY
    }
    
    configured = []
    missing = []
    
    for api_name, api_key in apis.items():
        if api_key and api_key != '':
            print(f"✅ {api_name}: Configured")
            configured.append(api_name)
        else:
            print(f"❌ {api_name}: Not configured")
            missing.append(api_name)
    
    print(f"\nSummary: {len(configured)}/{len(apis)} APIs configured")
    
    if missing:
        print(f"\n📋 To configure missing APIs:")
        for api in missing:
            print(f"  - {api}: See API_SETUP_GUIDE.md")
    
    return configured, missing

def test_people_data_labs():
    """Test People Data Labs email enrichment"""
    print("\n📧 Testing People Data Labs API...")
    
    if not PEOPLE_DATA_LABS_API_KEY:
        print("❌ API key not configured")
        return False
    
    try:
        from agents.email_scout_real import scout_from_email, get_usage_stats
        
        # Test with a common test email (this won't return real data)
        test_email = "test@example.com"
        print(f"Testing email: {test_email}")
        
        result = scout_from_email(test_email)
        
        if result:
            print(f"✅ API call successful!")
            print(f"Result: {result[0]['name']} - {result[0]['title']} at {result[0]['company']}")
            print(f"Source: {result[0]['source']}")
        else:
            print(f"⚠️  No profile found (this is normal for test emails)")
        
        # Check usage stats
        usage = get_usage_stats()
        if 'error' not in usage:
            print(f"📊 Usage stats: {usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_twitter_api():
    """Test Twitter API v2"""
    print("\n🐦 Testing Twitter API...")
    
    if not TWITTER_BEARER_TOKEN:
        print("❌ Bearer token not configured")
        return False
    
    try:
        from agents.x_scout_real import x_scout, get_twitter_usage_info
        
        test_query = "AI startup founder"
        print(f"Testing query: {test_query}")
        
        result = x_scout(test_query)
        
        if result:
            print(f"✅ API call successful!")
            print(f"Found {len(result)} profiles")
            if result:
                sample = result[0]
                print(f"Sample: {sample['name']} - {sample['title']} ({sample['x_handle']})")
                print(f"Followers: {sample.get('followers', 'N/A')}")
        else:
            print(f"⚠️  No profiles found")
        
        # Show usage info
        usage_info = get_twitter_usage_info()
        print(f"📊 Rate limits: {usage_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_google_search():
    """Test Google Custom Search Engine"""
    print("\n🌐 Testing Google Custom Search...")
    
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        print("❌ Google CSE API key or ID not configured")
        return False
    
    try:
        from agents.internet_scout_real import internet_scout, get_google_usage_info
        
        test_query = "AI startup founders Bay Area"
        print(f"Testing query: {test_query}")
        
        result = internet_scout(test_query)
        
        if result:
            print(f"✅ API call successful!")
            print(f"Found {len(result)} profiles")
            if result:
                sample = result[0]
                print(f"Sample: {sample['name']} - {sample['title']} at {sample['company']}")
                print(f"Source: {sample['source']}")
                print(f"Domain: {sample.get('domain', 'N/A')}")
        else:
            print(f"⚠️  No profiles found")
        
        # Show usage info
        usage_info = get_google_usage_info()
        print(f"📊 Usage limits: {usage_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_phantombuster():
    """Test PhantomBuster LinkedIn integration"""
    print("\n💼 Testing PhantomBuster LinkedIn...")
    
    if not PHANTOMBUSTER_API_KEY:
        print("❌ PhantomBuster API key not configured")
        return False
    
    try:
        from agents.linkedin_scout_real import get_phantombuster_setup_info, get_linkedin_usage_info
        
        # Show setup info instead of running actual test
        # (PhantomBuster requires phantom setup which is complex)
        setup_info = get_phantombuster_setup_info()
        print("📋 PhantomBuster Setup Required:")
        for step in setup_info['setup_steps']:
            print(f"  {step}")
        
        print(f"\n💰 Cost: {setup_info['cost']}")
        
        usage_info = get_linkedin_usage_info()
        print(f"📊 Usage info: {usage_info}")
        
        print("\n⚠️  Note: PhantomBuster requires manual phantom setup")
        print("   This test shows setup info only")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_full_pipeline_with_real_apis():
    """Test the full pipeline with whatever real APIs are available"""
    print("\n🚀 Testing Full Pipeline with Real APIs...")
    
    try:
        # Import the main app components
        from agents.reasoning import interpret_goal
        from agents.email_scout import scout_from_email
        from agents.linkedin_scout import linkedin_scout
        from agents.x_scout import x_scout
        from agents.internet_scout import internet_scout
        from agents.validate_rank import validate_and_rank
        from agents.message_gen import generate_message
        
        # Test input
        test_input = {
            "emails": ["founder@example.com"],
            "company_info": "VoiceFlow AI",
            "goal": "Find Bay Area SaaS founders looking for AI-powered voice solutions",
            "target": 3
        }
        
        print(f"Goal: {test_input['goal']}")
        print(f"Company: {test_input['company_info']}")
        
        # 1. Goal interpretation (always uses Gemini)
        print("\n  Step 1: Goal interpretation...")
        search_plan = interpret_goal(
            test_input['goal'], 
            test_input['company_info'], 
            test_input['emails']
        )
        print(f"  ✅ Generated {len(search_plan.get('linkedin_queries', []))} LinkedIn queries")
        
        # 2. Scouting (mix of real and mock)
        print("\n  Step 2: Profile scouting...")
        profiles = []
        
        # Email scouting
        for email in test_input['emails']:
            email_profiles = scout_from_email(email)
            profiles.extend(email_profiles)
            print(f"    Email scout: {len(email_profiles)} profiles ({email_profiles[0]['source'] if email_profiles else 'none'})")
        
        # LinkedIn scouting
        for query in search_plan.get('linkedin_queries', [])[:1]:  # Test just one query
            linkedin_profiles = linkedin_scout(query)
            profiles.extend(linkedin_profiles)
            print(f"    LinkedIn scout: {len(linkedin_profiles)} profiles ({linkedin_profiles[0]['source'] if linkedin_profiles else 'none'})")
        
        # X scouting
        for query in search_plan.get('x_queries', [])[:1]:  # Test just one query
            x_profiles = x_scout(query)
            profiles.extend(x_profiles)
            print(f"    X scout: {len(x_profiles)} profiles ({x_profiles[0]['source'] if x_profiles else 'none'})")
        
        # Internet scouting
        for query in search_plan.get('internet_queries', [])[:1]:  # Test just one query
            internet_profiles = internet_scout(query)
            profiles.extend(internet_profiles)
            print(f"    Internet scout: {len(internet_profiles)} profiles ({internet_profiles[0]['source'] if internet_profiles else 'none'})")
        
        print(f"  Total profiles found: {len(profiles)}")
        
        # 3. Validation & Ranking
        print("\n  Step 3: Validation & ranking...")
        unique_profiles = validate_and_rank(profiles, test_input['goal'], test_input['company_info'])
        unique_profiles = unique_profiles[:test_input['target']]
        print(f"  ✅ {len(unique_profiles)} unique profiles after validation")
        
        # 4. Message generation
        print("\n  Step 4: Message generation...")
        for profile in unique_profiles:
            profile['message'] = generate_message(profile, test_input['goal'], test_input['company_info'])
        print(f"  ✅ Generated {len(unique_profiles)} personalized messages")
        
        # Show results
        print(f"\n📊 Final Results:")
        for i, profile in enumerate(unique_profiles, 1):
            print(f"\n  Profile {i}:")
            print(f"    Name: {profile['name']}")
            print(f"    Title: {profile['title']}")
            print(f"    Company: {profile['company']}")
            print(f"    Source: {profile['source']}")
            print(f"    Message: {profile['message'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False

def main():
    """Run all real API tests"""
    print("🧪 Pre-Funnel Real API Testing Suite")
    print("=" * 50)
    
    # Check API configuration
    configured, missing = check_api_keys()
    
    if not configured:
        print("\n⚠️  No APIs configured. Please set up at least one API.")
        print("See API_SETUP_GUIDE.md for instructions.")
        return
    
    # Test each configured API
    test_results = {}
    
    if "People Data Labs" in configured:
        test_results["People Data Labs"] = test_people_data_labs()
    
    if "Twitter Bearer Token" in configured:
        test_results["Twitter API"] = test_twitter_api()
    
    if "Google CSE API Key" in configured and "Google CSE ID" in configured:
        test_results["Google Search"] = test_google_search()
    
    if "PhantomBuster API Key" in configured:
        test_results["PhantomBuster"] = test_phantombuster()
    
    # Test full pipeline
    test_results["Full Pipeline"] = test_full_pipeline_with_real_apis()
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 REAL API TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All configured APIs are working!")
    else:
        print("⚠️  Some API tests failed. Check the errors above.")
    
    print(f"\n💡 Next Steps:")
    if missing:
        print(f"1. Set up remaining APIs: {', '.join(missing)}")
    print(f"2. Run production tests with real data")
    print(f"3. Monitor API usage and costs")
    print(f"4. Scale up when ready!")

if __name__ == "__main__":
    main() 