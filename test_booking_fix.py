# Quick Fix Script - Run this to test your booking functionality

from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
from datetime import datetime

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

@app.route('/test-booking', methods=['POST'])
@jwt_required()
def test_booking():
    """Test booking endpoint without database dependencies"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get required fields
        hostel_id = data.get('hostel_id')
        room_id = data.get('room_id')
        property_type = data.get('property_type')
        facility = data.get('facility')
        
        if not all([hostel_id, room_id, property_type, facility]):
            return jsonify({
                'success': False,
                'message': 'Missing required booking information'
            }), 400
        
        # Simulate user data (replace with actual user lookup)
        user = {
            'name': 'Test User',
            'email': 'stayfinder101@gmail.com'
        }
        
        # Simulate hostel data (replace with actual hostel lookup)
        hostel = {
            'name': 'Test Hostel',
            'contact_email': 'stayfinder101@gmail.com'
        }
        
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
            Dear {user['name']},
            
            Your booking request for {hostel['name']} has been received.
            
            Details:
            - Property: {hostel['name']}
            - Room Type: {property_type}
            - Facility: {facility}
            - Status: Pending
            
            Thank you for using Stayfinder!
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
                
                Property: {hostel['name']}
                User: {user['name']} ({user['email']})
                Room Type: {property_type}
                Facility: {facility}
                Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                
                Please contact the user to confirm availability.
                """
                mail.send(owner_msg)
                print(f"✅ Owner email sent to: {hostel['contact_email']}")
                
        except Exception as email_error:
            print(f"❌ Email sending failed: {email_error}")
            return jsonify({
                'success': False,
                'message': f'Email sending failed: {str(email_error)}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Booking request submitted successfully! Confirmation emails have been sent.',
            'booking_id': 'test_booking_id'
        })
        
    except Exception as e:
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

if __name__ == '__main__':
    print("🔧 Email Configuration Status:")
    print(f"✅ MAIL_SERVER: {app.config['MAIL_SERVER']}")
    print(f"✅ MAIL_PORT: {app.config['MAIL_PORT']}")
    print(f"✅ MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
    print(f"✅ MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
    print(f"✅ MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")
    
    if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
        print("\n❌ ERROR: Missing email credentials in .env file!")
        print("Please set MAIL_USERNAME and MAIL_PASSWORD in your .env file")
    else:
        print("\n✅ Email configuration looks good!")
    
    print("\n📝 Testing Instructions:")
    print("1. Run this app: python test_booking_fix.py")
    print("2. Get token: curl -X POST http://localhost:5002/test-token")
    print("3. Test booking: curl -X POST http://localhost:5002/test-booking \\")
    print("   -H 'Authorization: Bearer YOUR_TOKEN' \\")
    print("   -H 'Content-Type: application/json' \\")
    print("   -d '{\"hostel_id\":\"123\",\"room_id\":\"double_regular\",\"property_type\":\"Double Sharing\",\"facility\":\"Regular\"}'")
    
    app.run(debug=True, port=5002)
