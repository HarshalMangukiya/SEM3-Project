from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

print("Email Configuration:")
print(f"  Server: {app.config['MAIL_SERVER']}")
print(f"  Port: {app.config['MAIL_PORT']}")
print(f"  TLS: {app.config['MAIL_USE_TLS']}")
print(f"  Username: {app.config['MAIL_USERNAME']}")
print(f"  Password: {'*' * len(app.config['MAIL_PASSWORD']) if app.config['MAIL_PASSWORD'] else 'NOT SET'}")

# Test email - sends to the same stayfinder account
TEST_EMAIL = "stayfinder101@gmail.com"

with app.app_context():
    try:
        msg = Message(
            subject="StayFinder - Test Email",
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[TEST_EMAIL]
        )
        msg.body = "This is a test email from StayFinder. If you received this, email configuration is working correctly!"
        msg.html = """
        <h2>🎉 Email Test Successful!</h2>
        <p>Your StayFinder email configuration is working correctly.</p>
        <p>Booking confirmation emails will now be sent from <strong>stayfinder101@gmail.com</strong></p>
        """
        mail.send(msg)
        print(f"\n[SUCCESS] Email sent successfully to {TEST_EMAIL}!")
    except Exception as e:
        print(f"\n[ERROR] Failed to send email: {e}")
