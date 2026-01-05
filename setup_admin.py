#!/usr/bin/env python3
"""
Script to create an admin user for the admin dashboard
"""
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create an admin user"""
    try:
        # Connect to MongoDB
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/stayfinder')
        client = MongoClient(mongo_uri)
        db = client.get_database()
        
        # Check if admin already exists
        existing_admin = db.users.find_one({'email': 'admin@stayfinder.com'})
        if existing_admin:
            print("❌ Admin user already exists!")
            print(f"   Email: {existing_admin['email']}")
            print(f"   Name: {existing_admin.get('name', 'Admin')}")
            return False
        
        # Create admin user
        password = "admin123"  # Change this in production!
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        admin_user = {
            'name': 'System Administrator',
            'first_name': 'System',
            'last_name': 'Administrator',
            'email': 'admin@stayfinder.com',
            'password': hashed_password,
            'user_type': 'admin',
            'is_admin': True,
            'account_status': 'active',
            'created_at': datetime.datetime.utcnow(),
            'email_verified': True
        }
        
        result = db.users.insert_one(admin_user)
        
        print("✅ Admin user created successfully!")
        print(f"   User ID: {result.inserted_id}")
        print(f"   Email: admin@stayfinder.com")
        print(f"   Password: admin123")
        print("⚠️  IMPORTANT: Change the password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def list_admin_users():
    """List all admin users"""
    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/stayfinder')
        client = MongoClient(mongo_uri)
        db = client.get_database()
        
        admin_users = list(db.users.find({'is_admin': True}))
        
        if not admin_users:
            print("📭 No admin users found in the database.")
            return
        
        print("👑 Admin Users:")
        print("-" * 50)
        for i, admin in enumerate(admin_users, 1):
            print(f"{i}. {admin.get('name', 'Unknown')}")
            print(f"   Email: {admin.get('email', 'No email')}")
            print(f"   Type: {admin.get('user_type', 'admin')}")
            print(f"   Status: {admin.get('account_status', 'unknown')}")
            print(f"   Created: {admin.get('created_at', 'Unknown')}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Error listing admin users: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()

def make_user_admin(email):
    """Make an existing user an admin"""
    try:
        mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/stayfinder')
        client = MongoClient(mongo_uri)
        db = client.get_database()
        
        # Find the user
        user = db.users.find_one({'email': email})
        if not user:
            print(f"❌ User with email '{email}' not found!")
            return False
        
        # Update user to be admin
        result = db.users.update_one(
            {'email': email},
            {'$set': {'is_admin': True, 'user_type': 'admin'}}
        )
        
        if result.matched_count > 0:
            print(f"✅ User '{email}' is now an admin!")
            return True
        else:
            print(f"❌ Failed to update user '{email}'")
            return False
            
    except Exception as e:
        print(f"❌ Error making user admin: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    import datetime
    
    print("🔧 Stayfinder Admin Setup")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_admin.py create     # Create default admin user")
        print("  python setup_admin.py list       # List all admin users")
        print("  python setup_admin.py make <email>  # Make existing user admin")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        create_admin_user()
    elif command == "list":
        list_admin_users()
    elif command == "make" and len(sys.argv) == 3:
        email = sys.argv[2]
        make_user_admin(email)
    else:
        print("Invalid command!")
        print("Usage:")
        print("  python setup_admin.py create     # Create default admin user")
        print("  python setup_admin.py list       # List all admin users")
        print("  python setup_admin.py make <email>  # Make existing user admin")
