#!/usr/bin/env python3
"""
Test script to verify email configuration
"""

import os
import sys
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app for testing
app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'stayfinder101@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'Mangukiya@108')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'stayfinder101@gmail.com')

# Initialize mail
mail = Mail(app)

def test_email_config():
    """Test email configuration"""
    print("🔧 Testing Email Configuration")
    print("=" * 50)
    
    print(f"Mail Server: {app.config['MAIL_SERVER']}")
    print(f"Mail Port: {app.config['MAIL_PORT']}")
    print(f"Mail Use TLS: {app.config['MAIL_USE_TLS']}")
    print(f"Mail Username: {app.config['MAIL_USERNAME']}")
    print(f"Mail Default Sender: {app.config['MAIL_DEFAULT_SENDER']}")
    print(f"Password Present: {'Yes' if app.config['MAIL_PASSWORD'] else 'No'}")
    
    return True

def test_send_email():
    """Test sending an email"""
    print("\n📧 Testing Email Sending")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Create test message
            msg = Message(
                'Stayfinder Email Test',
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=['stayfinder101@gmail.com']  # Send to self for testing
            )
            msg.html = """
            <h2>✅ Email Configuration Test Successful!</h2>
            <p>This is a test email from Stayfinder to verify that the email configuration is working correctly.</p>
            <p><strong>Details:</strong></p>
            <ul>
                <li>From: stayfinder101@gmail.com</li>
                <li>To: stayfinder101@gmail.com</li>
                <li>Server: smtp.gmail.com</li>
                <li>Port: 587</li>
                <li>TLS: Enabled</li>
            </ul>
            <p>If you receive this email, the email functionality is working properly!</p>
            <hr>
            <p><em>Stayfinder Email System Test</em></p>
            """
            
            # Send email
            mail.send(msg)
            print("✅ Test email sent successfully!")
            print("📬 Check your inbox at stayfinder101@gmail.com")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Stayfinder Email Configuration Test")
    print("=" * 60)
    
    # Test configuration
    config_ok = test_email_config()
    
    if config_ok:
        # Test email sending
        email_ok = test_send_email()
        
        if email_ok:
            print("\n🎉 All tests passed! Email functionality is working correctly.")
        else:
            print("\n⚠️ Email test failed. Check the error message above.")
    else:
        print("\n❌ Configuration test failed.")
