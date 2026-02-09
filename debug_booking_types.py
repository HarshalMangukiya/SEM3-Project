
import os
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import pprint

# Hardcoded URI
MONGO_URI = "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0"

def debug_types():
    print(f"Connecting...")
    client = MongoClient(MONGO_URI)
    db = client['stayfinder']
    
    # 1. Find property "antilla"
    property_obj = db.hostels.find_one({'name': {'$regex': 'antilla', '$options': 'i'}})
    if not property_obj:
        print("Antilla not found")
        return

    print(f"Property ID: {property_obj['_id']} (Type: {type(property_obj['_id'])})")
    print(f"Property Owner: {property_obj.get('created_by')} (Type: {type(property_obj.get('created_by'))})")
    
    # 2. Find any booking for this property (try both types)
    print("\n--- Searching for bookings ---")
    
    # Try with ObjectId
    b_oid = db.bookings.find_one({'hostel_id': property_obj['_id']})
    if b_oid:
        print("Found with ObjectId match!")
        pprint.pprint(b_oid)
    else:
        print("Not found with ObjectId match")
        
    # Try with String
    b_str = db.bookings.find_one({'hostel_id': str(property_obj['_id'])})
    if b_str:
        print("Found with String match!")
        pprint.pprint(b_str)
    else:
        print("Not found with String match")

if __name__ == "__main__":
    debug_types()
