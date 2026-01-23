#!/usr/bin/env python3
"""
Quick test to verify JWT configuration
"""

import sys
sys.path.append('.')

from app import app

def test_jwt_config():
    """Test JWT configuration"""
    print("=== JWT Configuration Test ===")
    
    with app.app_context():
        jwt_expires = app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
        print(f"JWT_ACCESS_TOKEN_EXPIRES: {jwt_expires}")
        
        if jwt_expires:
            hours = jwt_expires.total_seconds() / 3600
            print(f"✅ JWT tokens expire after: {hours} hours")
            
            if hours >= 24:
                print("✅ JWT expiration is correctly set to 24+ hours")
                return True
            else:
                print(f"⚠️  JWT expiration is only {hours} hours (should be 24+)")
                return False
        else:
            print("❌ JWT_ACCESS_TOKEN_EXPIRES is not set!")
            return False

if __name__ == "__main__":
    success = test_jwt_config()
    
    if success:
        print("\n🎉 JWT configuration is correct!")
        print("📝 Please restart your Flask application to apply the changes")
    else:
        print("\n❌ JWT configuration needs to be fixed")
