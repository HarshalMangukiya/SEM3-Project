#!/usr/bin/env python3
"""
Debug the actual content of the photos array
"""

import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

def debug_photos_content():
    """Debug what's actually in the photos array"""
    
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
            
            # Check photos
            photos = hostel.get('photos', [])
            print(f"Photos array length: {len(photos)}")
            
            if photos:
                print("First few photos with types:")
                for i, photo in enumerate(photos[:3]):
                    print(f"  {i+1}: Type: {type(photo)} - Value: {str(photo)[:100]}")
                    
                    # Check if it's a string
                    if isinstance(photo, str):
                        print(f"      ✅ It's a string")
                    else:
                        print(f"      ❌ It's NOT a string!")
                        print(f"      ❌ This is the problem!")
                        
                        # Try to convert to string
                        try:
                            photo_str = str(photo)
                            print(f"      🔄 As string: {photo_str[:100]}")
                        except Exception as e:
                            print(f"      ❌ Can't convert to string: {e}")
            
            # Test JSON serialization
            import json
            try:
                json_str = json.dumps(photos)
                print(f"✅ JSON serialization works: {len(json_str)} chars")
                print(f"First 100 chars: {json_str[:100]}")
            except Exception as e:
                print(f"❌ JSON serialization failed: {e}")
                
                # Try with string conversion
                try:
                    photos_as_strings = [str(photo) for photo in photos]
                    json_str = json.dumps(photos_as_strings)
                    print(f"✅ JSON with string conversion works: {len(json_str)} chars")
                    print(f"First 100 chars: {json_str[:100]}")
                except Exception as e2:
                    print(f"❌ Even string conversion failed: {e2}")
                
        else:
            print("No hostel found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_photos_content()
