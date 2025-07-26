#!/usr/bin/env python3

import requests
import time
import sys

def test_health_endpoint():
    """Test the health endpoint with proper error handling"""
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/health"
    
    print(f"Testing health endpoint: {health_url}")
    
    # Test basic connectivity first
    try:
        print("Testing basic connectivity...")
        response = requests.get(health_url, timeout=5)
        print(f"✅ Connected successfully!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed!")
            print(f"Uptime: {data.get('uptime_seconds', 'N/A')} seconds")
            print(f"Status: {data.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_other_endpoints():
    """Test other endpoints to see if they work"""
    base_url = "http://localhost:8000"
    endpoints = [
        "/",
        "/docs",
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            print(f"\nTesting {url}...")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

if __name__ == "__main__":
    print("🔍 Testing Theobroma API Health...")
    print("=" * 50)
    
    # Wait a bit for the API to be ready
    print("Waiting for API to be ready...")
    time.sleep(5)
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    
    # Test other endpoints
    test_other_endpoints()
    
    if health_ok:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Health check failed!")
        sys.exit(1)
