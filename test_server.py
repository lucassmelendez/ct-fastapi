#!/usr/bin/env python3
"""
Test script to verify the CowTracker FastAPI server with Chilean Central Bank integration
"""

import requests
import json
from datetime import datetime, timedelta

# Server URL
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start it with: python -m uvicorn main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_bcentral_endpoints():
    """Test Chilean Central Bank endpoints"""
    endpoints = [
        "/bcentral/exchange-rate",
        "/bcentral/uf", 
        "/bcentral/utm",
        "/bcentral/economic-indicators",
        "/bcentral/series"
    ]
    
    print("\n🏦 Testing Chilean Central Bank Endpoints:")
    print("-" * 50)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"   📊 Data points: {len(data)}")
                    print(f"   📅 Sample: {data[0] if data else 'No data'}")
                elif isinstance(data, dict):
                    print(f"   📊 Response: {list(data.keys())}")
            else:
                print(f"   ⚠️  Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
        
        print()

def test_cow_endpoints():
    """Test basic cow tracking endpoints"""
    print("\n🐄 Testing Cow Tracking Endpoints:")
    print("-" * 40)
    
    endpoints = [
        ("/cows", "GET"),
        ("/", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {method} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {method} {endpoint}: Error - {e}")

def main():
    print("🚀 CowTracker API Test Suite")
    print("=" * 50)
    
    # Test if server is running
    if not test_health_endpoint():
        print("\n💡 To start the server, run:")
        print("   cd c:\\Users\\daner\\Documents\\GitHub\\ct-fastapi")
        print("   python -m uvicorn main:app --reload --port 8000")
        return
    
    # Test endpoints
    test_cow_endpoints()
    test_bcentral_endpoints()
    
    print("\n📖 API Documentation available at:")
    print(f"   {BASE_URL}/docs")
    print(f"   {BASE_URL}/redoc")
    
    print("\n🧪 Test interfaces available at:")
    print("   file:///c:/Users/daner/Documents/GitHub/ct-fastapi/test_bcentral.html")

if __name__ == "__main__":
    main()
