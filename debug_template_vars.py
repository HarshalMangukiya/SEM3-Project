#!/usr/bin/env python3
"""
Debug what template variables are available
"""

import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

def debug_template_vars():
    """Debug the actual hostel data that would be sent to template"""
    
    try:
        # Connect to MongoDB
        MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0")
        
        client = MongoClient(
            MONGO_URI, 
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=False
        )
        
        db = client["stayfinder"]
        
        # Find the LA 365 hostel
        hostel = db.hostels.find_one({"name": {"$regex": "LA 365", "$options": "i"}})
        
        if hostel:
            print(f"Hostel: {hostel.get('name', 'N/A')}")
            print(f"Hostel ID: {hostel['_id']}")
            
            # Check photos
            photos = hostel.get('photos', [])
            print(f"Hostel photos array length: {len(photos)}")
            
            if photos:
                print("First few photos:")
                for i, photo in enumerate(photos[:3]):
                    print(f"  {i+1}: {photo[:50]}...")
            
            # Check main image
            main_image = hostel.get('image')
            print(f"Main image: {main_image[:50] if main_image else 'None'}...")
            
            # Simulate the template logic
            print("\n🔍 Simulating template logic:")
            
            all_photos = []
            if photos and len(photos) > 0:
                all_photos = photos
                print("✅ Using photos array")
            elif main_image and main_image and main_image.strip():
                all_photos = [main_image]
                print("✅ Using main image")
            else:
                all_photos = []
                print("❌ No photos available")
            
            print(f"Final all_photos length: {len(all_photos)}")
            
            if len(all_photos) > 0:
                print(f"✅ Main photo would be: {all_photos[0][:50]}...")
                
                if len(all_photos) > 1:
                    print(f"✅ {len(all_photos)} thumbnails would be shown")
                else:
                    print("ℹ️  Only 1 photo, so no thumbnails would be shown")
                    print("ℹ️  This is normal behavior - thumbnails only show for multiple photos")
            else:
                print("❌ No photos to show")
                
        else:
            print("No hostel found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_template_vars()
