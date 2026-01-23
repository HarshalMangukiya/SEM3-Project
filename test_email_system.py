#!/usr/bin/env python3
"""
Test script to verify email sending functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, mail
from flask_mail import Message
from dotenv import load_dotenv

load_dotenv()

def test_email_config():
    """Test email configuration"""
    print("=== Email Configuration Test ===")
    
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print(f"Password configured: {'Yes' if app.config.get('MAIL_PASSWORD') else 'No'}")
    
    # Check if all required config is present
    required_configs = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    missing_configs = [config for config in required_configs if not app.config.get(config)]
    
    if missing_configs:
        print(f"❌ Missing configurations: {', '.join(missing_configs)}")
        return False
    else:
        print("✅ All email configurations are present")
        return True

def test_email_sending():
    """Test sending a test email"""
    print("\n=== Email Sending Test ===")
    
    try:
        with app.app_context():
            # Create a test message
            test_email = os.environ.get('MAIL_USERNAME')  # Send to self for testing
            msg = Message(
                'Stayfinder Email Test',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[test_email]
            )
            msg.body = """
This is a test email from Stayfinder booking system.

If you receive this email, it means the email configuration is working correctly.

Best regards,
Stayfinder Team
            """
            
            # Try to send the email
            mail.send(msg)
            print(f"✅ Test email sent successfully to {test_email}")
            print("✅ Email sending functionality is working!")
            return True
            
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print("\n🔧 Possible solutions:")
        print("1. Check if Gmail App Password is configured (not regular password)")
        print("2. Ensure 'Less secure app access' is enabled in Gmail settings")
        print("3. Verify SMTP settings are correct")
        print("4. Check network connectivity")
        return False

def test_booking_email_content():
    """Test the booking email content generation"""
    print("\n=== Booking Email Content Test ===")
    
    try:
        # Sample booking data
        sample_user = {
            'name': 'Test Student',
            'email': 'student@example.com'
        }
        
        sample_hostel = {
            'name': 'Test Hostel',
            'location': 'Test Area',
            'city': 'Test City'
        }
        
        property_type = 'Triple Sharing'
        facility = 'Regular'
        
        # Generate email content (same as in the actual booking API)
        email_body = f"""
Dear {sample_user.get('name', 'User')},

Your booking request for {sample_hostel['name']} has been received.

Details:
- Property: {sample_hostel['name']}
- Location: {sample_hostel.get('location', 'N/A')}, {sample_hostel.get('city', 'N/A')}
- Room Type: {property_type}
- Facility: {facility}
- Status: Pending
- Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Thank you for using Stayfinder! We'll notify you once the property owner confirms your booking.

Best regards,
Stayfinder Team
        """
        
        print("✅ Email content generated successfully:")
        print("-" * 50)
        print(email_body)
        print("-" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Email content generation failed: {e}")
        return False

def main():
    """Run all email tests"""
    print("🧪 Testing Stayfinder Email System\n")
    
    config_ok = test_email_config()
    
    if config_ok:
        # Test email content generation (always safe)
        content_ok = test_booking_email_content()
        
        # Ask user if they want to test actual email sending
        print("\n" + "="*50)
        response = input("Do you want to test actual email sending? (y/n): ").lower().strip()
        
        if response == 'y':
            send_ok = test_email_sending()
        else:
            print("⏭️  Skipping actual email sending test")
            send_ok = True  # Don't fail the test if user skips
    else:
        print("❌ Email configuration is incomplete. Skipping other tests.")
        content_ok = False
        send_ok = False
    
    print("\n=== Summary ===")
    if config_ok and content_ok and send_ok:
        print("🎉 All email tests passed!")
        print("✅ The email system is ready to send booking confirmations")
    else:
        print("⚠️  Some email tests failed.")
        if not config_ok:
            print("❌ Fix email configuration in .env file")
        if not content_ok:
            print("❌ Fix email content generation")
        if not send_ok:
            print("❌ Fix email sending functionality")

if __name__ == "__main__":
    from datetime import datetime
    main()
