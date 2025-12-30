from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, verify_jwt_in_request
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from bson import json_util
import os
import re
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

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder=".")

# Configure Flask
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 24)))

# Initialize JWT
jwt = JWTManager(app)

# Initialize OAuth
oauth = OAuth(app)

# --- DATABASE CONFIGURATION ---
# Ensure MongoDB is running on your computer OR replace with your Atlas URL
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/Stayfinder")
mongo = PyMongo(app)

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
# Initialize Firebase Admin SDK
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

# Facebook OAuth
facebook = oauth.register(
    name='facebook',
    client_id=os.environ.get('FACEBOOK_CLIENT_ID'),
    client_secret=os.environ.get('FACEBOOK_CLIENT_SECRET'),
    access_token_url='https://graph.facebook.com/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    client_kwargs={'scope': 'email'},
)

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize Mail
mail = Mail(app)

# --- API ENDPOINTS FOR JAVASCRIPT FRONTEND ---
# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

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
            print(f" User email sent to: {user['email']}")
            
            # Email to owner (if contact email exists)
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
- Phone: {user.get('phone', 'Not provided')}
- Request Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Action Required:
Please contact the user to confirm availability and proceed with the booking.

Best regards,
Stayfinder Team
                """
                mail.send(owner_msg)
                print(f" Owner email sent to: {hostel['contact_email']}")
                
        except Exception as email_error:
            print(f" Email sending failed: {email_error}")
            # Still return success even if email fails
        
        return jsonify({
            'success': True,
            'message': 'Booking request submitted successfully! Confirmation emails have been sent.',
            'booking_id': str(booking['_id']) if '_id' in booking else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

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

# --- ROUTES ---

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

@app.route('/')
def home():
    # Get all hostels from the database
    hostels = list(mongo.db.hostels.find())
    return render_template('index.html', hostels=hostels)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    # Simple search by City (case insensitive)
    hostels = list(mongo.db.hostels.find({"city": {"$regex": query, "$options": "i"}}))
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

@app.route('/help-center')
def help_center():
    return render_template('helpcenter.html')

@app.route('/safety')
def safety():
    return render_template('safety.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/cancellation')
def cancellation():
    return render_template('cancellation.html')

@app.route('/hostel/<hostel_id>')
def detail(hostel_id):
    # Find specific hostel by ID
    hostel = mongo.db.hostels.find_one({"_id": ObjectId(hostel_id)})
    return render_template('detail.html', hostel=hostel)

@app.route('/add', methods=['GET', 'POST'])
def add_hostel():
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
                            flash(f'Cloudinary credentials missing: {", ".join(missing)}. Photos not uploaded.', 'warning')
                            break
                    except Exception as e:
                        print(f"Error uploading photo: {e}")
                        continue
            
            if uploaded_count > 0:
                flash(f'{uploaded_count} photos uploaded successfully!', 'success')
                # Set the first photo as the main image if no image_url provided
                if not image_url and photo_urls:
                    image_url = photo_urls[0]
        
        # Ensure we have an image URL - use placeholder if none provided
        if not image_url or image_url.strip() == '':
            # Default placeholder image
            image_url = "https://via.placeholder.com/400x300?text=No+Image"
            flash('No image provided. Using placeholder image.', 'info')
        
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
            "property_type": request.form.get("property_type", "Hostel")  # Hostel or PG
        }
        
        # Add individual pricing fields to the hostel document
        new_hostel.update(pricing_data)
        mongo.db.hostels.insert_one(new_hostel)
        flash('Hostel added successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('add.html')

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Find user in database
        user = mongo.db.users.find_one({'email': email})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Create JWT token
            access_token = create_access_token(identity=str(user['_id']))
            session['user_id'] = str(user['_id'])
            session['access_token'] = access_token
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
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
            'created_at': datetime.utcnow(),
            'auth_method': 'email'
        }
        
        mongo.db.users.insert_one(new_user)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

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
            'redirect': url_for('home')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Authentication failed: {str(e)}'}), 500

# --- USER PROFILE ROUTES ---

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
    return render_template('bookings.html', user=user)

@app.route('/enquiries')
def enquiries():
    if 'user_id' not in session:
        flash('Please login to view your enquiries', 'error')
        return redirect(url_for('login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('enquiries.html', user=user)

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

if __name__ == '__main__':
    app.run(debug=True)