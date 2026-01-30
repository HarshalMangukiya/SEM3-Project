"""
Script to update all existing properties with bed availability counts.
This adds 50 beds for each room type (Double, Triple, Quadruple - Regular & AC).
Run this once to update your existing database records.
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI')

if not MONGO_URI:
    # Fallback to hardcoded URI if not in env
    MONGO_URI = "mongodb+srv://harshal_mangukiya_db_user:HhH3iDZDPm71omqY@cluster0.ntg5ion.mongodb.net/?appName=Cluster0"

print("[OK] Connecting to MongoDB...")

try:
    # Connect to MongoDB
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=10000,
        ssl=True,
        tlsAllowInvalidCertificates=True,
        retryWrites=False
    )
    
    # Test connection
    client.admin.command('ping')
    print("[OK] MongoDB Atlas connection successful")
    
    # Use the stayfinder database (as defined in utils/database.py)
    db = client["stayfinder"]
    print("[OK] Connected to database: stayfinder")
    
    # Get all hostels/PGs
    hostels = list(db.hostels.find({}))
    print(f"[OK] Found {len(hostels)} properties to update")
    
    if len(hostels) == 0:
        print("[INFO] No properties found in database. Add some properties first.")
        exit(0)
    
    # Default bed count
    DEFAULT_BEDS = 50
    
    # Update each property
    updated_count = 0
    for hostel in hostels:
        hostel_id = hostel['_id']
        hostel_name = hostel.get('name', 'Unknown')
        
        # Prepare bed availability data (preserve existing booked counts)
        bed_update = {
            # Double Sharing
            'double_sharing_regular_total_beds': DEFAULT_BEDS,
            'double_sharing_regular_booked_beds': hostel.get('double_sharing_regular_booked_beds', 0),
            'double_sharing_ac_total_beds': DEFAULT_BEDS,
            'double_sharing_ac_booked_beds': hostel.get('double_sharing_ac_booked_beds', 0),
            
            # Triple Sharing
            'triple_sharing_regular_total_beds': DEFAULT_BEDS,
            'triple_sharing_regular_booked_beds': hostel.get('triple_sharing_regular_booked_beds', 0),
            'triple_sharing_ac_total_beds': DEFAULT_BEDS,
            'triple_sharing_ac_booked_beds': hostel.get('triple_sharing_ac_booked_beds', 0),
            
            # Quadruple Sharing
            'quadruple_sharing_regular_total_beds': DEFAULT_BEDS,
            'quadruple_sharing_regular_booked_beds': hostel.get('quadruple_sharing_regular_booked_beds', 0),
            'quadruple_sharing_ac_total_beds': DEFAULT_BEDS,
            'quadruple_sharing_ac_booked_beds': hostel.get('quadruple_sharing_ac_booked_beds', 0),
        }
        
        # Update the property
        result = db.hostels.update_one(
            {'_id': hostel_id},
            {'$set': bed_update}
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            updated_count += 1
            print(f"  [UPDATED] {hostel_name}")
    
    print("")
    print("=" * 50)
    print(f"[SUCCESS] Updated {updated_count} properties!")
    print(f"   Each property now has {DEFAULT_BEDS} beds per room type:")
    print(f"   - Double Sharing Regular: {DEFAULT_BEDS} beds")
    print(f"   - Double Sharing AC: {DEFAULT_BEDS} beds")
    print(f"   - Triple Sharing Regular: {DEFAULT_BEDS} beds")
    print(f"   - Triple Sharing AC: {DEFAULT_BEDS} beds")
    print(f"   - Quadruple Sharing Regular: {DEFAULT_BEDS} beds")
    print(f"   - Quadruple Sharing AC: {DEFAULT_BEDS} beds")
    print(f"   Total: {DEFAULT_BEDS * 6} beds per property")
    print("=" * 50)
    
    client.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    exit(1)
