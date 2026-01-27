from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, verify_jwt_in_request
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from bson import json_util
import os
import re
import ssl
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from authlib.integrations.flask_client import OAuth
import bcrypt
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth
import json
import math
from pymongo import MongoClient
import random
import string

# Import custom modules
from config.settings import config
from utils.database import load_colleges, calculate_distance, find_college_by_name, serialize_doc, get_database_connection

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder="templates")

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# Set JWT token expiration to 24 hours (must be before JWT initialization)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize JWT
jwt = JWTManager(app)

# Initialize OAuth
oauth = OAuth(app)

# --- DATABASE CONFIGURATION ---
# Use the database connection from utils
mongo = get_database_connection(app.config['MONGO_URI'])

# --- CLOUDINARY CONFIGURATION ---
# Only configure Cloudinary if credentials are available
cloudinary_cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME")
cloudinary_api_key = os.environ.get("CLOUDINARY_API_KEY")
cloudinary_api_secret = os.environ.get("CLOUDINARY_API_SECRET")

# Check if Cloudinary credentials are properly loaded
if cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret:
    # Strip any whitespace that might have been accidentally included
    cloudinary_cloud_name = cloudinary_cloud_name.strip()
    cloudinary_api_key = cloudinary_api_key.strip()
    cloudinary_api_secret = cloudinary_api_secret.strip()
    
    if cloudinary_cloud_name and cloudinary_api_key and cloudinary_api_secret:
        cloudinary.config(
            cloud_name=cloudinary_cloud_name,
            api_key=cloudinary_api_key,
            api_secret=cloudinary_api_secret
        )
        print("✓ Cloudinary configured successfully")
    else:
        print("⚠ Cloudinary credentials found but are empty after stripping whitespace")
else:
    print("⚠ Cloudinary credentials not found in environment variables")
    if not cloudinary_cloud_name:
        print("  - CLOUDINARY_CLOUD_NAME is missing")
    if not cloudinary_api_key:
        print("  - CLOUDINARY_API_KEY is missing")
    if not cloudinary_api_secret:
        print("  - CLOUDINARY_API_SECRET is missing")

# --- FIREBASE ADMIN CONFIGURATION ---
# Initialize Firebase admin SDK
firebase_config = {
    "apiKey": "AIzaSyCONFEQz0f0eNpZHt9AKfNjTrsSwG_8BY0",
    "authDomain": "stayfinder-cee38.firebaseapp.com",
    "projectId": "stayfinder-cee38",
    "storageBucket": "stayfinder-cee38.firebasestorage.app",
    "messagingSenderId": "404788657962",
    "appId": "1:404788657962:web:93facaca2fcf76ab1be853"
}

if not firebase_admin._apps:
    # Initialize Firebase Admin SDK with service account or default credentials
    try:
        # Try to initialize with default credentials first
        firebase_admin.initialize_app()
    except Exception as e:
        # If that fails, you'll need to set up service account credentials
        print(f"Firebase Admin initialization error: {e}")

# --- OAUTH CONFIGURATION ---
# Google OAuth   
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'stayfinder101@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'hobwbkgmkuqlgzhl')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'stayfinder101@gmail.com')

# Initialize Mail
mail = Mail(app)

# --- COLLEGE DATA ---
# Load colleges at startup
colleges = load_colleges()

