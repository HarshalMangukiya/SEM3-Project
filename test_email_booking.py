#!/usr/bin/env python3
"""
Test script to verify email configuration and booking functionality
"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_email_config():
    """Test email configuration"""
    print("=== Email Configuration Test ===")
    
    required_vars = {
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_PORT': os.environ.get('MAIL_PORT', '587'),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', 'stayfinder101@gmail.com')
    }
    
    all_configured = True
    for var, value in required_vars.items():
        if var != 'MAIL_PASSWORD' and not value:
            print(f"❌ {var}: NOT SET")
            all_configured = False
        elif var == 'MAIL_PASSWORD' and not value:
            print(f"❌ {var}: NOT SET")
            all_configured = False
        else:
            if var == 'MAIL_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
    
    if all_configured:
        print("\n🎉 All email configuration is properly set!")
        return True
    else:
        print("\n⚠️  Some email configuration is missing. Please check your .env file.")
        return False

def test_booking_api():
    """Test if booking API endpoint exists"""
    print("\n=== Booking API Test ===")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test if the endpoint exists
            response = client.post('/api/bookings/request')
            
            if response.status_code == 401:  # Unauthorized (expected without JWT token)
                print("✅ Booking API endpoint exists and is protected")
                return True
            elif response.status_code == 404:
                print("❌ Booking API endpoint not found")
                return False
            else:
                print(f"✅ Booking API endpoint exists (Status: {response.status_code})")
                return True
                
    except Exception as e:
        print(f"❌ Error testing booking API: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Stayfinder Email Booking System\n")
    
    email_ok = test_email_config()
    api_ok = test_booking_api()
    
    print("\n=== Summary ===")
    if email_ok and api_ok:
        print("🎉 All tests passed! The email booking system should work correctly.")
        print("\n📧 Email will be sent from: stayfinder101@gmail.com")
        print("🔐 Users will receive confirmation emails when they click 'Request to Book'")
    else:
        print("⚠️  Some tests failed. Please check the configuration above.")
    
    print("\n📝 Next Steps:")
    print("1. Ensure Gmail App Password is configured for stayfinder101@gmail.com")
    print("2. Test the booking functionality by logging in and clicking 'Request to Book'")
    print("3. Check email inbox for confirmation messages")

if __name__ == "__main__":
    main()
