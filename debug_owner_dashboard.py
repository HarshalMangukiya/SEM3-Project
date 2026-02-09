
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pprint

# Hardcoded URI from settings.py
MONGO_URI = "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0"

def debug_dashboard():
    print(f"Connecting to {MONGO_URI.split('@')[1]}...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['stayfinder']
        # force connection
        client.admin.command('ping')
        print("[OK] Connected to database")
    except Exception as e:
        print(f"[ERROR] Could not connect: {e}")
        return

    # 1. Find property "antilla"
    print("\n--- Property: antilla ---")
    property_obj = db.hostels.find_one({'name': {'$regex': 'antilla', '$options': 'i'}})
    
    if not property_obj:
        print("Property 'antilla' not found!")
        return
        
    print(f"Found Property: {property_obj.get('name')}")
    print(f"ID: {property_obj.get('_id')}")
    print(f"Created By (Owner ID): {property_obj.get('created_by')}")
    
    owner_id = property_obj.get('created_by')
    
    # 2. Check bookings for this property
    print("\n--- Bookings for 'antilla' (Legacy Query) ---")
    query = {
        '$or': [
            {'hostel_id': property_obj['_id']},
            {'property_id': property_obj['_id']},
        ]
    }
    bookings = list(db.bookings.find(query))
    print(f"Found (Legacy): {len(bookings)}")
    
    print("\n--- Bookings for 'antilla' (NEW QUERY) ---")
    # Simulate NEW route logic
    all_ids = [property_obj['_id'], str(property_obj['_id'])]
    
    dashboard_query = {
            '$or': [
                {'hostel_id': {'$in': all_ids}},
                {'property_id': {'$in': all_ids}},
                {'created_by': owner_id},
                {'created_by': str(owner_id)}
            ]
        }
    
    recent_bookings = list(db.bookings.find(dashboard_query).sort('created_at', -1).limit(5))
    print(f"Dashboard Query Found: {len(recent_bookings)}")
    
    for b in recent_bookings:
        print(f"  - Booking ID: {b['_id']}")
        print(f"    Hostel ID: {b.get('hostel_id')} (Type: {type(b.get('hostel_id'))})")

if __name__ == "__main__":
    debug_dashboard()