@app.route('/api/hostels', methods=['GET'])
def api_get_hostels():
    """Get all hostels as JSON API"""
    try:
        # Get query parameters for filtering
        city = request.args.get('city', '')
        type_filter = request.args.get('type', '')
        min_price = float(request.args.get('min_price', 0))
        max_price = float(request.args.get('max_price', 10000))
        amenities = request.args.getlist('amenities')
        
        # Build query
        query = {}
        if city:
            query['city'] = city
        if type_filter:
            query['type'] = type_filter
        query['price'] = {'$gte': min_price, '$lte': max_price}
        if amenities:
            query['amenities'] = {'$all': amenities}
        
        hostels = list(mongo.db.hostels.find(query))
        serialized_hostels = [serialize_doc(hostel) for hostel in hostels]
        
        return jsonify({
            'success': True,
            'data': serialized_hostels,
            'count': len(serialized_hostels)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/hostels/<hostel_id>', methods=['GET'])
def api_get_hostel(hostel_id):
    """Get specific hostel by ID as JSON API"""
    try:
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if hostel:
            return jsonify({
                'success': True,
                'data': serialize_doc(hostel)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/hostels/search', methods=['POST'])
def api_search_hostels():
    """Search hostels as JSON API with enhanced filtering"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        property_type = data.get('property_type', 'all')
        
        # Build search query
        search_conditions = []
        
        # Text search across multiple fields
        if query and query.strip():
            # Use exact match and prefix matching for better precision
            query_clean = query.strip()
            
            # For very short queries (2-3 chars), use exact matching only
            if len(query_clean) <= 1:
                # Only match exact names for single character queries
                search_conditions.extend([
                    {"name": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"city": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"location": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}}
                ])
            elif len(query_clean) <= 2:
                # For 2-char queries, only allow exact matching to prevent false positives
                search_conditions.extend([
                    {"name": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"city": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"location": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}}
                ])
            elif len(query_clean) <= 3:
                # For 3-char queries, allow exact match, word boundary, and prefix matching
                word_boundary_pattern = r'\b' + re.escape(query_clean) + r'\b'
                search_conditions.extend([
                    {"name": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"city": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"location": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
                    {"name": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"city": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"location": {"$regex": word_boundary_pattern, "$options": "i"}},
                    # Allow prefix matching for 3-char queries
                    {"name": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}},
                    {"city": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}},
                    {"location": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}}
                ])
            else:
                # For longer queries, allow word boundary matching
                word_boundary_pattern = r'\b' + re.escape(query_clean) + r'\b'
                start_boundary_pattern = r'\b' + re.escape(query_clean)
                
                search_conditions.extend([
                    {"name": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"city": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"location": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"desc": {"$regex": word_boundary_pattern, "$options": "i"}},
                    {"address": {"$regex": word_boundary_pattern, "$options": "i"}},
                    # Also allow prefix matching for better UX
                    {"name": {"$regex": start_boundary_pattern, "$options": "i"}},
                    {"city": {"$regex": start_boundary_pattern, "$options": "i"}},
                    {"location": {"$regex": start_boundary_pattern, "$options": "i"}}
                ])
        
        # Property type filtering
        if property_type and property_type != 'all':
            if property_type == 'hostel':
                search_conditions.append({"property_type": {"$regex": "hostel", "$options": "i"}})
            elif property_type == 'pg':
                search_conditions.append({"property_type": {"$regex": "pg", "$options": "i"}})
            elif property_type == 'apartment':
                search_conditions.append({"property_type": {"$regex": "apartment", "$options": "i"}})
        
        # Combine search conditions
        if search_conditions:
            if len(search_conditions) == 1:
                search_query = search_conditions[0]
            else:
                search_query = {"$or": search_conditions}
        else:
            search_query = {}
        
        hostels = list(mongo.db.hostels.find(search_query))
        serialized_hostels = [serialize_doc(hostel) for hostel in hostels]
        
        return jsonify({
            'success': True,
            'data': serialized_hostels,
            'count': len(serialized_hostels),
            'query': query,
            'property_type': property_type
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/colleges', methods=['GET'])
def api_get_colleges():
    """Get all colleges as JSON API"""
    try:
        return jsonify({
            'success': True,
            'data': colleges,
            'count': len(colleges)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/hostels/search/college', methods=['POST'])
def api_search_hostels_by_college():
    """Search hostels near a specific college"""
    try:
        data = request.get_json()
        college_name = data.get('college_name', '')
        max_distance = float(data.get('max_distance', 30))  # Default 30km radius
        property_type = data.get('property_type', 'all')
        
        if not college_name:
            return jsonify({
                'success': False,
                'message': 'College name is required'
            }), 400
        
        # Find college by name
        college = find_college_by_name(college_name, colleges)
        if not college:
            return jsonify({
                'success': False,
                'message': f'College "{college_name}" not found'
            }), 404
        
        # Get all hostels with coordinates
        hostels = list(mongo.db.hostels.find({
            'latitude': {'$exists': True},
            'longitude': {'$exists': True}
        }))
        
        # Filter hostels within distance and by property type
        nearby_hostels = []
        for hostel in hostels:
            if not hostel.get('latitude') or not hostel.get('longitude'):
                continue
                
            distance = calculate_distance(
                college['Latitude'], college['Longitude'],
                hostel['latitude'], hostel['longitude']
            )
            
            if distance <= max_distance:
                # Add distance to hostel data
                hostel['distance_from_college'] = round(distance, 2)
                
                # Filter by property type if specified
                if property_type and property_type != 'all':
                    if property_type == 'hostel' and not hostel.get('property_type', '').lower().startswith('hostel'):
                        continue
                    elif property_type == 'pg' and not hostel.get('property_type', '').lower().startswith('pg'):
                        continue
                    elif property_type == 'apartment' and not hostel.get('property_type', '').lower().startswith('apartment'):
                        continue
                
                nearby_hostels.append(hostel)
        
        # Sort by distance
        nearby_hostels.sort(key=lambda x: x['distance_from_college'])
        
        serialized_hostels = [serialize_doc(hostel) for hostel in nearby_hostels]
        
        return jsonify({
            'success': True,
            'data': serialized_hostels,
            'count': len(serialized_hostels),
            'college': college,
            'max_distance': max_distance,
            'query': college_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def api_get_user_profile():
    """Get current user profile as JSON API"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if user:
            # Remove password from response
            user_data = serialize_doc(user)
            user_data.pop('password', None)
            
            return jsonify({
                'success': True,
                'data': user_data
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/user/bookings', methods=['GET'])
@jwt_required()
def api_get_user_bookings():
    """Get user bookings as JSON API"""
    try:
        current_user_id = get_jwt_identity()
        # This would integrate with a bookings collection
        # For now, return empty array
        return jsonify({
            'success': True,
            'data': [],
            'message': 'Bookings feature coming soon'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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
        
        # Get user information
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get hostel information
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
        
        # Create booking record
        booking = {
            'user_id': ObjectId(current_user_id),
            'hostel_id': ObjectId(hostel_id),
            'room_id': room_id,
            'property_type': property_type,
            'facility': facility,
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        # Save booking to database
        mongo.db.bookings.insert_one(booking)
        
        # Send confirmation emails to both user and owner
        user_email_sent = False
        owner_email_sent = False
        email_error_message = None
        
        try:
            # Debug email configuration
            print(f"=== EMAIL DEBUG ===")
            print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
            print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
            print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
            print(f"MAIL_PASSWORD configured: {'Yes' if app.config.get('MAIL_PASSWORD') else 'No'}")
            print(f"User Email: {user['email']}")
            print(f"==================")
            
            # 1. Email to user with HTML template
            user_subject = f"Booking Request Confirmed - {hostel['name']}"
            user_msg = Message(
                user_subject,
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user['email']]
            )
            user_msg.html = render_template('emails/booking_request_user.html', 
                                          user=user, 
                                          hostel=hostel, 
                                          property_type=property_type, 
                                          facility=facility,
                                          now=datetime.utcnow())
            mail.send(user_msg)
            user_email_sent = True
            print(f"[+] User confirmation email sent to: {user['email']}")
            
            # 2. Email to owner with booking request notification
            # Get owner information
            owner_id = hostel.get('owner_id') or hostel.get('created_by')
            if owner_id:
                try:
                    owner = mongo.db.users.find_one({"_id": ObjectId(owner_id)})
                    if owner and owner.get('email'):
                        owner_subject = f"New Booking Request - {hostel['name']} from {user.get('name', user['email'])}"
                        owner_msg = Message(
                            owner_subject,
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[owner['email']]
                        )
                        owner_msg.html = render_template('emails/booking_request_to_owner.html',
                                                        user=user,
                                                        owner=owner,
                                                        hostel=hostel,
                                                        property_type=property_type,
                                                        facility=facility,
                                                        request_time=datetime.utcnow(),
                                                        dashboard_link=None)
                        mail.send(owner_msg)
                        owner_email_sent = True
                        print(f"[+] Owner notification email sent to: {owner['email']}")
                    else:
                        print(f"[!] Owner email not found for hostel {hostel_id}")
                except Exception as owner_error:
                    print(f"[!] Owner email sending failed: {owner_error}")
                    # Continue without failing - owner email is optional
            else:
                print(f"[!] Owner ID not found for hostel {hostel_id}")
                
        except Exception as email_error:
            email_error_message = str(email_error)
            print(f"[-] Email sending failed: {email_error}")
            import traceback
            traceback.print_exc()
            # Still return success even if email fails
        
        # Build response message
        response_message = 'Booking request submitted successfully!'
        if user_email_sent:
            response_message += ' Confirmation email has been sent to your email address.'
        if owner_email_sent:
            response_message += ' The property owner has been notified and will respond soon.'
        if not user_email_sent and not owner_email_sent:
            response_message += ' (Email notifications could not be sent, but your booking is confirmed.)'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'booking_id': str(booking['_id']) if '_id' in booking else None,
            'user_email_sent': user_email_sent,
            'owner_email_sent': owner_email_sent,
            'email_error': email_error_message if (not user_email_sent or not owner_email_sent) else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/bookings/<booking_id>/confirm', methods=['POST'])
def api_confirm_booking(booking_id):
    """Confirm a booking (owner only) - marks as completed for user dashboard"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'}), 401
    
    try:
        # Get the booking
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Verify owner owns this property
        property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Get owner (logged in user)
        owner = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        
        # Get user who made the booking
        booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
        
        # Update booking status to completed (for user's dashboard)
        mongo.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {
                'status': 'completed', 
                'confirmed_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
        
        # Send confirmation email to user if email is enabled
        try:
            if app.config.get('MAIL_DEFAULT_SENDER') and booking_user and booking_user.get('email'):
                subject = f"Booking Accepted - {property.get('name', 'Your Property')}"
                msg = Message(
                    subject,
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[booking_user['email']]
                )
                msg.html = render_template('emails/booking_acceptance_user.html',
                    user=booking_user,
                    hostel=property,
                    owner=owner,
                    booking=booking
                )
                mail.send(msg)
                print(f"[+] Booking acceptance email sent to: {booking_user['email']}")
        except Exception as email_error:
            print(f"[!] Booking acceptance email sending failed: {email_error}")
        
        return jsonify({'success': True, 'message': 'Booking confirmed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/bookings/<booking_id>/reject', methods=['POST'])
def api_reject_booking(booking_id):
    """Reject a booking (owner only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'}), 401
    
    try:
        # Get the booking
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        
        # Verify owner owns this property
        property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update booking status
        mongo.db.bookings.update_one(
            {'_id': ObjectId(booking_id)},
            {'$set': {'status': 'rejected', 'rejected_at': datetime.utcnow()}}
        )
        
        return jsonify({'success': True, 'message': 'Booking rejected'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/enquiries/<enquiry_id>/accept', methods=['POST'])
def api_accept_enquiry(enquiry_id):
    """Accept an enquiry (owner only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'}), 401
    
    try:
        # Get the enquiry
        enquiry = mongo.db.enquiries.find_one({'_id': ObjectId(enquiry_id)})
        if not enquiry:
            return jsonify({'success': False, 'message': 'Enquiry not found'}), 404
        
        # Verify owner owns this property
        property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update enquiry status
        mongo.db.enquiries.update_one(
            {'_id': ObjectId(enquiry_id)},
            {'$set': {
                'status': 'approved', 
                'responded_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
        
        return jsonify({'success': True, 'message': 'Enquiry accepted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/enquiries/<enquiry_id>/reject', methods=['POST'])
def api_reject_enquiry(enquiry_id):
    """Reject an enquiry (owner only)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'}), 401
    
    try:
        # Get the enquiry
        enquiry = mongo.db.enquiries.find_one({'_id': ObjectId(enquiry_id)})
        if not enquiry:
            return jsonify({'success': False, 'message': 'Enquiry not found'}), 404
        
        # Verify owner owns this property
        property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
        if not property or property.get('created_by') != session['user_id']:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update enquiry status
        mongo.db.enquiries.update_one(
            {'_id': ObjectId(enquiry_id)},
            {'$set': {
                'status': 'rejected', 
                'rejected_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }}
        )
        
        return jsonify({'success': True, 'message': 'Enquiry rejected'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/hostels/<hostel_id>', methods=['PUT'])
@jwt_required()
def api_update_hostel(hostel_id):
    """Update hostel as JSON API"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if hostel exists and user has permission
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
        
        # Check if user created this hostel or is admin
        if hostel.get('created_by') != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        # Update hostel
        update_data = {k: v for k, v in data.items() if k != '_id'}
        update_data['updated_at'] = datetime.utcnow()
        
        mongo.db.hostels.update_one(
            {"_id": ObjectId(hostel_id)},
            {"$set": update_data}
        )
        
        updated_hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        
        return jsonify({
            'success': True,
            'data': serialize_doc(updated_hostel),
            'message': 'Hostel updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/hostels/<hostel_id>', methods=['DELETE'])
@jwt_required()
def api_delete_hostel(hostel_id):
    """Delete hostel as JSON API"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if hostel exists and user has permission
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
        
        # Check if user created this hostel or is admin
        if hostel.get('created_by') != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Permission denied'
            }), 403
        
        mongo.db.hostels.delete_one({"_id": ObjectId(hostel_id)})
        
        return jsonify({
            'success': True,
            'message': 'Hostel deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def api_verify_token():
    """Verify JWT token"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if user:
            user_data = serialize_doc(user)
            user_data.pop('password', None)
            
            return jsonify({
                'success': True,
                'data': user_data,
                'message': 'Token is valid'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# --- ADMIN API ROUTES ---

@app.route('/api/admin/properties/<hostel_id>/approve', methods=['POST'])
@jwt_required()
def api_admin_approve_property(hostel_id):
    """Approve a property (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if not user or not user.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Access denied. Admin account required.'
            }), 403
        
        # Update property status to active
        result = mongo.db.hostels.update_one(
            {"_id": ObjectId(hostel_id)},
            {"$set": {"status": "active", "approved_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Property approved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/properties/<hostel_id>/deactivate', methods=['POST'])
@jwt_required()
def api_admin_deactivate_property(hostel_id):
    """Deactivate a property (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if not user or not user.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Access denied. Admin account required.'
            }), 403
        
        # Update property status to inactive
        result = mongo.db.hostels.update_one(
            {"_id": ObjectId(hostel_id)},
            {"$set": {"status": "inactive"}}
        )
        
        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Property deactivated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/properties/<hostel_id>/edit', methods=['PUT'])
@jwt_required()
def api_admin_edit_property(hostel_id):
    """Edit a property (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if not user or not user.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Access denied. Admin account required.'
            }), 403
        
        data = request.get_json()
        
        # Check if property exists
        property = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not property:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        # Prepare update data
        update_data = {
            'name': data.get('name', property.get('name')),
            'property_type': data.get('property_type', property.get('property_type')),
            'city': data.get('city', property.get('city')),
            'location': data.get('location', property.get('location')),
            'price': data.get('price', property.get('price')),
            'status': data.get('status', property.get('status')),
            'address': data.get('address', property.get('address')),
            'contact_email': data.get('contact_email', property.get('contact_email')),
            'contact_phone': data.get('contact_phone', property.get('contact_phone')),
            'description': data.get('description', property.get('description')),
            'updated_at': datetime.utcnow(),
            'updated_by': str(user['_id'])
        }
        
        # Update image only if provided
        if data.get('image') and data.get('image').strip():
            update_data['image'] = data['image']
        
        # Update the property
        result = mongo.db.hostels.update_one(
            {"_id": ObjectId(hostel_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        # Get updated property
        updated_property = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        
        return jsonify({
            'success': True,
            'message': 'Property updated successfully',
            'data': serialize_doc(updated_property)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/admin/properties/<hostel_id>', methods=['DELETE'])
@jwt_required()
def api_admin_delete_property(hostel_id):
    """Delete a property (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        
        if not user or not user.get('is_admin', False):
            return jsonify({
                'success': False,
                'message': 'Access denied. Admin account required.'
            }), 403
        
        # Delete the property
        result = mongo.db.hostels.delete_one({"_id": ObjectId(hostel_id)})
        
        if result.deleted_count == 0:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Property deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# --- ROUTES ---

# Debug route to check JWT configuration
@app.route('/debug/jwt')
def debug_jwt():
    """Debug route to check JWT configuration"""
    return jsonify({
        "jwt_access_token_expires": str(app.config.get('JWT_ACCESS_TOKEN_EXPIRES')),
        "jwt_expires_hours": app.config.get('JWT_ACCESS_TOKEN_EXPIRES').total_seconds() / 3600 if app.config.get('JWT_ACCESS_TOKEN_EXPIRES') else None,
        "note": "JWT tokens should now expire after 24 hours"
    })

# Debug route to check email configuration
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

# Debug route to check Cloudinary configuration (remove in production)
@app.route('/debug/cloudinary')
def debug_cloudinary():
    """Debug route to check if Cloudinary credentials are loaded"""
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    api_key = os.environ.get("CLOUDINARY_API_KEY", "")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")
    
    return jsonify({
        "cloud_name_present": bool(cloud_name),
        "cloud_name_length": len(cloud_name) if cloud_name else 0,
        "api_key_present": bool(api_key),
        "api_key_length": len(api_key) if api_key else 0,
        "api_secret_present": bool(api_secret),
        "api_secret_length": len(api_secret) if api_secret else 0,
        "all_configured": bool(cloud_name and api_key and api_secret),
        "note": "Visit this URL to check if your .env file is being read correctly"
    })

# Context processor to make user data available in all templates
@app.context_processor
def inject_user():
    """Make user data available in all templates"""
    user = None
    if 'user_id' in session and mongo.db is not None:
        user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
        # Convert ObjectId to string for template usage
        if user:
            user['_id'] = str(user['_id'])
    
    return dict(user=user)

@app.route('/')
def home():
    # Get all hostels from the database
    if mongo.db is not None:
        hostels = list(mongo.db.hostels.find())
    else:
        hostels = []  # Empty list when database is not available
    return render_template('index.html', hostels=hostels)

@app.route('/search-by-college')
def search_by_college():
    """Render college search page"""
    return render_template('college_search.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    # Simple search by City (case insensitive)
    if mongo.db is not None:
        hostels = list(mongo.db.hostels.find({"city": {"$regex": query, "$options": "i"}}))
    else:
        hostels = []  # Empty list when database is not available
    return render_template('index.html', hostels=hostels)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/contact/send-email', methods=['POST'])
def send_contact_email():
    """Handle contact form email submission"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        topic = request.form.get('topic', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validation
        if not all([name, email, message]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('contact'))
        
        # Validate email format
        if '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('contact'))
        
        # Send email to admin
        try:
            admin_msg = Message(
                f"New Contact Form Submission - {topic}",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=['stayfinder101@gmail.com']
            )
            admin_msg.body = f"""
New Contact Form Submission:

Name: {name}
Email: {email}
Phone: {phone}
Topic: {topic}

Message:
{message}

---
Please reply to {email} directly or use the dashboard to manage this inquiry.
"""
            mail.send(admin_msg)
            
            # Send confirmation email to user
            user_msg = Message(
                "We received your message - StayFinder",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            user_msg.body = f"""
Dear {name},

Thank you for reaching out to StayFinder!

We have received your message and will get back to you within 24 hours.

Your Message Details:
Topic: {topic}
Submitted: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
StayFinder Team
"""
            mail.send(user_msg)
            
            flash('Thank you! Your message has been sent successfully. We will respond within 24 hours.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as email_error:
            print(f"Failed to send contact email: {email_error}")
            flash('Your message was not sent. Please try again later.', 'error')
            return redirect(url_for('contact'))
        
    except Exception as e:
        print(f"Error submitting contact form: {e}")
        flash('An error occurred while processing your request. Please try again.', 'error')
        return redirect(url_for('contact'))

@app.route('/help-center')
def help_center():
    return render_template('helpcenter.html')

@app.route('/support')
def support():
    """Support page with FAQs, ticket submission, and contact options"""
    return render_template('support.html')

@app.route('/support/submit-ticket', methods=['POST'])
def submit_support_ticket():
    """Handle support ticket submission"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        category = request.form.get('category', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        booking_id = request.form.get('booking_id', '').strip()
        
        # Validation
        if not all([name, email, category, subject, message]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('support'))
        
        # Create ticket
        ticket = {
            'name': name,
            'email': email,
            'phone': phone,
            'category': category,
            'subject': subject,
            'message': message,
            'booking_id': booking_id,
            'status': 'open',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'user_id': session.get('user_id'),
            'ticket_id': f"TKT{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Save to database
        mongo.db.support_tickets.insert_one(ticket)
        
        # Send confirmation email
        try:
            msg = Message(
                f"Support Ticket Received - {ticket['ticket_id']}",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            msg.body = f"""
Dear {name},

Thank you for contacting StayFinder Support. We have received your ticket.

Ticket Details:
- Ticket ID: {ticket['ticket_id']}
- Category: {category}
- Subject: {subject}

Our support team will review your request and respond within 24 hours.

If you have any urgent concerns, please call us at +91 1800-123-456.

Best regards,
StayFinder Support Team
"""
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")
        
        flash(f"Your support ticket ({ticket['ticket_id']}) has been submitted successfully! We'll respond within 24 hours.", 'success')
        return redirect(url_for('support'))
        
    except Exception as e:
        print(f"Error submitting support ticket: {e}")
        flash('An error occurred while submitting your ticket. Please try again.', 'error')
        return redirect(url_for('support'))

@app.route('/safety')
def safety():
    return render_template('safety.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/cancellation')
def cancellation():
    return render_template('cancellation.html')

@app.route('/debug/session')
def debug_session():
    """Debug route to check session status"""
    return jsonify({
        "session_keys": list(session.keys()),
        "has_user_id": 'user_id' in session,
        "user_id_value": session.get('user_id'),
        "session_data": dict(session)
    })

@app.route('/hostel/<hostel_id>')
def detail(hostel_id):
    # Find specific hostel by ID
    if mongo.db is not None:
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
    else:
        hostel = None  # No hostel when database is not available
    
    # Prepare all_photos for the template
    all_photos = []
    if hostel:
        print(f"DEBUG: Hostel found: {hostel.get('name', 'N/A')}")
        print(f"DEBUG: Hostel photos length: {len(hostel.get('photos', []))}")
        print(f"DEBUG: Hostel image: {hostel.get('image', 'None')[:50] if hostel.get('image') else 'None'}")
        
        if hostel.get('photos') and len(hostel.get('photos', [])) > 0:
            all_photos = hostel['photos']
            print(f"DEBUG: Using photos array: {len(all_photos)} items")
        elif hostel.get('image') and hostel.get('image', '').strip():
            all_photos = [hostel['image']]
            print(f"DEBUG: Using main image: {len(all_photos)} items")
        else:
            print("DEBUG: No photos found")
            all_photos = []
    else:
        print("DEBUG: No hostel found")
        all_photos = []
    
    print(f"DEBUG: Final all_photos length: {len(all_photos)}")
    if all_photos:
        print(f"DEBUG: First photo: {all_photos[0][:50]}")
    
    return render_template('detail.html', hostel=hostel, all_photos=all_photos)

@app.route('/add', methods=['GET', 'POST'])
def add_hostel():
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to list your property', 'error')
        return redirect(url_for('login'))
    # Check if user is an owner
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Only registered owners can list properties. Please register as an owner first.', 'error')
        return redirect(url_for('register_owner'))
    
    # This page lets you add hostels to the database easily
    if request.method == 'POST':
        image_url = request.form.get("image") or None  # Fallback to URL if provided
        photo_urls = []
        
        # Handle multiple photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            uploaded_count = 0
            
            for photo in photos:
                if photo and photo.filename != '':
                    try:
                        # Check if Cloudinary is configured
                        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
                        api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
                        api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
                        
                        if cloud_name and api_key and api_secret:
                            # Ensure Cloudinary is configured with current values
                            cloudinary.config(
                                cloud_name=cloud_name,
                                api_key=api_key,
                                api_secret=api_secret
                            )
                            
                            # Upload to Cloudinary
                            upload_result = cloudinary.uploader.upload(
                                photo,
                                folder="stayfinder/hostels",
                                resource_type="image"
                            )
                            photo_url = upload_result.get('secure_url')
                            if photo_url:
                                photo_urls.append(photo_url)
                                uploaded_count += 1
                        else:
                            # If Cloudinary not configured, skip file upload
                            missing = []
                            if not cloud_name:
                                missing.append("CLOUDINARY_CLOUD_NAME")
                            if not api_key:
                                missing.append("CLOUDINARY_API_KEY")
                            if not api_secret:
                                missing.append("CLOUDINARY_API_SECRET")
                            return jsonify({
                                'success': False,
                                'message': f'Cloudinary credentials missing: {", ".join(missing)}. Photos not uploaded.'
                            }), 500
                    except Exception as e:
                        print(f"Error uploading photo: {e}")
                        continue
            
            if uploaded_count > 0:
                # Photos uploaded successfully, continue processing
                # Set the first photo as the main image if no image_url provided
                if not image_url and photo_urls:
                    image_url = photo_urls[0]
        
        # Ensure we have an image URL - use placeholder if none provided
        if not image_url or image_url.strip() == '':
            # Default placeholder image
            image_url = "https://via.placeholder.com/400x300?text=No+Image"
        
        # Get amenities from form (can be multiple)
        amenities = request.form.getlist("amenities")
        # If no amenities selected, use default ones
        if not amenities:
            amenities = ["WiFi", "Fully Furnished", "AC", "TV", "Laundry"]
        
        # Get original_price (optional)
        original_price = request.form.get("original_price")
        if original_price and original_price.strip():
            original_price = int(original_price)
        else:
            original_price = None
        
        # Get appliances from form (can be multiple)
        appliances = request.form.getlist("appliances")
        
        # Get room types and pricing from new form structure
        room_types = []
        
        # Double Sharing - Regular
        double_regular_price = request.form.get("double_sharing_regular_price")
        has_double_regular = request.form.get("has_double_regular")
        if has_double_regular and double_regular_price:
            room_types.append({
                "type": "Double Sharing",
                "facility": "Regular",
                "price": int(double_regular_price)
            })
        
        # Double Sharing - AC
        double_ac_price = request.form.get("double_sharing_ac_price")
        has_double_ac = request.form.get("has_double_ac")
        if has_double_ac and double_ac_price:
            room_types.append({
                "type": "Double Sharing",
                "facility": "AC",
                "price": int(double_ac_price)
            })
        
        # Triple Sharing - Regular
        triple_regular_price = request.form.get("triple_sharing_regular_price")
        has_triple_regular = request.form.get("has_triple_regular")
        if has_triple_regular and triple_regular_price:
            room_types.append({
                "type": "Triple Sharing",
                "facility": "Regular",
                "price": int(triple_regular_price)
            })
        
        # Triple Sharing - AC
        triple_ac_price = request.form.get("triple_sharing_ac_price")
        has_triple_ac = request.form.get("has_triple_ac")
        if has_triple_ac and triple_ac_price:
            room_types.append({
                "type": "Triple Sharing",
                "facility": "AC",
                "price": int(triple_ac_price)
            })
        
        # Quadruple Sharing - Regular
        quadruple_regular_price = request.form.get("quadruple_sharing_regular_price")
        has_quadruple_regular = request.form.get("has_quadruple_regular")
        if has_quadruple_regular and quadruple_regular_price:
            room_types.append({
                "type": "Quadruple Sharing",
                "facility": "Regular",
                "price": int(quadruple_regular_price)
            })
        
        # Quadruple Sharing - AC
        quadruple_ac_price = request.form.get("quadruple_sharing_ac_price")
        has_quadruple_ac = request.form.get("has_quadruple_ac")
        if has_quadruple_ac and quadruple_ac_price:
            room_types.append({
                "type": "Quadruple Sharing",
                "facility": "AC",
                "price": int(quadruple_ac_price)
            })
        
        # Also store the individual pricing fields for direct access in templates
        pricing_data = {
            "has_double_regular": bool(has_double_regular),
            "double_sharing_regular_price": int(double_regular_price) if double_regular_price else None,
            "has_double_ac": bool(has_double_ac),
            "double_sharing_ac_price": int(double_ac_price) if double_ac_price else None,
            "has_triple_regular": bool(has_triple_regular),
            "triple_sharing_regular_price": int(triple_regular_price) if triple_regular_price else None,
            "has_triple_ac": bool(has_triple_ac),
            "triple_sharing_ac_price": int(triple_ac_price) if triple_ac_price else None,
            "has_quadruple_regular": bool(has_quadruple_regular),
            "quadruple_sharing_regular_price": int(quadruple_regular_price) if quadruple_regular_price else None,
            "has_quadruple_ac": bool(has_quadruple_ac),
            "quadruple_sharing_ac_price": int(quadruple_ac_price) if quadruple_ac_price else None
        }
        
        # Get neighborhood highlights
        neighborhood_highlights = []
        for i in range(1, 6):  # Support up to 5 nearby places
            place_name = request.form.get(f"nearby_place_{i}")
            place_distance = request.form.get(f"nearby_distance_{i}")
            place_time = request.form.get(f"nearby_time_{i}")
            
            if place_name and place_distance and place_time:
                neighborhood_highlights.append({
                    "name": place_name,
                    "distance": place_distance,
                    "time": place_time
                })
        
        new_hostel = {
            "name": request.form.get("name"),
            "city": request.form.get("city"),
            "location": request.form.get("location", "").strip(),  # Area/locality
            "price": int(request.form.get("price")),
            "original_price": original_price,
            "image": image_url,  # Cloudinary URL or provided URL
            "photos": photo_urls,  # Multiple photo URLs
            "desc": request.form.get("desc"),
            "type": request.form.get("type"),  # e.g., Boys, Girls, Co-ed
            "amenities": amenities,
            "appliances": appliances,
            "room_types": room_types,
            "longitude": float(request.form.get("longitude", 0.0)),
            "latitude": float(request.form.get("latitude", 0.0)),
            "neighborhood_highlights": neighborhood_highlights,
            "contact_phone": request.form.get("contact_phone", ""),
            "contact_email": request.form.get("contact_email", ""),
            "address": request.form.get("address", ""),
            "property_type": request.form.get("property_type", "Hostel"),  # Hostel or PG
            "created_by": session['user_id'],  # Associate with the owner
            "status": "pending",  # pending, active, inactive
            "created_at": datetime.utcnow()
        }
        
        # Add individual pricing fields to the hostel document
        new_hostel.update(pricing_data)
        mongo.db.hostels.insert_one(new_hostel)
        
        # Update owner's properties count
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$inc': {'properties_count': 1}}
        )
        
        flash('Property listed successfully! It will be visible after verification.', 'success')
        return redirect(url_for('owner_dashboard'))
    return render_template('add.html')

@app.route('/edit-property/<property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    """Edit an existing property (owner only)"""
    if 'user_id' not in session:
        flash('Please login to edit your property', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get the property
    property = mongo.db.hostels.find_one({'_id': ObjectId(property_id)})
    if not property:
        flash('Property not found', 'error')
        return redirect(url_for('owner_dashboard'))
    
    # Verify ownership
    if property.get('created_by') != session['user_id']:
        flash('You can only edit your own properties', 'error')
        return redirect(url_for('owner_dashboard'))
    
    if request.method == 'POST':
        image_url = request.form.get("image") or property.get('image')
        photo_urls = property.get('photos', [])
        
        # Handle multiple photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            new_photos = []
            
            for photo in photos:
                if photo and photo.filename != '':
                    try:
                        cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
                        api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
                        api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
                        
                        if cloud_name and api_key and api_secret:
                            cloudinary.config(
                                cloud_name=cloud_name,
                                api_key=api_key,
                                api_secret=api_secret
                            )
                            
                            upload_result = cloudinary.uploader.upload(
                                photo,
                                folder="stayfinder/hostels",
                                resource_type="image"
                            )
                            photo_url = upload_result.get('secure_url')
                            if photo_url:
                                new_photos.append(photo_url)
                    except Exception as e:
                        print(f"Error uploading photo: {e}")
                        continue
            
            if new_photos:
                photo_urls = new_photos
                if not request.form.get("image"):
                    image_url = new_photos[0]
        
        # Get amenities from form
        amenities = request.form.getlist("amenities")
        if not amenities:
            amenities = property.get('amenities', [])
        
        # Get original_price
        original_price = request.form.get("original_price")
        if original_price and original_price.strip():
            original_price = int(original_price)
        else:
            original_price = property.get('original_price')
        
        # Get appliances from form
        appliances = request.form.getlist("appliances")
        if not appliances:
            appliances = property.get('appliances', [])
        
        # Get room types and pricing
        room_types = []
        
        double_regular_price = request.form.get("double_sharing_regular_price")
        has_double_regular = request.form.get("has_double_regular")
        if has_double_regular and double_regular_price:
            room_types.append({
                "type": "Double Sharing",
                "facility": "Regular",
                "price": int(double_regular_price)
            })
        
        double_ac_price = request.form.get("double_sharing_ac_price")
        has_double_ac = request.form.get("has_double_ac")
        if has_double_ac and double_ac_price:
            room_types.append({
                "type": "Double Sharing",
                "facility": "AC",
                "price": int(double_ac_price)
            })
        
        triple_regular_price = request.form.get("triple_sharing_regular_price")
        has_triple_regular = request.form.get("has_triple_regular")
        if has_triple_regular and triple_regular_price:
            room_types.append({
                "type": "Triple Sharing",
                "facility": "Regular",
                "price": int(triple_regular_price)
            })
        
        triple_ac_price = request.form.get("triple_sharing_ac_price")
        has_triple_ac = request.form.get("has_triple_ac")
        if has_triple_ac and triple_ac_price:
            room_types.append({
                "type": "Triple Sharing",
                "facility": "AC",
                "price": int(triple_ac_price)
            })
        
        quadruple_regular_price = request.form.get("quadruple_sharing_regular_price")
        has_quadruple_regular = request.form.get("has_quadruple_regular")
        if has_quadruple_regular and quadruple_regular_price:
            room_types.append({
                "type": "Quadruple Sharing",
                "facility": "Regular",
                "price": int(quadruple_regular_price)
            })
        
        quadruple_ac_price = request.form.get("quadruple_sharing_ac_price")
        has_quadruple_ac = request.form.get("has_quadruple_ac")
        if has_quadruple_ac and quadruple_ac_price:
            room_types.append({
                "type": "Quadruple Sharing",
                "facility": "AC",
                "price": int(quadruple_ac_price)
            })
        
        pricing_data = {
            "has_double_regular": bool(has_double_regular),
            "double_sharing_regular_price": int(double_regular_price) if double_regular_price else None,
            "has_double_ac": bool(has_double_ac),
            "double_sharing_ac_price": int(double_ac_price) if double_ac_price else None,
            "has_triple_regular": bool(has_triple_regular),
            "triple_sharing_regular_price": int(triple_regular_price) if triple_regular_price else None,
            "has_triple_ac": bool(has_triple_ac),
            "triple_sharing_ac_price": int(triple_ac_price) if triple_ac_price else None,
            "has_quadruple_regular": bool(has_quadruple_regular),
            "quadruple_sharing_regular_price": int(quadruple_regular_price) if quadruple_regular_price else None,
            "has_quadruple_ac": bool(has_quadruple_ac),
            "quadruple_sharing_ac_price": int(quadruple_ac_price) if quadruple_ac_price else None
        }
        
        # Build update data
        update_data = {
            "name": request.form.get("name"),
            "city": request.form.get("city"),
            "location": request.form.get("location", "").strip(),
            "price": int(request.form.get("price")),
            "original_price": original_price,
            "image": image_url,
            "photos": photo_urls,
            "desc": request.form.get("desc"),
            "type": request.form.get("type"),
            "amenities": amenities,
            "appliances": appliances,
            "room_types": room_types,
            "contact_phone": request.form.get("contact_phone", ""),
            "contact_email": request.form.get("contact_email", ""),
            "address": request.form.get("address", ""),
            "property_type": request.form.get("property_type", "Hostel"),
            "status": request.form.get("status", property.get('status', 'pending')),
            "updated_at": datetime.utcnow()
        }
        
        # Handle coordinates
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        if latitude:
            update_data["latitude"] = float(latitude)
        if longitude:
            update_data["longitude"] = float(longitude)
        
        update_data.update(pricing_data)
        
        mongo.db.hostels.update_one(
            {'_id': ObjectId(property_id)},
            {'$set': update_data}
        )
        
        flash('Property updated successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    
    return render_template('edit_property.html', property=property)

@app.route('/get-token')
def get_token():
    """Transfer JWT token from session to client"""
    if 'access_token' in session:
        return jsonify({
            'access_token': session['access_token']
        })
    else:
        return jsonify({'error': 'No token found'}), 401

@app.route('/login-student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        # Check if request is JSON or form data
        is_json_request = request.is_json or request.headers.get('Content-Type', '').startswith('application/json')
        
        if is_json_request:
            data = request.get_json()
            email = data.get('email') if data else None
            password = data.get('password') if data else None
        else:
            email = request.form.get('email')
            password = request.form.get('password')
        
        if not email or not password:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            flash('Email and password are required', 'error')
            return render_template('login_student.html')
        
        # Find user in database
        user = mongo.db.users.find_one({'email': email})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Check if user is a student (not owner)
            if user.get('user_type') == 'owner':
                if is_json_request:
                    return jsonify({'success': False, 'message': 'This is an owner account. Please use Owner Login.'}), 400
                flash('This is an owner account. Please use Owner Login.', 'error')
                return render_template('login_student.html')
            
            # Create JWT token
            access_token = create_access_token(identity=str(user['_id']))
            session['user_id'] = str(user['_id'])
            session['access_token'] = access_token
            session['user_type'] = user.get('user_type', 'user')
            
            # Update login stats
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {'last_login': datetime.utcnow()},
                    '$inc': {'login_count': 1}
                }
            )
            
            flash('Login successful!', 'success')
            
            # Check if this is an AJAX/JSON request
            if is_json_request:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': url_for('home'),
                    'access_token': access_token
                })
            else:
                # Regular form submission - store token in session and redirect
                return redirect(url_for('home'))
        else:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            flash('Invalid email or password', 'error')
    
    return render_template('login_student.html')

@app.route('/login-owner', methods=['GET', 'POST'])
def login_owner():
    if request.method == 'POST':
        # Check if request is JSON or form data
        is_json_request = request.is_json or request.headers.get('Content-Type', '').startswith('application/json')
        
        if is_json_request:
            data = request.get_json()
            email = data.get('email') if data else None
            password = data.get('password') if data else None
        else:
            email = request.form.get('email')
            password = request.form.get('password')
        
        if not email or not password:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            flash('Email and password are required', 'error')
            return render_template('login_owner.html')
        
        # Find user in database
        user = mongo.db.users.find_one({'email': email})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Check if user is an owner
            if user.get('user_type') != 'owner':
                if is_json_request:
                    return jsonify({'success': False, 'message': 'This is a student account. Please use Student Login.'}), 400
                flash('This is a student account. Please use Student Login.', 'error')
                return render_template('login_owner.html')
            
            # Create JWT token
            access_token = create_access_token(identity=str(user['_id']))
            session['user_id'] = str(user['_id'])
            session['access_token'] = access_token
            session['user_type'] = 'owner'
            
            # Update login stats
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {'last_login': datetime.utcnow()},
                    '$inc': {'login_count': 1}
                }
            )
            
            flash('Login successful!', 'success')
            
            if is_json_request:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': url_for('owner_dashboard'),
                    'access_token': access_token
                })
            return redirect(url_for('owner_dashboard'))
        else:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            flash('Invalid email or password', 'error')
    
    return render_template('login_owner.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Check if request is JSON or form data
        is_json_request = request.is_json or request.headers.get('Content-Type', '').startswith('application/json')
        
        if is_json_request:
            data = request.get_json()
            email = data.get('email') if data else None
            password = data.get('password') if data else None
        else:
            email = request.form.get('email')
            password = request.form.get('password')
        
        if not email or not password:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Email and password are required'}), 400
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        # Find user in database
        user = mongo.db.users.find_one({'email': email})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Create JWT token
            access_token = create_access_token(identity=str(user['_id']))
            session['user_id'] = str(user['_id'])
            session['access_token'] = access_token
            session['user_type'] = user.get('user_type', 'user')  # Store user type in session
            
            # Update login stats
            mongo.db.users.update_one(
                {'_id': user['_id']},
                {
                    '$set': {'last_login': datetime.utcnow()},
                    '$inc': {'login_count': 1}
                }
            )
            
            flash('Login successful!', 'success')
            
            # Redirect based on user type
            redirect_url = url_for('owner_dashboard') if user.get('user_type') == 'owner' else url_for('home')
            
            if is_json_request:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': redirect_url,
                    'access_token': access_token
                })
            return redirect(redirect_url)
        else:
            if is_json_request:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                            
        # Create new user
        new_user = {
            'name': name,
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'user_type': 'user',  # Explicitly set as regular user
            'created_at': datetime.utcnow(),
            'auth_method': 'email',
            'is_verified': False,
            'profile_completion': 50  # Basic profile completion
        }
        
        mongo.db.users.insert_one(new_user)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/register-owner', methods=['GET', 'POST'])
def register_owner():
    if request.method == 'POST':
        try:
            # Personal Information
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            
            # Business Information
            business_name = request.form.get('business_name', '').strip()
            business_type = request.form.get('business_type', '').strip()
            pan_number = request.form.get('pan_number', '').strip().upper()
            
            # Address Information
            address = request.form.get('address', '').strip()
            city = request.form.get('city', '').strip()
            state = request.form.get('state', '').strip()
            pincode = request.form.get('pincode', '').strip()
            
            # Password
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Terms acceptance
            terms_accepted = request.form.get('terms')
            
            # Validation
            errors = []
            
            # Required fields validation
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if not email:
                errors.append("Email is required")
            if not phone:
                errors.append("Phone number is required")
            if not business_name:
                errors.append("Business name is required")
            if not business_type:
                errors.append("Business type is required")
            if not pan_number:
                errors.append("PAN number is required")
            if not address:
                errors.append("Address is required")
            if not city:
                errors.append("City is required")
            if not state:
                errors.append("State is required")
            if not pincode:
                errors.append("PIN code is required")
            if not password:
                errors.append("Password is required")
            
            # Email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                errors.append("Invalid email format")
            
            # Phone number validation (10 digits)
            if not re.match(r'^[6-9]\d{9}$', phone.replace('-', '').replace(' ', '')):
                errors.append("Invalid phone number format")
            
            # PAN number validation
            if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan_number):
                errors.append("Invalid PAN number format")
            
            # PIN code validation (6 digits)
            if not re.match(r'^\d{6}$', pincode):
                errors.append("Invalid PIN code format")
            
            # Password validation
            if len(password) < 6:
                errors.append("Password must be at least 6 characters long")
            if password != confirm_password:
                errors.append("Passwords do not match")
            
            # Terms validation
            if not terms_accepted:
                errors.append("You must accept the terms and conditions")
            
            # If there are errors, return them to the user with form data
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('register_owner.html', 
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    business_name=business_name,
                    business_type=business_type,
                    pan_number=pan_number,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    terms_accepted=terms_accepted)
            
            # Check if user already exists
            existing_user = mongo.db.users.find_one({'email': email})
            if existing_user:
                flash('Email already registered. Please use a different email or login.', 'error')
                return render_template('register_owner.html', 
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    business_name=business_name,
                    business_type=business_type,
                    pan_number=pan_number,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    terms_accepted=terms_accepted)
            
            # Check if PAN number already exists
            existing_pan = mongo.db.users.find_one({'pan_number': pan_number})
            if existing_pan:
                flash('PAN number already registered. Please contact support if you think this is an error.', 'error')
                return render_template('register_owner.html', 
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    business_name=business_name,
                    business_type=business_type,
                    pan_number=pan_number,
                    address=address,
                    city=city,
                    state=state,
                    pincode=pincode,
                    terms_accepted=terms_accepted)
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create new owner user
            new_user = {
                'first_name': first_name,
                'last_name': last_name,
                'name': f"{first_name} {last_name}",
                'email': email,
                'phone': phone,
                'business_name': business_name,
                'business_type': business_type,
                'pan_number': pan_number,
                'address': address,
                'city': city,
                'state': state,
                'pincode': pincode,
                'password': hashed_password.decode('utf-8'),
                'user_type': 'owner',
                'created_at': datetime.utcnow(),
                'auth_method': 'email',
                'is_verified': False,
                'properties_count': 0,
                'account_status': 'pending',  # pending, active, suspended
                'verification_status': 'not_submitted',  # not_submitted, submitted, verified, rejected
                'profile_completion': 85,  # Basic profile completion percentage
                'last_login': None,
                'login_count': 0
            }
            
            # Insert user into database
            result = mongo.db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            
            # Create owner profile document for additional details
            owner_profile = {
                'user_id': ObjectId(user_id),
                'business_description': '',
                'website': '',
                'established_year': '',
                'total_properties': 0,
                'verified_properties': 0,
                'average_rating': 0.0,
                'total_reviews': 0,
                'response_rate': 0,
                'response_time': '',
                'bank_details': {
                    'account_holder': '',
                    'bank_name': '',
                    'account_number': '',
                    'ifsc_code': ''
                },
                'documents': {
                    'pan_card': '',
                    'address_proof': '',
                    'business_registration': '',
                    'id_proof': ''
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            mongo.db.owner_profiles.insert_one(owner_profile)
            
            # Send welcome email to owner
            try:
                welcome_subject = "Welcome to StayFinder - Your Owner Account is Ready!"
                welcome_msg = Message(
                    welcome_subject,
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                welcome_msg.body = f"""
Dear {first_name} {last_name},

Welcome to StayFinder! Your owner account has been successfully created.

Account Details:
- Name: {first_name} {last_name}
- Business Name: {business_name}
- Email: {email}
- Phone: {phone}

Next Steps:
1. Complete your profile by adding business details
2. Submit verification documents for faster approval
3. List your first property to start receiving bookings

Your account is currently in 'pending' status. You can:
- Add properties immediately (they will be visible after verification)
- Submit verification documents to get verified status
- Access your dashboard to manage properties

Login to your account: http://127.0.0.1:5000/login

Need help? Contact our support team at support@stayfinder.com

Best regards,
StayFinder Team
                """
                mail.send(welcome_msg)
                print(f"Welcome email sent to owner: {email}")
            except Exception as email_error:
                print(f"Failed to send welcome email: {email_error}")
            
            flash(f'Welcome {first_name}! Your owner account has been created successfully. Please login to continue.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Owner registration error: {e}")
            flash('An error occurred during registration. Please try again or contact support.', 'error')
            return render_template('register_owner.html')
    
    return render_template('register_owner.html')

# --- OAUTH ROUTES ---

@app.route('/auth/google')
def google_auth():
    redirect_uri = url_for('google_auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_auth_callback():
    try:
        token = google.authorize_access_token()
        # Get user info from Google
        user_info = google.parse_id_token(token)
        
        if not user_info:
            flash('Failed to get user information from Google', 'error')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = mongo.db.users.find_one({'email': user_info['email']})
        
        if not user:
            # Create new user from Google data
            new_user = {
                'name': user_info.get('name', ''),
                'email': user_info['email'],
                'password': '',  # No password for OAuth users
                'google_id': user_info.get('sub'),
                'profile_picture': user_info.get('picture', ''),
                'created_at': datetime.utcnow(),
                'auth_method': 'google'
            }
            mongo.db.users.insert_one(new_user)
            user = new_user
        
        # Create JWT token
        access_token = create_access_token(identity=str(user['_id']))
        session['user_id'] = str(user['_id'])
        session['access_token'] = access_token
        flash('Login successful with Google!', 'success')
        return redirect(url_for('home'))
        
    except Exception as e:
        flash(f'Google authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/auth/facebook')
def facebook_auth():
    redirect_uri = url_for('facebook_auth_callback', _external=True)
    return facebook.authorize_redirect(redirect_uri)

@app.route('/auth/facebook/callback')
def facebook_auth_callback():
    try:
        token = facebook.authorize_access_token()
        resp = facebook.get('me?fields=id,name,email,picture')
        user_info = resp.json()
        
        if not user_info or 'email' not in user_info:
            flash('Failed to get user information from Facebook', 'error')
            return redirect(url_for('login'))
        
        # Check if user exists
        user = mongo.db.users.find_one({'email': user_info['email']})
        
        if not user:
            # Create new user from Facebook data
            new_user = {
                'name': user_info.get('name', ''),
                'email': user_info['email'],
                'password': '',  # No password for OAuth users
                'facebook_id': user_info.get('id'),
                'profile_picture': user_info.get('picture', {}).get('data', {}).get('url', ''),
                'created_at': datetime.utcnow(),
                'auth_method': 'facebook'
            }
            mongo.db.users.insert_one(new_user)
            user = new_user
        
        # Create JWT token
        access_token = create_access_token(identity=str(user['_id']))
        session['user_id'] = str(user['_id'])
        session['access_token'] = access_token
        flash('Login successful with Facebook!', 'success')
        return redirect(url_for('home'))
        
    except Exception as e:
        flash(f'Facebook authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))

# --- FIREBASE GOOGLE OAUTH ROUTE ---

@app.route('/auth/firebase/google', methods=['POST'])
def firebase_google_auth():
    try:
        data = request.get_json()
        id_token = data.get('idToken')
        user_data = data.get('user', {})
        
        if not id_token:
            return jsonify({'success': False, 'message': 'No ID token provided'}), 400
        
        # Verify the Firebase ID token
        try:
            # For development, you might need to set up proper Firebase Admin credentials
            # For now, we'll skip verification and use the user data directly
            # In production, you should verify the token like this:
            # decoded_token = auth.verify_id_token(id_token)
            # uid = decoded_token['uid']
            
            # For development, use the user data from frontend
            uid = user_data.get('uid')
            email = user_data.get('email')
            name = user_data.get('displayName', '')
            photo_url = user_data.get('photoURL', '')
            email_verified = user_data.get('emailVerified', False)
            
            if not email:
                return jsonify({'success': False, 'message': 'Email is required'}), 400
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Token verification failed: {str(e)}'}), 400
        
        # Check if user exists in database
        user = mongo.db.users.find_one({'email': email})
        
        if not user:
            # Create new user from Firebase data
            new_user = {
                'name': name,
                'email': email,
                'password': '',  # No password for OAuth users
                'firebase_uid': uid,
                'profile_picture': photo_url,
                'email_verified': email_verified,
                'created_at': datetime.utcnow(),
                'auth_method': 'firebase_google'
            }
            
            result = mongo.db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
        else:
            user_id = str(user['_id'])
            # Update user info if needed
            mongo.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {
                    'firebase_uid': uid,
                    'profile_picture': photo_url,
                    'email_verified': email_verified,
                    'last_login': datetime.utcnow()
                }}
            )
        
        # Create JWT token
        access_token = create_access_token(identity=user_id)
        session['user_id'] = user_id
        session['access_token'] = access_token
        
        return jsonify({
            'success': True,
            'message': 'Firebase Google authentication successful',
            'redirect': url_for('home'),
            'access_token': access_token  # Include JWT token in response
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Authentication failed: {str(e)}'}), 500

# --- USER PROFILE ROUTES ---

@app.route('/owner-dashboard')
def owner_dashboard():
    if 'user_id' not in session:
        flash('Please login to access your dashboard', 'error')
        return redirect(url_for('login'))
    
    # Check if user is an owner
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get owner profile
    owner_profile = mongo.db.owner_profiles.find_one({'user_id': ObjectId(session['user_id'])})
    
    # Get owner's properties
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    # Get recent bookings for owner's properties with user details
    recent_bookings = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        bookings_cursor = mongo.db.bookings.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1).limit(3)
        
        for booking in bookings_cursor:
            # Get user details for this booking
            booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
            if booking_user:
                booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
                booking['user_email'] = booking_user.get('email', 'No email')
                booking['user_phone'] = booking_user.get('phone', 'No phone')
            else:
                booking['user_name'] = 'Unknown User'
                booking['user_email'] = 'No email'
                booking['user_phone'] = 'No phone'
            
            # Get property details for this booking
            booking_property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
            if booking_property:
                booking['property_name'] = booking_property.get('name', 'Unknown Property')
            else:
                booking['property_name'] = 'Unknown Property'
            
            recent_bookings.append(booking)
    
    # Get recent enquiries for owner's properties
    recent_enquiries = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        enquiries_cursor = mongo.db.enquiries.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1).limit(3)
        
        for enquiry in enquiries_cursor:
            # Get property details
            enquiry_property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
            if enquiry_property:
                enquiry['property_name'] = enquiry_property.get('name', 'Unknown Property')
            else:
                enquiry['property_name'] = 'Unknown Property'
            recent_enquiries.append(enquiry)
    
    # Calculate stats
    total_properties = len(properties)
    active_properties = len([p for p in properties if p.get('status') == 'active'])
    pending_bookings = len([b for b in recent_bookings if b.get('status') == 'pending'])
    
    return render_template('owner_dashboard.html', 
                         user=user, 
                         owner_profile=owner_profile,
                         properties=properties,
                         recent_bookings=recent_bookings,
                         recent_enquiries=recent_enquiries,
                         total_properties=total_properties,
                         active_properties=active_properties,
                         pending_bookings=pending_bookings)

@app.route('/owner-bookings')
def owner_bookings():
    """View all bookings for owner's properties"""
    if 'user_id' not in session:
        flash('Please login to view bookings', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get owner's properties
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    # Get all bookings for owner's properties with user details
    all_bookings = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        bookings_cursor = mongo.db.bookings.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1)
        
        for booking in bookings_cursor:
            # Get user details
            booking_user = mongo.db.users.find_one({'_id': booking.get('user_id')})
            if booking_user:
                booking['user_name'] = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip() or 'Unknown'
                booking['user_email'] = booking_user.get('email', 'No email')
                booking['user_phone'] = booking_user.get('phone', 'No phone')
            else:
                booking['user_name'] = 'Unknown User'
                booking['user_email'] = 'No email'
                booking['user_phone'] = 'No phone'
            
            # Get property details
            booking_property = mongo.db.hostels.find_one({'_id': booking.get('hostel_id')})
            if booking_property:
                booking['property_name'] = booking_property.get('name', 'Unknown Property')
                booking['property_city'] = booking_property.get('city', '')
                booking['property_location'] = booking_property.get('location', '')
            else:
                booking['property_name'] = 'Unknown Property'
                booking['property_city'] = ''
                booking['property_location'] = ''
            
            all_bookings.append(booking)
    
    return render_template('owner_bookings.html', user=user, bookings=all_bookings)

@app.route('/owner-enquiries')
def owner_enquiries():
    """View all enquiries for owner's properties"""
    if 'user_id' not in session:
        flash('Please login to view enquiries', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get owner's properties
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    
    # Get all enquiries for owner's properties
    all_enquiries = []
    if properties:
        property_ids = [prop['_id'] for prop in properties]
        enquiries_cursor = mongo.db.enquiries.find(
            {'hostel_id': {'$in': property_ids}}
        ).sort('created_at', -1)
        
        for enquiry in enquiries_cursor:
            # Get property details
            enquiry_property = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
            if enquiry_property:
                enquiry['property_name'] = enquiry_property.get('name', 'Unknown Property')
                enquiry['property_city'] = enquiry_property.get('city', '')
            else:
                enquiry['property_name'] = 'Unknown Property'
                enquiry['property_city'] = ''
            all_enquiries.append(enquiry)
    
    return render_template('owner_enquiries.html', user=user, enquiries=all_enquiries)

@app.route('/owner-profile', methods=['GET', 'POST'])
def owner_profile():
    """Owner profile completion page"""
    if 'user_id' not in session:
        flash('Please login to access your profile', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Update profile
        update_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'business_name': request.form.get('business_name', '').strip(),
            'business_type': request.form.get('business_type', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'state': request.form.get('state', '').strip(),
            'pincode': request.form.get('pincode', '').strip(),
            'bio': request.form.get('bio', '').strip(),
            'updated_at': datetime.utcnow()
        }
        
        # Set profile completion to 100%
        update_data['profile_completion'] = 100
        
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': update_data}
        )
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('owner_profile'))
    
    return render_template('owner_profile.html', user=user)

@app.route('/owner-verification', methods=['GET', 'POST'])
def owner_verification():
    """Owner verification page"""
    if 'user_id' not in session:
        flash('Please login to access verification', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Handle document uploads
        pan_number = request.form.get('pan_number', '').strip().upper()
        aadhar_number = request.form.get('aadhar_number', '').strip()
        bank_account = request.form.get('bank_account', '').strip()
        ifsc_code = request.form.get('ifsc_code', '').strip().upper()
        
        update_data = {
            'pan_number': pan_number,
            'aadhar_number': aadhar_number,
            'bank_account': bank_account,
            'ifsc_code': ifsc_code,
            'verification_status': 'pending',
            'verification_submitted_at': datetime.utcnow()
        }
        
        mongo.db.users.update_one(
            {'_id': ObjectId(session['user_id'])},
            {'$set': update_data}
        )
        
        flash('Verification documents submitted! We will review and verify within 24-48 hours.', 'success')
        return redirect(url_for('owner_verification'))
    
    return render_template('owner_verification.html', user=user)

@app.route('/owner-analytics')
def owner_analytics():
    """Owner analytics page"""
    if 'user_id' not in session:
        flash('Please login to view analytics', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or user.get('user_type') != 'owner':
        flash('Access denied. Owner account required.', 'error')
        return redirect(url_for('home'))
    
    # Get owner's properties
    properties = list(mongo.db.hostels.find({'created_by': session['user_id']}))
    property_ids = [prop['_id'] for prop in properties]
    
    # Calculate analytics
    total_properties = len(properties)
    active_properties = len([p for p in properties if p.get('status') == 'active'])
    pending_properties = len([p for p in properties if p.get('status') == 'pending'])
    
    # Get bookings stats
    total_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}}) if property_ids else 0
    confirmed_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'confirmed'}) if property_ids else 0
    pending_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'pending'}) if property_ids else 0
    rejected_bookings = mongo.db.bookings.count_documents({'hostel_id': {'$in': property_ids}, 'status': 'rejected'}) if property_ids else 0
    
    # Get enquiries count
    total_enquiries = mongo.db.enquiries.count_documents({'hostel_id': {'$in': property_ids}}) if property_ids else 0
    
    analytics = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'pending_properties': pending_properties,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'rejected_bookings': rejected_bookings,
        'total_enquiries': total_enquiries,
        'conversion_rate': round((confirmed_bookings / total_bookings * 100), 1) if total_bookings > 0 else 0
    }
    
    return render_template('owner_analytics.html', user=user, analytics=analytics, properties=properties)

@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please login to access admin dashboard', 'error')
        return redirect(url_for('login'))
    
    # Check if user is an admin (you might want to add an 'is_admin' field to users)
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user or not user.get('is_admin', False):
        flash('Access denied. Admin account required.', 'error')
        return redirect(url_for('home'))
    
    # Get all properties with owner information
    properties = list(mongo.db.hostels.find({}))
    
    # Add owner information to each property
    for property in properties:
        if property.get('created_by'):
            owner = mongo.db.users.find_one({'_id': ObjectId(property['created_by'])})
            if owner:
                property['owner_name'] = owner.get('first_name', 'Unknown') + ' ' + owner.get('last_name', '')
                property['owner_email'] = owner.get('email', 'No email')
            else:
                property['owner_name'] = 'Unknown Owner'
                property['owner_email'] = 'No email'
        else:
            property['owner_name'] = 'System Added'
            property['owner_email'] = 'N/A'
    
    # Get all bookings
    total_bookings = mongo.db.bookings.count_documents({})
    
    # Get total owners
    total_owners = mongo.db.users.count_documents({'user_type': 'owner'})
    
    # Calculate stats
    total_properties = len(properties)
    pending_properties = len([p for p in properties if p.get('status') == 'pending'])
    
    return render_template('admin_dashboard.html', 
                         user=user,
                         properties=properties,
                         total_properties=total_properties,
                         total_owners=total_owners,
                         pending_properties=pending_properties,
                         total_bookings=total_bookings)

@app.route('/account-settings')
def account_settings():
    if 'user_id' not in session:
        flash('Please login to access account settings', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('account_settings.html', user=user)

@app.route('/bookings')
def bookings():
    if 'user_id' not in session:
        flash('Please login to view your bookings', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Fetch user bookings from database
    bookings = list(mongo.db.bookings.find({'user_id': ObjectId(session['user_id'])}))
    
    # Enhance bookings with hostel information
    enhanced_bookings = []
    for booking in bookings:
        # Get hostel information
        hostel = mongo.db.hostels.find_one({'_id': booking['hostel_id']})
        if hostel:
            booking['hostel_name'] = hostel.get('name', 'Unknown Hostel')
            booking['hostel_location'] = hostel.get('location', '')
            booking['hostel_city'] = hostel.get('city', '')
            booking['hostel_image'] = hostel.get('image', '')
            booking['hostel_contact'] = hostel.get('contact_email', '')
        else:
            booking['hostel_name'] = 'Unknown Hostel'
            booking['hostel_location'] = ''
            booking['hostel_city'] = ''
            booking['hostel_image'] = ''
            booking['hostel_contact'] = ''
        
        # Convert ObjectId to string for template
        booking['_id'] = str(booking['_id'])
        booking['user_id'] = str(booking['user_id'])
        booking['hostel_id'] = str(booking['hostel_id'])
        
        enhanced_bookings.append(booking)
    
    return render_template('bookings.html', user=user, bookings=enhanced_bookings)

@app.route('/enquiries')
def enquiries():
    if 'user_id' not in session:
        flash('Please login to view your enquiries', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    # Fetch user enquiries from database
    enquiries = list(mongo.db.enquiries.find({'user_id': ObjectId(session['user_id'])}))
    print(f"DEBUG: Found {len(enquiries)} enquiries for user {session['user_id']}")
    for e in enquiries:
        print(f"DEBUG: Enquiry {e['_id']} status: {e.get('status')}")
    
    # Enhance enquiries with hostel information
    enhanced_enquiries = []
    for enquiry in enquiries:
        # Get hostel information
        hostel = mongo.db.hostels.find_one({'_id': enquiry['hostel_id']})
        if hostel:
            enquiry['hostel_name'] = hostel.get('name', 'Unknown Hostel')
            enquiry['hostel_location'] = hostel.get('location', '')
            enquiry['hostel_city'] = hostel.get('city', '')
            enquiry['hostel_image'] = hostel.get('image', '')
            enquiry['hostel_contact'] = hostel.get('contact_email', '')
        else:
            enquiry['hostel_name'] = 'Unknown Hostel'
            enquiry['hostel_location'] = ''
            enquiry['hostel_city'] = ''
            enquiry['hostel_image'] = ''
            enquiry['hostel_contact'] = ''
        
        # Convert ObjectId to string for template
        enquiry['_id'] = str(enquiry['_id'])
        enquiry['user_id'] = str(enquiry['user_id'])
        enquiry['hostel_id'] = str(enquiry['hostel_id'])
        
        enhanced_enquiries.append(enquiry)
    
    return render_template('enquiries.html', user=user, enquiries=enhanced_enquiries)

@app.route('/api/rating', methods=['POST'])
def api_rating():
    """Submit rating for a property"""
    try:
        data = request.get_json()
        
        hostel_id = data.get('hostel_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        name = data.get('name', 'Anonymous')
        email = data.get('email', '')
        
        if not hostel_id or not rating:
            return jsonify({
                'success': False,
                'message': 'Property ID and rating are required'
            }), 400
        
        # Validate rating is between 1-5
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({
                'success': False,
                'message': 'Rating must be between 1 and 5'
            }), 400
        
        # Get hostel
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        # Create rating record
        rating_record = {
            'hostel_id': ObjectId(hostel_id),
            'rating': rating,
            'comment': comment,
            'name': name,
            'email': email,
            'created_at': datetime.utcnow()
        }
        
        # Save rating
        mongo.db.ratings.insert_one(rating_record)
        
        # Calculate new average rating
        all_ratings = list(mongo.db.ratings.find({'hostel_id': ObjectId(hostel_id)}))
        total_ratings = len(all_ratings)
        avg_rating = sum(r['rating'] for r in all_ratings) / total_ratings if total_ratings > 0 else 0
        
        # Update hostel with average rating
        mongo.db.hostels.update_one(
            {'_id': ObjectId(hostel_id)},
            {'$set': {
                'avg_rating': round(avg_rating, 1),
                'total_ratings': total_ratings
            }}
        )
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully!',
            'avg_rating': round(avg_rating, 1),
            'total_ratings': total_ratings
        })
        
    except Exception as e:
        print(f"Rating error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/enquiry', methods=['POST'])
def api_enquiry():
    """Submit enquiry from property detail page (no login required)"""
    try:
        data = request.get_json()
        print(f"Received enquiry data: {data}")
        
        # Get required fields
        hostel_id = data.get('hostel_id')
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        
        print(f"Hostel ID: {hostel_id}, Name: {name}, Email: {email}, Phone: {phone}")
        
        if not hostel_id or not name or not email or not phone:
            return jsonify({
                'success': False,
                'message': 'Name, email, and phone are required'
            }), 400
        
        # Get hostel information
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        print(f"Found hostel: {hostel.get('name') if hostel else 'None'}")
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Property not found'
            }), 404
        
        # Create enquiry record
        enquiry = {
            'hostel_id': ObjectId(hostel_id),
            'hostel_name': data.get('hostel_name', hostel.get('name')),
            'name': name,
            'email': email,
            'phone': phone,
            'room_type': data.get('room_type', ''),
            'message': data.get('message', ''),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }

        # If user is logged in via session, link the enquiry to them
        if 'user_id' in session:
            enquiry['user_id'] = ObjectId(session['user_id'])
            print(f"Linking enquiry to logged-in user: {session['user_id']}")
        
        # Save enquiry to database
        mongo.db.enquiries.insert_one(enquiry)
        
        # Send confirmation emails to both user and owner
        user_email_sent = False
        owner_email_sent = False
        
        try:
            # Debug email configuration
            print(f"=== ENQUIRY EMAIL DEBUG (Unauthenticated) ===")
            print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            print(f"User Email: {email}")
            print(f"==========================================")
            
            # 1. Email to user with HTML template (enquiry confirmation)
            try:
                user_subject = f"Enquiry Submitted - {hostel['name']}"
                user_msg = Message(
                    user_subject,
                    sender=app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[email]
                )
                
                # Create user object for template
                user_data = {
                    'name': name,
                    'email': email
                }
                
                user_msg.html = render_template('emails/enquiry_confirmation_user.html', 
                                              user=user_data, 
                                              hostel=hostel, 
                                              message=data.get('message', ''),
                                              now=datetime.utcnow())
                mail.send(user_msg)
                user_email_sent = True
                print(f"[+] User confirmation email sent to: {email}")
            except Exception as user_email_error:
                print(f"[!] User email sending failed: {user_email_error}")
            
            # 2. Email to owner with enquiry notification
            owner_email = hostel.get('contact_email') or (hostel.get('owner_email') if hostel.get('owner_email') else None)
            
            # If owner email not in contact_email, try to get from owner_id
            if not owner_email:
                owner_id = hostel.get('owner_id') or hostel.get('created_by')
                if owner_id:
                    try:
                        owner_user = mongo.db.users.find_one({"_id": ObjectId(owner_id)})
                        if owner_user and owner_user.get('email'):
                            owner_email = owner_user.get('email')
                    except:
                        pass
            
            if owner_email:
                try:
                    owner_subject = f"New Enquiry - {hostel['name']} from {name}"
                    owner_msg = Message(
                        owner_subject,
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=[owner_email]
                    )
                    
                    # Create owner object for template
                    owner_data = {
                        'name': hostel.get('owner_name', 'Property Owner'),
                        'email': owner_email
                    }
                    
                    owner_msg.html = render_template('emails/enquiry_notification_owner.html',
                                                    user=user_data,
                                                    owner=owner_data,
                                                    hostel=hostel,
                                                    message=data.get('message', ''),
                                                    enquiry_time=datetime.utcnow(),
                                                    dashboard_link=None)
                    mail.send(owner_msg)
                    owner_email_sent = True
                    print(f"[+] Owner notification email sent to: {owner_email}")
                except Exception as owner_error:
                    print(f"[!] Owner email sending failed: {owner_error}")
            else:
                print(f"[!] Owner email not found for hostel {hostel_id}")
                
        except Exception as email_error:
            print(f"[-] Email sending failed: {email_error}")
            import traceback
            traceback.print_exc()
            # Still return success even if email fails
        
        # Build response message
        response_message = 'Enquiry sent successfully! The property owner will contact you soon.'
        if user_email_sent:
            response_message = 'Enquiry sent successfully! Confirmation email has been sent to your email address.'
        if owner_email_sent and user_email_sent:
            response_message = 'Enquiry sent successfully! Confirmation email sent to you and the property owner has been notified.'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'user_email_sent': user_email_sent,
            'owner_email_sent': owner_email_sent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/enquiry/submit', methods=['POST'])
@jwt_required()
def api_submit_enquiry():
    """Submit enquiry and send confirmation emails"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get required fields
        hostel_id = data.get('hostel_id')
        message = data.get('message')
        
        if not hostel_id or not message:
            return jsonify({
                'success': False,
                'message': 'Hostel ID and message are required'
            }), 400
        
        # Get user information
        user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get hostel information
        hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
        if not hostel:
            return jsonify({
                'success': False,
                'message': 'Hostel not found'
            }), 404
        
        # Get contact details from request or user profile
        name = data.get('name') or user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        email = data.get('email') or user.get('email')
        phone = data.get('phone') or user.get('phone')
        room_type = data.get('room_type', '')

        # Create enquiry record
        enquiry = {
            'user_id': ObjectId(current_user_id),
            'hostel_id': ObjectId(hostel_id),
            'hostel_name': hostel.get('name'),
            'name': name,
            'email': email,
            'phone': phone,
            'room_type': room_type,
            'message': message,
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        # Save enquiry to database
        mongo.db.enquiries.insert_one(enquiry)
        
        # Send confirmation emails to both user and owner
        user_email_sent = False
        owner_email_sent = False
        email_error_message = None
        
        try:
            # Debug email configuration
            print(f"=== ENQUIRY EMAIL DEBUG ===")
            print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            print(f"User Email: {user['email']}")
            print(f"===========================")
            
            # 1. Email to user with HTML template
            user_subject = f"Enquiry Submitted - {hostel['name']}"
            user_msg = Message(
                user_subject,
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user['email']]
            )
            user_msg.html = render_template('emails/enquiry_confirmation_user.html', 
                                          user=user, 
                                          hostel=hostel, 
                                          message=message,
                                          now=datetime.utcnow())
            mail.send(user_msg)
            user_email_sent = True
            print(f"[+] User confirmation email sent to: {user['email']}")
            
            # 2. Email to owner with enquiry notification
            # Get owner information
            owner_id = hostel.get('owner_id') or hostel.get('created_by')
            if owner_id:
                try:
                    owner = mongo.db.users.find_one({"_id": ObjectId(owner_id)})
                    if owner and owner.get('email'):
                        owner_subject = f"New Enquiry - {hostel['name']} from {user.get('name', user['email'])}"
                        owner_msg = Message(
                            owner_subject,
                            sender=app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[owner['email']]
                        )
                        owner_msg.html = render_template('emails/enquiry_notification_owner.html',
                                                        user=user,
                                                        owner=owner,
                                                        hostel=hostel,
                                                        message=message,
                                                        enquiry_time=datetime.utcnow(),
                                                        dashboard_link=None)
                        mail.send(owner_msg)
                        owner_email_sent = True
                        print(f"[+] Owner notification email sent to: {owner['email']}")
                    else:
                        print(f"[!] Owner email not found for hostel {hostel_id}")
                except Exception as owner_error:
                    print(f"[!] Owner email sending failed: {owner_error}")
                    # Continue without failing - owner email is optional
            else:
                print(f"[!] Owner ID not found for hostel {hostel_id}")
                
        except Exception as email_error:
            email_error_message = str(email_error)
            print(f"[-] Email sending failed: {email_error}")
            import traceback
            traceback.print_exc()
            # Still return success even if email fails
        
        # Build response message
        response_message = 'Enquiry submitted successfully!'
        if user_email_sent:
            response_message += ' Confirmation email has been sent to your email address.'
        if owner_email_sent:
            response_message += ' The property owner has been notified and will respond soon.'
        if not user_email_sent and not owner_email_sent:
            response_message += ' (Email notifications could not be sent, but your enquiry is confirmed.)'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'enquiry_id': str(enquiry['_id']) if '_id' in enquiry else None,
            'user_email_sent': user_email_sent,
            'owner_email_sent': owner_email_sent,
            'email_error': email_error_message if (not user_email_sent or not owner_email_sent) else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/enquiry/<enquiry_id>/followup', methods=['POST'])
@jwt_required()
def api_followup_enquiry(enquiry_id):
    """Follow up on an enquiry and notify owner"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        followup_message = data.get('message', '')
        
        # Get enquiry
        enquiry = mongo.db.enquiries.find_one({"_id": ObjectId(enquiry_id)})
        if not enquiry:
            return jsonify({
                'success': False,
                'message': 'Enquiry not found'
            }), 404
        
        # Check if user owns this enquiry
        if str(enquiry['user_id']) != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Get hostel and owner information
        hostel = mongo.db.hostels.find_one({'_id': enquiry.get('hostel_id')})
        owner = mongo.db.users.find_one({'_id': ObjectId(hostel.get('created_by'))}) if hostel else None
        
        # Update enquiry with follow-up
        mongo.db.enquiries.update_one(
            {"_id": ObjectId(enquiry_id)},
            {"$set": {
                'status': 'pending',
                'followed_up_at': datetime.utcnow()
            }}
        )
        
        # Send email to owner if owner email exists
        if owner and owner.get('email'):
            try:
                subject = f"Follow-up: User Response to Your Enquiry - {hostel.get('name', 'Property')}"
                body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px;">
                            <div style="text-align: center; margin-bottom: 30px;">
                                <h1 style="color: #2196F3; margin: 0;">StayFinder</h1>
                                <p style="color: #666; margin: 10px 0 0 0;">New Follow-up Message</p>
                            </div>
                            
                            <p style="color: #333; font-size: 16px; margin-bottom: 20px;">Hi {owner.get('name', 'Host')},</p>
                            
                            <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                                {enquiry.get('name')} has sent a follow-up message regarding their enquiry about your property.
                            </p>
                            
                            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                <p style="margin: 5px 0; color: #666;"><strong>Enquirer:</strong> {enquiry.get('name')}</p>
                                <p style="margin: 5px 0; color: #666;"><strong>Email:</strong> {enquiry.get('email')}</p>
                                <p style="margin: 5px 0; color: #666;"><strong>Phone:</strong> {enquiry.get('phone')}</p>
                                <p style="margin: 5px 0; color: #666;"><strong>Property:</strong> {hostel.get('name') if hostel else 'Unknown'}</p>
                            </div>
                            
                            <p style="color: #333; font-size: 16px; margin-bottom: 15px;"><strong>Follow-up Message:</strong></p>
                            <div style="background-color: #fff8e1; border-left: 4px solid #FFC107; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                                <p style="color: #333; margin: 0; white-space: pre-wrap;">{followup_message}</p>
                            </div>
                            
                            <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                                Please respond to this enquiry through your StayFinder dashboard to keep the conversation going.
                            </p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="https://stayfinder.example.com/owner/enquiries" style="display: inline-block; background-color: #2196F3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                    View in Dashboard
                                </a>
                            </div>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                            
                            <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                                This is an automated email. Please do not reply to this message.<br>
                                © 2024 StayFinder. All rights reserved.
                            </p>
                        </div>
                    </body>
                </html>
                """
                
                msg = Message(
                    subject=subject,
                    recipients=[owner.get('email')],
                    html=body
                )
                
                mail.send(msg)
                print(f"[+] Follow-up email sent to owner: {owner.get('email')}")
            except Exception as e:
                print(f"[-] Failed to send follow-up email to owner: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Follow-up sent successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/enquiry/<enquiry_id>/close', methods=['POST'])
@jwt_required()
def api_close_enquiry(enquiry_id):
    """Close an enquiry"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get enquiry
        enquiry = mongo.db.enquiries.find_one({"_id": ObjectId(enquiry_id)})
        if not enquiry:
            return jsonify({
                'success': False,
                'message': 'Enquiry not found'
            }), 404
        
        # Check if user owns this enquiry
        if str(enquiry['user_id']) != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Update enquiry status
        mongo.db.enquiries.update_one(
            {"_id": ObjectId(enquiry_id)},
            {"$set": {
                'status': 'closed',
                'closed_at': datetime.utcnow()
            }}
        )
        
        return jsonify({
            'success': True,
            'message': 'Enquiry closed successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/booking/<booking_id>/cancel', methods=['POST'])
@jwt_required()
def api_cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get booking
        booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            return jsonify({
                'success': False,
                'message': 'Booking not found'
            }), 404
        
        # Check if user owns this booking
        if str(booking['user_id']) != current_user_id:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Update booking status
        mongo.db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {
                'status': 'cancelled',
                'cancelled_at': datetime.utcnow()
            }}
        )
        
        return jsonify({
            'success': True,
            'message': 'Booking cancelled successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return {'success': False, 'message': 'Please login to update profile'}
    
    try:
        data = request.get_json()
        user_id = ObjectId(session['user_id'])
        
        # Update user profile
        update_data = {
            'name': data.get('name'),
            'phone': data.get('phone'),
            'gender': data.get('gender'),
            'profile_picture': data.get('profile_picture')
        }
        
        mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': update_data}
        )
        
        return {'success': True, 'message': 'Profile updated successfully'}
    except Exception as e:
        return {'success': False, 'message': str(e)}

# ==================== FORGOT PASSWORD ROUTES ====================

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP to user's email"""
    try:
        subject = "StayFinder - Password Reset OTP"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2196F3; margin: 0;">StayFinder</h1>
                        <p style="color: #666; margin: 10px 0 0 0;">Password Reset Request</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">Hi,</p>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        We received a request to reset your StayFinder account password. Use the OTP below to proceed:
                    </p>
                    
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 30px 0;">
                        <p style="margin: 0; color: #666; font-size: 14px;">Your One-Time Password (OTP):</p>
                        <h2 style="color: #2196F3; font-size: 36px; letter-spacing: 5px; margin: 15px 0;">{otp}</h2>
                        <p style="margin: 0; color: #999; font-size: 12px;">This OTP is valid for 10 minutes</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px; margin-bottom: 20px;">
                        <strong>Important:</strong> Never share this OTP with anyone. If you did not request a password reset, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                        This is an automated email. Please do not reply to this message.<br>
                        © 2024 StayFinder. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=body
        )
        
        mail.send(msg)
        print(f"[+] OTP sent successfully to: {email}")
        return True
    except Exception as e:
        print(f"[-] Failed to send OTP email: {str(e)}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Display forgot password page"""
    if request.method == 'POST':
        # This route handles the initial page load
        return render_template('forgot_password.html')
    return render_template('forgot_password.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to user's email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        # Check if user exists
        user = mongo.db.users.find_one({'email': email})
        if not user:
            # Don't reveal if email exists for security
            return jsonify({
                'success': False,
                'message': 'If an account with this email exists, an OTP will be sent shortly'
            }), 404
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        
        # Store OTP in database
        mongo.db.password_resets.update_one(
            {'email': email},
            {
                '$set': {
                    'otp': otp,
                    'otp_expiry': otp_expiry,
                    'created_at': datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Send OTP via email
        email_sent = send_otp_email(email, otp)
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': 'OTP sent successfully to your email'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send OTP. Please try again.'
            }), 500
    
    except Exception as e:
        print(f"Error in send_otp: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP sent to user's email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({
                'success': False,
                'message': 'Email and OTP are required'
            }), 400
        
        # Validate OTP
        otp_record = mongo.db.password_resets.find_one({'email': email})
        
        if not otp_record:
            return jsonify({
                'success': False,
                'message': 'No OTP found. Please request a new one.'
            }), 400
        
        # Check if OTP is expired
        if datetime.utcnow() > otp_record.get('otp_expiry', datetime.utcnow()):
            mongo.db.password_resets.delete_one({'email': email})
            return jsonify({
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            }), 400
        
        # Check if OTP matches
        if otp_record.get('otp') != otp:
            return jsonify({
                'success': False,
                'message': 'Invalid OTP. Please try again.'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'OTP verified successfully'
        })
    
    except Exception as e:
        print(f"Error in verify_otp: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset user's password after OTP verification"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '')
        
        if not email or not otp or not new_password:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400
        
        # Validate password strength
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # Verify OTP again for security
        otp_record = mongo.db.password_resets.find_one({'email': email})
        
        if not otp_record:
            return jsonify({
                'success': False,
                'message': 'Invalid request. Please request a new OTP.'
            }), 400
        
        if datetime.utcnow() > otp_record.get('otp_expiry', datetime.utcnow()):
            mongo.db.password_resets.delete_one({'email': email})
            return jsonify({
                'success': False,
                'message': 'OTP has expired. Please request a new one.'
            }), 400
        
        if otp_record.get('otp') != otp:
            return jsonify({
                'success': False,
                'message': 'Invalid OTP. Please try again.'
            }), 400
        
        # Find user and update password
        user = mongo.db.users.find_one({'email': email})
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        
        # Update password in database
        mongo.db.users.update_one(
            {'email': email},
            {
                '$set': {
                    'password': hashed_password,
                    'password_reset_at': datetime.utcnow()
                }
            }
        )
        
        # Delete OTP record
        mongo.db.password_resets.delete_one({'email': email})
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully. Please log in with your new password.'
        })
    
    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Get the port from the environment variable, default to 5000 if not found
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 so Render can access it
    app.run(host='0.0.0.0', port=port)
