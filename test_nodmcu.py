#!/usr/bin/env python3
"""
Test script to verify NodeMCU connection and servo control
Run this script to test the connection before using the main application
"""

import requests
import json
import time

# NodeMCU configuration
NODEMCU_IP = "192.168.1.100"  # Change this to your NodeMCU IP address
NODEMCU_PORT = 80
BASE_URL = f"http://{NODEMCU_IP}:{NODEMCU_PORT}"

def test_connection():
    """Test basic connection to NodeMCU"""
    print("Testing NodeMCU connection...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Connection successful!")
            print(f"Response: {response.text[:200]}...")
            return True
        else:
            print(f"❌ Connection failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_status():
    """Test status endpoint"""
    print("\nTesting status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint working!")
            print(f"Status: {data.get('status')}")
            print(f"IP: {data.get('ip')}")
            print(f"Uptime: {data.get('uptime')} seconds")
            print(f"Dispensing: {data.get('dispensing')}")
            print(f"Servo Position: {data.get('servo_position')}°")
            return True
        else:
            print(f"❌ Status endpoint failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Status endpoint error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def test_dispense():
    """Test medicine dispensing"""
    print("\nTesting medicine dispensing...")
    try:
        response = requests.post(f"{BASE_URL}/dispense", 
                               json={"action": "dispense"}, 
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Dispense command sent successfully!")
            print(f"Response: {data}")
            
            # Wait a moment and check status
            time.sleep(3)
            status_response = requests.get(f"{BASE_URL}/status", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"Current servo position: {status_data.get('servo_position')}°")
                print(f"Currently dispensing: {status_data.get('dispensing')}")
            
            return True
        else:
            print(f"❌ Dispense command failed with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Dispense command error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("NodeMCU Medical Dispensing System Test")
    print("=" * 50)
    print(f"Testing connection to: {BASE_URL}")
    print()
    
    # Test connection
    if not test_connection():
        print("\n❌ Cannot connect to NodeMCU. Please check:")
        print("1. NodeMCU is powered on and connected to WiFi")
        print("2. IP address is correct")
        print("3. Network connectivity")
        return
    
    # Test status endpoint
    if not test_status():
        print("\n❌ Status endpoint not working properly")
        return
    
    # Ask user if they want to test dispensing
    print("\n" + "=" * 50)
    user_input = input("Do you want to test medicine dispensing? (y/n): ").lower().strip()
    
    if user_input in ['y', 'yes']:
        print("\n⚠️  WARNING: This will move the servo motor!")
        confirm = input("Are you sure? (y/n): ").lower().strip()
        
        if confirm in ['y', 'yes']:
            test_dispense()
        else:
            print("Dispense test cancelled.")
    else:
        print("Skipping dispense test.")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
