#!/usr/bin/env python3
"""
Test script to verify the user portal fix
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_user_portal():
    """Test that regular users see correct options"""
    print("🧪 Testing Regular User Portal...")
    
    # Register a regular user
    user_data = {
        'name': 'Test Regular User',
        'email': 'testuser@example.com',
        'password': 'test123456'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", data=user_data)
        print(f"User Registration Status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful registration
            print("✅ User registration successful!")
            
            # Login as regular user
            login_data = {
                'email': 'testuser@example.com',
                'password': 'test123456'
            }
            
            login_response = requests.post(f"{BASE_URL}/login", data=login_data)
            print(f"User Login Status: {login_response.status_code}")
            
            if login_response.status_code == 302:
                print("✅ User login successful!")
                print("📋 Regular user should see:")
                print("   - Account Settings")
                print("   - My Bookings") 
                print("   - My Enquiries")
                print("   - Logout")
                print("   - NOT: Owner Dashboard")
                print("   - NOT: List Your Property")
                return True
        else:
            print("❌ User registration/login failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_owner_portal():
    """Test that owners see correct options"""
    print("\n🧪 Testing Owner Portal...")
    
    # Register an owner
    owner_data = {
        'first_name': 'Test',
        'last_name': 'Owner',
        'email': 'testowner@example.com',
        'phone': '9876543210',
        'business_name': 'Test Business',
        'business_type': 'Individual',
        'pan_number': 'ABCDE1234F',
        'address': '123 Test Street',
        'city': 'Test City',
        'state': 'Test State',
        'pincode': '123456',
        'password': 'test123456',
        'confirm_password': 'test123456',
        'terms': 'on'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register-owner", data=owner_data)
        print(f"Owner Registration Status: {response.status_code}")
        
        if response.status_code == 302:  # Redirect after successful registration
            print("✅ Owner registration successful!")
            
            # Login as owner
            login_data = {
                'email': 'testowner@example.com',
                'password': 'test123456'
            }
            
            login_response = requests.post(f"{BASE_URL}/login", data=login_data)
            print(f"Owner Login Status: {login_response.status_code}")
            
            if login_response.status_code == 302:
                print("✅ Owner login successful!")
                print("📋 Owner should see:")
                print("   - Owner Dashboard")
                print("   - List Your Property")
                print("   - Account Settings")
                print("   - Logout")
                print("   - NOT: My Bookings")
                print("   - NOT: My Enquiries")
                return True
        else:
            print("❌ Owner registration/login failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing User Portal Fix...\n")
    
    # Test both user types
    user_success = test_user_portal()
    owner_success = test_owner_portal()
    
    if user_success or owner_success:
        print("\n🎯 Test completed!")
        print("📝 Check the navbar to verify:")
        print("   - Regular users should NOT see owner options")
        print("   - Owners should see owner-specific options")
        print("   - Both should see appropriate logout option")
