from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# JWT configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-secret')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')
jwt = JWTManager(app)

# Initialize Mail
mail = Mail(app)

@app.route('/test-email', methods=['POST'])
@jwt_required()
def test_email():
    """Test email sending functionality"""
    try:
        current_user_id = get_jwt_identity()
        
        # Test email
        msg = Message(
            'Test Email from Stayfinder',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=['stayfinder101@gmail.com']  # Send to yourself for testing
        )
        msg.body = 'This is a test email to verify email configuration is working.'
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Email test failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("Email Configuration:")
    print(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
    print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    print("\nTo test email functionality:")
    print("1. Run this app: python test_email.py")
    print("2. Get a JWT token by logging into your main app")
    print("3. Send POST request to /test-email with Authorization header")
    app.run(debug=True, port=5001)
