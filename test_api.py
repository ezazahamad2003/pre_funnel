#!/usr/bin/env python3
"""
Test script for the Pre-Funnel API endpoint
Make sure the Flask app is running before executing this script
"""

import requests
import json
import time

API_BASE = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print(f"    ✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"    ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("    ❌ Cannot connect to API. Make sure Flask app is running!")
        return False
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def test_lead_discovery_endpoint():
    """Test the main lead discovery endpoint"""
    print("\n🎯 Testing Lead Discovery Endpoint...")
    
    test_cases = [
        {
            "name": "Valid Request - VoiceFlow AI",
            "payload": {
                "emails": ["sam@startup.com", "jane@aiworld.co"],
                "company_info": "VoiceFlow AI",
                "goal": "Find Bay Area SaaS founders looking for AI-powered voice solutions",
                "target": 5
            }
        },
        {
            "name": "Valid Request - Healthcare Tech",
            "payload": {
                "emails": ["doctor@medtech.com"],
                "company_info": "MedTech Solutions",
                "goal": "Connect with healthcare technology CTOs in Boston",
                "target": 3
            }
        },
        {
            "name": "Missing Required Field",
            "payload": {
                "emails": ["test@example.com"],
                "company_info": "Test Company"
                # Missing 'goal' field
            }
        },
        {
            "name": "Invalid Email Format",
            "payload": {
                "emails": "not-a-list",  # Should be a list
                "company_info": "Test Company",
                "goal": "Test goal"
            }
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/lead-discovery",
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'},
                timeout=60  # Give Gemini API time to respond
            )
            
            print(f"    Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                
                if response.status_code == 200:
                    profiles = response_data.get('profiles', [])
                    print(f"    ✅ Success! Found {len(profiles)} profiles")
                    
                    if profiles:
                        sample = profiles[0]
                        print(f"    Sample Profile: {sample.get('name')} - {sample.get('title')}")
                        print(f"    Sample Message: {sample.get('message', '')[:80]}...")
                    
                    if 'warnings' in response_data:
                        print(f"    ⚠️  Warnings: {len(response_data['warnings'])}")
                        
                elif response.status_code == 400:
                    print(f"    ⚠️  Expected validation error: {response_data.get('error')}")
                else:
                    print(f"    ❌ Unexpected status: {response_data}")
                
                results.append({
                    'test': test_case['name'],
                    'status': response.status_code,
                    'success': response.status_code in [200, 400]  # 400 is expected for invalid requests
                })
                
            except json.JSONDecodeError:
                print(f"    ❌ Invalid JSON response: {response.text}")
                results.append({
                    'test': test_case['name'],
                    'status': response.status_code,
                    'success': False
                })
                
        except requests.exceptions.Timeout:
            print(f"    ❌ Request timeout (>60s)")
            results.append({
                'test': test_case['name'],
                'status': 'timeout',
                'success': False
            })
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results.append({
                'test': test_case['name'],
                'status': 'error',
                'success': False
            })
    
    return results

def test_performance():
    """Test API performance with a simple request"""
    print("\n⚡ Testing API Performance...")
    
    payload = {
        "emails": ["test@example.com"],
        "company_info": "Test Company",
        "goal": "Quick performance test",
        "target": 2
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/api/lead-discovery",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=120
        )
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"    Response time: {duration:.2f} seconds")
        
        if duration < 10:
            print(f"    ✅ Fast response!")
        elif duration < 30:
            print(f"    ⚠️  Moderate response time")
        else:
            print(f"    ❌ Slow response (>{duration:.1f}s)")
        
        if response.status_code == 200:
            print(f"    ✅ Request successful")
            return True
        else:
            print(f"    ❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ❌ Performance test failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Pre-Funnel API Testing Suite")
    print("=" * 50)
    print("Make sure the Flask app is running: python app.py")
    print("=" * 50)
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("\n❌ Health check failed. Make sure the Flask app is running!")
        print("Run: python app.py")
        return
    
    # Test main functionality
    results = test_lead_discovery_endpoint()
    
    # Test performance
    performance_ok = test_performance()
    
    # Summary
    print(f"\n{'='*50}")
    print("🏁 API TEST SUMMARY")
    print("=" * 50)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['test']} (Status: {result['status']})")
    
    performance_status = "✅ PASS" if performance_ok else "❌ FAIL"
    print(f"{performance_status} - Performance Test")
    
    total_tests = len(results) + 1  # +1 for performance test
    passed_tests = sum(r['success'] for r in results) + (1 if performance_ok else 0)
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All API tests passed! Your Pre-Funnel API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("\n💡 Next Steps:")
    print("1. If Gemini tests pass, you can start integrating real data APIs")
    print("2. Test with real emails and see the AI-generated search strategies")
    print("3. Add more external API integrations (LinkedIn, Twitter, etc.)")

if __name__ == "__main__":
    main() 