
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pprint

# Hardcoded URI
MONGO_URI = "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0"

def debug_users():
    print(f"Connecting...")
    client = MongoClient(MONGO_URI)
    db = client['stayfinder']
    
    # 1. Find property "antilla"
    property_obj = db.hostels.find_one({'name': {'$regex': 'antilla', '$options': 'i'}})

    # 2. Get bookings
    all_ids = [property_obj['_id'], str(property_obj['_id'])]
    bookings = list(db.bookings.find({
        '$or': [
            {'hostel_id': {'$in': all_ids}},
            {'property_id': {'$in': all_ids}}
        ]
    }).sort('created_at', -1).limit(5))
    
    print(f"\nFound {len(bookings)} bookings. Simulating Fix:")
    
    for b in bookings:
        print(f"\nBooking ID: {b['_id']}")
        
        # Simulate logic in routes.py
        user_id = b.get('user_id')
        booking_user = None
        
        if user_id:
            try:
                if isinstance(user_id, str):
                    user_id = ObjectId(user_id.strip())
                booking_user = db.users.find_one({'_id': user_id})
            except Exception as e:
                print(f"  Error: {e}")
        
        if booking_user:
            name = booking_user.get('name') or f"{booking_user.get('first_name', '')} {booking_user.get('last_name', '')}".strip()
            print(f"  [SUCCESS] Resolved User: {name}")
            print(f"  Email: {booking_user.get('email')}")
        else:
            print(f"  [FAILURE] Could not resolve user")

if __name__ == "__main__":
    debug_users()
