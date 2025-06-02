#!/usr/bin/env python3
"""
Enhanced startup and test script for CowTracker with Chilean Central Bank API integration
"""

import sys
import subprocess
import time
import requests
import json
from datetime import datetime, timedelta
import threading
import webbrowser

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "pydantic==2.5.0",
        "python-multipart==0.0.6",
        "transbank-sdk==4.0.0",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "aiohttp==3.9.1"
    ]
    
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    print("✅ All dependencies installed successfully!")
    return True

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    try:
        # Start server in background
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", "--reload", "--port", "8000"
        ], cwd="c:\\Users\\daner\\Documents\\GitHub\\ct-fastapi")
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Test if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server started successfully!")
                return process
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException:
            print("❌ Server is not responding")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_bcentral_api():
    """Test Chilean Central Bank API endpoints"""
    print("\n🏦 Testing Chilean Central Bank API Integration:")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("/bcentral/exchange-rate", "💱 Exchange Rate (USD/CLP)"),
        ("/bcentral/uf", "📈 UF (Unidad de Fomento)"),
        ("/bcentral/utm", "📊 UTM (Unidad Tributaria Mensual)"),
        ("/bcentral/economic-indicators", "📉 Economic Indicators"),
        ("/bcentral/series", "📋 Available Series")
    ]
    
    results = []
    
    for endpoint, description in endpoints:
        print(f"\nTesting {description}...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: SUCCESS")
                
                if isinstance(data, list) and len(data) > 0:
                    print(f"   📊 Data points received: {len(data)}")
                    print(f"   📅 Latest entry: {data[0] if data else 'No data'}")
                elif isinstance(data, dict):
                    print(f"   📊 Response keys: {list(data.keys())}")
                    
                results.append((endpoint, "SUCCESS", len(data) if isinstance(data, list) else "N/A"))
                
            elif response.status_code == 401:
                print(f"🔐 {description}: AUTHENTICATION REQUIRED")
                print("   ⚠️  Please verify BCENTRAL_USER and BCENTRAL_PASSWORD in .env file")
                results.append((endpoint, "AUTH_ERROR", "N/A"))
                
            elif response.status_code == 500:
                print(f"❌ {description}: SERVER ERROR")
                print(f"   ⚠️  Error: {response.text[:100]}...")
                results.append((endpoint, "SERVER_ERROR", "N/A"))
                
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                results.append((endpoint, f"HTTP_{response.status_code}", "N/A"))
                
        except requests.exceptions.Timeout:
            print(f"⏰ {description}: TIMEOUT (>10s)")
            results.append((endpoint, "TIMEOUT", "N/A"))
            
        except requests.exceptions.ConnectionError:
            print(f"🔌 {description}: CONNECTION ERROR")
            results.append((endpoint, "CONNECTION_ERROR", "N/A"))
            
        except Exception as e:
            print(f"❌ {description}: ERROR - {str(e)[:50]}...")
            results.append((endpoint, "ERROR", "N/A"))
    
    return results

def generate_test_report(results):
    """Generate a test report"""
    print("\n📋 TEST SUMMARY REPORT")
    print("=" * 60)
    
    success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
    total_count = len(results)
    
    print(f"📊 Overall Status: {success_count}/{total_count} endpoints working")
    print(f"✅ Success Rate: {(success_count/total_count)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for endpoint, status, data_count in results:
        status_icon = "✅" if status == "SUCCESS" else "❌"
        print(f"{status_icon} {endpoint:<30} {status:<15} {data_count}")
    
    if success_count < total_count:
        print("\n💡 Troubleshooting Tips:")
        auth_errors = [r for r in results if r[1] == "AUTH_ERROR"]
        if auth_errors:
            print("   🔐 Authentication Issues:")
            print("      - Verify BCENTRAL_USER and BCENTRAL_PASSWORD in .env file")
            print("      - Check if credentials are valid with Chilean Central Bank")
            print("      - Ensure account has API access permissions")
        
        server_errors = [r for r in results if "ERROR" in r[1]]
        if server_errors:
            print("   🔧 Server Issues:")
            print("      - Check server logs for detailed error messages")
            print("      - Verify API endpoint URLs are correct")
            print("      - Test with smaller date ranges")

def open_interfaces():
    """Open test interfaces in browser"""
    print("\n🌐 Opening test interfaces...")
    
    # API Documentation
    try:
        webbrowser.open("http://localhost:8000/docs")
        print("✅ Opened API documentation at http://localhost:8000/docs")
    except:
        print("❌ Could not open API documentation automatically")
    
    # Test Interface
    test_file = "file:///c:/Users/daner/Documents/GitHub/ct-fastapi/test_bcentral.html"
    try:
        webbrowser.open(test_file)
        print("✅ Opened test interface")
    except:
        print("❌ Could not open test interface automatically")

def main():
    print("🐄 CowTracker with Chilean Central Bank Integration")
    print("🚀 Enhanced Startup & Test Script")
    print("=" * 60)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        return
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("❌ Failed to start server. Exiting.")
        return
    
    try:
        # Test API endpoints
        results = test_bcentral_api()
        
        # Generate report
        generate_test_report(results)
        
        # Open interfaces
        open_interfaces()
        
        print("\n🎯 Next Steps:")
        print("1. 📖 Review API documentation: http://localhost:8000/docs")
        print("2. 🧪 Use the test interface to try different endpoints")
        print("3. 📊 Check the example usage in: example_bcentral_usage.py")
        print("4. 🔧 If authentication fails, verify your Central Bank credentials")
        
        print("\n⏹️  Press Ctrl+C to stop the server")
        
        # Keep server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped successfully!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()
