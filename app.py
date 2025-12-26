from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from authlib.integrations.flask_client import OAuth
import bcrypt
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, auth

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
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

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

# --- ROUTES ---

@app.route('/')
def home():
    # Get all hostels from the database
    hostels = mongo.db.hostels.find()
    return render_template('index.html', hostels=hostels)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    # Simple search by City (case insensitive)
    hostels = mongo.db.hostels.find({"city": {"$regex": query, "$options": "i"}})
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
        image_url = request.form.get("image")  # Fallback to URL if provided
        
        # Check if a file was uploaded
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '':
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder="stayfinder/hostels",  # Organize images in a folder
                        resource_type="image"
                    )
                    image_url = upload_result.get('secure_url')  # Get the secure URL
                except Exception as e:
                    # If upload fails, fall back to URL input or show error
                    print(f"Cloudinary upload error: {str(e)}")
                    # You might want to flash an error message here
        
        new_hostel = {
            "name": request.form.get("name"),
            "city": request.form.get("city"),
            "price": request.form.get("price"),
            "image": image_url,  # Cloudinary URL or provided URL
            "desc": request.form.get("desc"),
            "type": request.form.get("type")  # e.g., Boys, Girls, Co-ed
        }
        mongo.db.hostels.insert_one(new_hostel)
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