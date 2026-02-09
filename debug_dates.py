
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pprint

# Hardcoded URI
MONGO_URI = "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0"

def debug_dates():
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
    
    print(f"\nFound {len(bookings)} bookings. Checking Dates:")
    
    for b in bookings:
        print(f"\nBooking ID: {b['_id']}")
        print(f"  Status: {b.get('status')}")
        print(f"  Payment Status: {b.get('payment_status')}")
        print(f"  Created At: {b.get('created_at')}")
        print(f"  Payment Date: {b.get('payment_date')}")
        print(f"  Last Payment: {b.get('last_payment_date')}")
        print(f"  Updated At: {b.get('updated_at')}")
        
        # Simulate logic
        status = b.get('status')
        if not status:
            status = b.get('payment_status', 'pending')
            
        display_date = None
        if status == 'paid' or b.get('payment_status') == 'paid':
             display_date = b.get('payment_date') or b.get('last_payment_date') or b.get('updated_at') or b.get('created_at')
             print(f"  [LOGIC] Paid -> Using Payment/Update Date")
        else:
             display_date = b.get('created_at')
             print(f"  [LOGIC] Not Paid -> Using Created At")
             
        print(f"  => Display Date: {display_date}")

if __name__ == "__main__":
    debug_dates()
