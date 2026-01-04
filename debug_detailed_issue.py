#!/usr/bin/env python3
"""
Debug the actual lightbox issue in detail
"""

import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask, render_template
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_detail_page_issue():
    """Debug the actual detail page rendering"""
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
            print(f"Hostel Found: {hostel.get('name', 'N/A')}")
            print(f"Hostel ID: {hostel['_id']}")
            
            # Simulate the exact template logic
            all_photos = []
            if hostel.get('photos') and len(hostel.get('photos', [])) > 0:
                all_photos = hostel['photos']
            elif hostel.get('image') and hostel.get('image') and hostel.get('image', '').strip():
                all_photos = [hostel['image']]
            else:
                all_photos = []
            
            print(f"Final all_photos array length: {len(all_photos)}")
            
            # Test JSON serialization like in template
            try:
                photos_json = json.dumps(all_photos)
                print(f"JSON serialization: SUCCESS")
                print(f"JSON length: {len(photos_json)}")
                
                # Test if this would be valid in HTML attribute
                print(f"First 200 chars of JSON: {photos_json[:200]}")
                
                # Simulate what the JavaScript would see
                print(f"\nSimulating JavaScript parsing...")
                
                # This simulates: data-photos="{{ all_photos|tojson|safe }}"
                simulated_attr = photos_json  # This is what |tojson|safe produces
                
                # This simulates: JSON.parse(photosData)
                parsed_back = json.loads(simulated_attr)
                print(f"Parsed back successfully: {len(parsed_back)} photos")
                
                # This simulates the filtering logic
                filtered = []
                for photo in parsed_back:
                    if photo and isinstance(photo, str) and photo.startswith('http'):
                        filtered.append(photo)
                
                print(f"After filtering (original logic): {len(filtered)} photos")
                
                # Test the new filtering logic
                filtered_new = []
                for photo in parsed_back:
                    if photo and isinstance(photo, str):
                        is_valid_url = photo.startswith('http://') or photo.startswith('https://') or photo.startswith('//')
                        is_image_path = '.jpg' in photo or '.jpeg' in photo or '.png' in photo or '.gif' in photo or '.webp' in photo
                        if is_valid_url or is_image_path:
                            filtered_new.append(photo)
                
                print(f"After filtering (new logic): {len(filtered_new)} photos")
                
                if len(filtered) == 0 and len(filtered_new) > 0:
                    print("❌ ISSUE FOUND: Original filtering logic removes all photos!")
                    print("✅ New logic would keep the photos")
                elif len(filtered) > 0:
                    print("✅ Original filtering logic works")
                else:
                    print("❌ No photos pass either filter")
                
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
    print("Debugging Detail Page Lightbox Issue")
    print("=" * 50)
    debug_detail_page_issue()
