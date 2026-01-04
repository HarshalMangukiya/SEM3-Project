#!/usr/bin/env python3
"""
Debug script to check photo data rendering
"""

import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask, render_template

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_photo_data():
    """Debug photo data for a specific hostel"""
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
        
        # Find the hostel from your screenshot (LA 365 Daughter's Home)
        hostel = db.hostels.find_one({"name": {"$regex": "LA 365", "$options": "i"}})
        
        if not hostel:
            # Try another hostel if that one doesn't exist
            hostel = db.hostels.find_one()
        
        if hostel:
            print(f"Hostel Found: {hostel.get('name', 'N/A')}")
            print(f"Hostel ID: {hostel['_id']}")
            
            # Check photos array
            photos = hostel.get('photos', [])
            print(f"Photos array length: {len(photos)}")
            
            if photos:
                print("First few photos:")
                for i, photo in enumerate(photos[:3]):
                    print(f"  {i+1}: {photo}")
                    print(f"     Type: {type(photo)}")
                    print(f"     Valid URL: {photo.startswith('http') if photo else False}")
            
            # Check main image
            main_image = hostel.get('image')
            print(f"Main image: {main_image}")
            print(f"Main image type: {type(main_image)}")
            print(f"Main image valid: {main_image.startswith('http') if main_image else False}")
            
            # Simulate the template logic
            all_photos = []
            if photos and len(photos) > 0:
                all_photos = photos
            elif main_image and main_image and main_image.strip():
                all_photos = [main_image]
            else:
                all_photos = []
            
            print(f"Final all_photos array: {all_photos}")
            print(f"Final array length: {len(all_photos)}")
            
            # Test JSON serialization
            import json
            try:
                json_str = json.dumps(all_photos)
                print(f"JSON serialization: SUCCESS")
                print(f"JSON length: {len(json_str)}")
                print(f"JSON preview: {json_str[:200]}...")
            except Exception as e:
                print(f"JSON serialization FAILED: {e}")
            
            return True
        else:
            print("No hostel found")
            return False
                
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Debugging Photo Data Rendering")
    print("=" * 40)
    debug_photo_data()
