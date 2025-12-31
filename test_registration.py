#!/usr/bin/env python3
"""
Test script to verify user and owner registration system
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_user_registration():
    """Test regular user registration"""
    print("🧪 Testing User Registration...")
    
    user_data = {
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'test123456'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", data=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 302:  # Redirect after successful registration
            print("✅ User registration successful!")
            return True
        else:
            print("❌ User registration failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_owner_registration():
    """Test owner registration"""
    print("\n🧪 Testing Owner Registration...")
    
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
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 302:  # Redirect after successful registration
            print("✅ Owner registration successful!")
            return True
        else:
            print("❌ Owner registration failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login():
    """Test login for both user types"""
    print("\n🧪 Testing User Login...")
    
    # Test user login
    user_login = {
        'email': 'testuser@example.com',
        'password': 'test123456'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", data=user_login)
        print(f"User Login Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ User login successful!")
        else:
            print("❌ User login failed!")
    except Exception as e:
        print(f"❌ User login error: {e}")
    
    # Test owner login
    print("\n🧪 Testing Owner Login...")
    owner_login = {
        'email': 'testowner@example.com',
        'password': 'test123456'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", data=owner_login)
        print(f"Owner Login Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Owner login successful!")
        else:
            print("❌ Owner login failed!")
    except Exception as e:
        print(f"❌ Owner login error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Registration System Tests...\n")
    
    # Test registrations
    user_success = test_user_registration()
    owner_success = test_owner_registration()
    
    # Test logins
    if user_success or owner_success:
        test_login()
    
    print("\n🎯 Test completed!")
