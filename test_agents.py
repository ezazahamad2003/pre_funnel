#!/usr/bin/env python3
"""
Test script for Pre-Funnel agents
Run individual agent tests to verify functionality before full integration
"""

import sys
import json
from agents.reasoning import interpret_goal
from agents.email_scout import scout_from_email
from agents.linkedin_scout import linkedin_scout
from agents.x_scout import x_scout
from agents.internet_scout import internet_scout
from agents.validate_rank import validate_and_rank
from agents.message_gen import generate_message

def test_reasoning_agent():
    """Test the Gemini-powered goal interpretation"""
    print("🧠 Testing Reasoning Agent (Gemini API)...")
    
    test_cases = [
        {
            "goal": "Find Bay Area SaaS founders looking for AI-powered networking solutions",
            "company_info": "VoiceFlow AI",
            "emails": ["sam@startup.com"]
        },
        {
            "goal": "Connect with healthcare technology CTOs in Boston",
            "company_info": "MedTech Solutions",
            "emails": ["john@healthtech.com"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test Case {i}:")
        print(f"    Goal: {test_case['goal']}")
        print(f"    Company: {test_case['company_info']}")
        
        try:
            result = interpret_goal(
                test_case['goal'], 
                test_case['company_info'], 
                test_case['emails']
            )
            print(f"    ✅ Success!")
            print(f"    LinkedIn queries: {result.get('linkedin_queries', [])}")
            print(f"    X queries: {result.get('x_queries', [])}")
            print(f"    Internet queries: {result.get('internet_queries', [])}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return True

def test_message_generation():
    """Test the Gemini-powered message generation"""
    print("\n💬 Testing Message Generation Agent (Gemini API)...")
    
    test_profiles = [
        {
            "name": "Sarah Johnson",
            "title": "CEO",
            "company": "TechStart Inc",
            "email": "sarah@techstart.com"
        },
        {
            "name": "Mike Chen",
            "title": "CTO",
            "company": "DataFlow",
            "email": "mike@dataflow.com"
        }
    ]
    
    goal = "Find Bay Area SaaS founders looking for AI-powered voice solutions"
    company_info = "VoiceFlow AI"
    
    for i, profile in enumerate(test_profiles, 1):
        print(f"\n  Test Case {i}:")
        print(f"    Profile: {profile['name']} - {profile['title']} at {profile['company']}")
        
        try:
            message = generate_message(profile, goal, company_info)
            print(f"    ✅ Success!")
            print(f"    Message: {message}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    return True

def test_mock_agents():
    """Test the mock agents (email, linkedin, x, internet scouts)"""
    print("\n🔍 Testing Mock Scout Agents...")
    
    # Test email scout
    print("\n  📧 Email Scout:")
    try:
        result = scout_from_email("test@example.com")
        print(f"    ✅ Success! Found {len(result)} profiles")
        if result:
            print(f"    Sample: {result[0]['name']} - {result[0]['title']}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test LinkedIn scout
    print("\n  💼 LinkedIn Scout:")
    try:
        result = linkedin_scout("AI startup founders")
        print(f"    ✅ Success! Found {len(result)} profiles")
        if result:
            print(f"    Sample: {result[0]['name']} - {result[0]['title']}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test X scout
    print("\n  🐦 X/Twitter Scout:")
    try:
        result = x_scout("tech founders")
        print(f"    ✅ Success! Found {len(result)} profiles")
        if result:
            print(f"    Sample: {result[0]['name']} - {result[0]['title']}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test Internet scout
    print("\n  🌐 Internet Scout:")
    try:
        result = internet_scout("VoiceFlow AI startup")
        print(f"    ✅ Success! Found {len(result)} profiles")
        if result:
            print(f"    Sample: {result[0]['name']} - {result[0]['title']}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    return True

def test_validation_ranking():
    """Test the validation and ranking agent"""
    print("\n🏆 Testing Validation & Ranking Agent...")
    
    # Create test profiles with duplicates
    test_profiles = [
        {
            "name": "John Doe",
            "title": "CEO",
            "company": "TechCorp",
            "source": "email_scout"
        },
        {
            "name": "Jane Smith", 
            "title": "CTO",
            "company": "DataFlow",
            "source": "linkedin_scout"
        },
        {
            "name": "John Doe",  # Duplicate
            "title": "CEO",
            "company": "TechCorp", 
            "source": "x_scout"
        },
        {
            "name": "Alice Brown",
            "title": "Founder",
            "company": "AI Startup",
            "source": "internet_scout"
        }
    ]
    
    goal = "Find AI startup founders"
    company_info = "VoiceFlow AI"
    
    try:
        result = validate_and_rank(test_profiles, goal, company_info)
        print(f"    ✅ Success!")
        print(f"    Input profiles: {len(test_profiles)}")
        print(f"    Unique profiles: {len(result)}")
        print(f"    Top profile: {result[0]['name']} (score: {result[0]['score']})")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    return True

def test_full_pipeline():
    """Test the complete pipeline end-to-end"""
    print("\n🚀 Testing Full Pipeline...")
    
    # Simulate the main app flow
    test_input = {
        "emails": ["founder@startup.com"],
        "company_info": "VoiceFlow AI", 
        "goal": "Find Bay Area SaaS founders looking for AI-powered voice solutions",
        "target": 5
    }
    
    try:
        # 1. Goal interpretation
        print("    Step 1: Goal interpretation...")
        search_plan = interpret_goal(
            test_input['goal'], 
            test_input['company_info'], 
            test_input['emails']
        )
        
        # 2. Scouting
        print("    Step 2: Profile scouting...")
        profiles = []
        
        # Email scouting
        for email in test_input['emails']:
            profiles.extend(scout_from_email(email))
        
        # LinkedIn scouting  
        for query in search_plan.get('linkedin_queries', []):
            profiles.extend(linkedin_scout(query))
        
        # X scouting
        for query in search_plan.get('x_queries', []):
            profiles.extend(x_scout(query))
        
        # Internet scouting
        for query in search_plan.get('internet_queries', []):
            profiles.extend(internet_scout(query))
        
        print(f"    Found {len(profiles)} total profiles")
        
        # 3. Validation & Ranking
        print("    Step 3: Validation & ranking...")
        unique_profiles = validate_and_rank(profiles, test_input['goal'], test_input['company_info'])
        unique_profiles = unique_profiles[:test_input['target']]
        
        # 4. Message generation
        print("    Step 4: Message generation...")
        for profile in unique_profiles:
            profile['message'] = generate_message(profile, test_input['goal'], test_input['company_info'])
        
        print(f"    ✅ Pipeline Success!")
        print(f"    Final result: {len(unique_profiles)} enriched profiles with messages")
        
        # Show sample result
        if unique_profiles:
            sample = unique_profiles[0]
            print(f"\n    Sample Profile:")
            print(f"      Name: {sample['name']}")
            print(f"      Title: {sample['title']}")
            print(f"      Company: {sample['company']}")
            print(f"      Message: {sample['message'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Pipeline Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Pre-Funnel Agent Testing Suite")
    print("=" * 50)
    
    tests = [
        ("Reasoning Agent (Gemini)", test_reasoning_agent),
        ("Message Generation (Gemini)", test_message_generation), 
        ("Mock Scout Agents", test_mock_agents),
        ("Validation & Ranking", test_validation_ranking),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your Pre-Funnel backend is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 