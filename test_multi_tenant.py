#!/usr/bin/env python3

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"

def test_user_creation():
    """Test user creation endpoint"""
    print("🧪 Testing User Creation...")
    
    response = requests.post(f"{BASE_URL}/api/user/create", json={
        "email": "test@startup.com"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ User created: {data['user_id']}")
        return data['user_id']
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_lead_discovery_with_user(user_id):
    """Test lead discovery with user context"""
    print("🧪 Testing Lead Discovery with User Context...")
    
    response = requests.post(f"{BASE_URL}/api/lead-discovery", json={
        "user_id": user_id,
        "emails": ["founder@startup.com"],
        "company_info": "VoiceFlow AI",
        "goal": "Find Bay Area SaaS founders looking for AI solutions",
        "target": 3
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Found {data['returned']} profiles for user {user_id}")
        print(f"  📊 Total discovered: {data['total_found']}")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return False

def test_user_connections(user_id):
    """Test user connections endpoint"""
    print("🧪 Testing User Connections...")
    
    response = requests.get(f"{BASE_URL}/api/user/{user_id}/connections")
    
    if response.status_code == 200:
        data = response.json()
        connections = data['connections']
        print(f"  ✅ Connections - Twitter: {connections['twitter']}, LinkedIn: {connections['linkedin']}")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return False

def test_user_usage(user_id):
    """Test user usage statistics"""
    print("🧪 Testing User Usage Statistics...")
    
    response = requests.get(f"{BASE_URL}/api/usage/{user_id}")
    
    if response.status_code == 200:
        data = response.json()
        usage = data['usage']
        print(f"  ✅ Usage - Twitter: {usage['twitter']}, LinkedIn: {usage['linkedin']}")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return False

def test_lead_discovery_with_email():
    """Test automatic user creation with email"""
    print("🧪 Testing Auto User Creation with Email...")
    
    response = requests.post(f"{BASE_URL}/api/lead-discovery", json={
        "user_email": "auto@startup.com",
        "emails": ["founder@startup.com"],
        "company_info": "VoiceFlow AI",
        "goal": "Find Bay Area SaaS founders",
        "target": 2
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Auto-created user: {data['user_id']}")
        print(f"  ✅ Found {data['returned']} profiles")
        return data['user_id']
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return None

def test_health_check():
    """Test health check endpoint"""
    print("🧪 Testing Health Check...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ {data['message']}")
        return True
    else:
        print(f"  ❌ Failed: {response.status_code} - {response.text}")
        return False

def main():
    print("🚀 Multi-Tenant Pre-Funnel Testing Suite")
    print("=" * 50)
    
    # Test results tracking
    tests_passed = 0
    total_tests = 6
    
    try:
        # Test 1: Health check
        if test_health_check():
            tests_passed += 1
        
        print()
        
        # Test 2: User creation
        user_id = test_user_creation()
        if user_id:
            tests_passed += 1
        
        print()
        
        # Test 3: Lead discovery with user context
        if user_id and test_lead_discovery_with_user(user_id):
            tests_passed += 1
        
        print()
        
        # Test 4: User connections
        if user_id and test_user_connections(user_id):
            tests_passed += 1
        
        print()
        
        # Test 5: User usage statistics
        if user_id and test_user_usage(user_id):
            tests_passed += 1
        
        print()
        
        # Test 6: Auto user creation
        auto_user_id = test_lead_discovery_with_email()
        if auto_user_id:
            tests_passed += 1
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Flask server is running")
        print("   Start with: python app.py")
        return
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return
    
    # Summary
    print()
    print("=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)
    
    if tests_passed == total_tests:
        print("🎉 All multi-tenant tests passed!")
        print("✅ User management working")
        print("✅ Multi-tenant lead discovery working")
        print("✅ Usage tracking working")
        print("✅ Auto user creation working")
    else:
        print(f"⚠️  {tests_passed}/{total_tests} tests passed")
    
    print(f"\nResults: {tests_passed}/{total_tests} tests passed")

if __name__ == "__main__":
    main() 