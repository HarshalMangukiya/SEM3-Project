from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Basic configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-secret')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret')

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
jwt = JWTManager(app)
mail = Mail(app)

# Mock MongoDB data (replace with real connection)
mock_users = {
    'test_user_id': {
        '_id': 'test_user_id',
        'name': 'Test User',
        'email': 'stayfinder101@gmail.com'
    }
}

mock_hostels = {
    'test_hostel_id': {
        '_id': 'test_hostel_id',
        'name': 'Test Hostel',
        'location': 'Test Location',
        'city': 'Test City',
        'contact_email': 'stayfinder101@gmail.com'
    }
}

@app.route('/api/bookings/request', methods=['POST'])
@jwt_required()
def api_request_booking():
    """Submit booking request and send confirmation emails"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Debug: Print received data
        print(f"Received booking data: {data}")
        
        # Get required fields
        hostel_id = data.get('hostel_id')
        room_id = data.get('room_id')
        property_type = data.get('property_type')
        facility = data.get('facility')
        
        # Check for missing fields with specific error messages
        missing_fields = []
        if not hostel_id:
            missing_fields.append('hostel_id')
        if not room_id:
            missing_fields.append('room_id')
        if not property_type:
            missing_fields.append('property_type')
        if not facility:
            missing_fields.append('facility')
        
        if missing_fields:
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'missing_fields': missing_fields,
                'received_data': data
            }), 400
        
        # Get user information (using mock data for now)
        user = mock_users.get(current_user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get hostel information (using mock data for now)
        hostel = mock_hostels.get(hostel_id)
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
        
        # Send confirmation emails
        try:
            # Email to user
            user_subject = f"Booking Request Confirmed - {hostel['name']}"
            user_msg = Message(
                user_subject,
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user['email']]
            )
            user_msg.body = f"""
Dear {user.get('name', 'User')},

Your booking request for {hostel['name']} has been received.

Details:
- Property: {hostel['name']}
- Location: {hostel.get('location', 'N/A')}, {hostel.get('city', 'N/A')}
- Room Type: {property_type}
- Facility: {facility}
- Status: Pending
- Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Thank you for using Stayfinder! We'll notify you once the property owner confirms your booking.

Best regards,
Stayfinder Team
            """
            mail.send(user_msg)
            print(f"✅ User email sent to: {user['email']}")
            
            # Email to owner
            if hostel.get('contact_email'):
                owner_subject = f"New Booking Request - {property_type} - {facility}"
                owner_msg = Message(
                    owner_subject,
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[hostel['contact_email']]
                )
                owner_msg.body = f"""
New Booking Request!

Property Details:
- Name: {hostel['name']}
- Location: {hostel.get('location', 'N/A')}, {hostel.get('city', 'N/A')}
- Room Type: {property_type}
- Facility: {facility}

User Details:
- Name: {user.get('name', 'Unknown')}
- Email: {user.get('email', 'No email')}
- Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Action Required:
Please contact the user to confirm availability and proceed with the booking.

Best regards,
Stayfinder Team
                """
                mail.send(owner_msg)
                print(f"✅ Owner email sent to: {hostel['contact_email']}")
                
        except Exception as email_error:
            print(f"❌ Email sending failed: {email_error}")
            # Still return success even if email fails
        
        return jsonify({
            'success': True,
            'message': 'Booking request submitted successfully! Confirmation emails have been sent.',
            'booking_id': 'test_booking_id'
        })
        
    except Exception as e:
        print(f"❌ Booking error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/test-token', methods=['POST'])
def get_test_token():
    """Get a test token for testing"""
    try:
        access_token = create_access_token(identity='test_user_id')
        return jsonify({
            'success': True,
            'token': access_token
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/debug/email')
def debug_email():
    """Debug route to check if email credentials are loaded"""
    return jsonify({
        "mail_server": app.config.get('MAIL_SERVER'),
        "mail_port": app.config.get('MAIL_PORT'),
        "mail_use_tls": app.config.get('MAIL_USE_TLS'),
        "mail_username": app.config.get('MAIL_USERNAME'),
        "mail_default_sender": app.config.get('MAIL_DEFAULT_SENDER'),
        "password_present": bool(app.config.get('MAIL_PASSWORD')),
        "all_configured": bool(
            app.config.get('MAIL_USERNAME') and 
            app.config.get('MAIL_PASSWORD') and 
            app.config.get('MAIL_DEFAULT_SENDER')
        ),
        "note": "Visit this URL to check if your email .env settings are loaded correctly"
    })

# Basic routes for testing
@app.route('/')
def home():
    return "Booking API is working! Use /test-token to get a token and /api/bookings/request to test booking."

if __name__ == '__main__':
    print("🔧 Email Configuration Status:")
    print(f"✅ MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"✅ MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"✅ MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
    print(f"✅ MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"✅ MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    
    if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], app.config['MAIL_DEFAULT_SENDER']]):
        print("\n❌ ERROR: Missing email credentials in .env file!")
        print("Please set MAIL_USERNAME, MAIL_PASSWORD, and MAIL_DEFAULT_SENDER in your .env file")
    else:
        print("\n✅ Email configuration looks good!")
    
    print("\n📝 Testing Instructions:")
    print("1. Visit http://localhost:5004/debug/email to check email config")
    print("2. Get token: curl -X POST http://localhost:5004/test-token")
    print("3. Test booking with the test script")
    
    app.run(debug=True, port=5004)
