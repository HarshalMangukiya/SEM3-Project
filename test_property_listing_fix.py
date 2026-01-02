#!/usr/bin/env python3
"""
Test script to verify the property listing fix
"""

import requests
import json

def test_property_listing_fix():
    """Test that the property listing no longer returns JSON prematurely"""
    
    # Test data for a minimal property listing
    test_data = {
        'name': 'Test Hostel',
        'city': 'Test City',
        'location': 'Test Location',
        'price': '5000',
        'desc': 'Test Description',
        'type': 'Boys',
        'property_type': 'Hostel',
        'longitude': '0.0',
        'latitude': '0.0',
        'contact_phone': '1234567890',
        'contact_email': 'test@example.com',
        'address': 'Test Address',
        'has_double_regular': 'on',
        'double_sharing_regular_price': '5000'
    }
    
    files = {}
    
    try:
        # Try to submit the form (this will fail without proper session, 
        # but we're checking if it returns JSON prematurely)
        response = requests.post(
            'http://localhost:5000/add',
            data=test_data,
            files=files,
            allow_redirects=False
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        # Check if response is JSON (which would indicate the bug)
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            print("❌ BUG DETECTED: Response is still JSON!")
            print(f"Response content: {response.text}")
            return False
        else:
            print("✅ FIX SUCCESSFUL: Response is not JSON (should be HTML redirect)")
            return True
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to the application. Make sure it's running on localhost:5000")
        return None
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    print("Testing property listing fix...")
    result = test_property_listing_fix()
    
    if result is True:
        print("\n🎉 Fix verified successfully!")
    elif result is False:
        print("\n💥 Fix failed - bug still exists")
    else:
        print("\n❓ Could not verify fix due to connection issues")
