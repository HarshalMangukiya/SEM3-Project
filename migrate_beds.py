#!/usr/bin/env python3
"""
Migration script to add bed counts and booking tracking to all properties
"""

from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_beds():
    """Add 100 beds to each room type (double, triple, quadruple) for all properties"""
    
    # Connect to MongoDB
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment variables")
        return False
    
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=False
        )
        client.admin.command('ping')
        db = client["stayfinder"]
        print("✓ Connected to MongoDB")
        
        # Get all hostels/properties
        properties = db.hostels.find({})
        total_properties = db.hostels.count_documents({})
        updated_count = 0
        
        print(f"\n📊 Found {total_properties} properties")
        print("=" * 60)
        
        for property_doc in properties:
            property_id = property_doc.get('_id')
            property_name = property_doc.get('name', 'Unknown')
            
            # Initialize beds structure if it doesn't exist
            beds = property_doc.get('beds', {})
            
            # Add 100 beds for each room type if not already present
            if 'double_sharing' not in beds:
                beds['double_sharing'] = {
                    'regular': 100,
                    'ac': 100
                }
            else:
                if 'regular' not in beds['double_sharing']:
                    beds['double_sharing']['regular'] = 100
                if 'ac' not in beds['double_sharing']:
                    beds['double_sharing']['ac'] = 100
            
            if 'triple_sharing' not in beds:
                beds['triple_sharing'] = {
                    'regular': 100,
                    'ac': 100
                }
            else:
                if 'regular' not in beds['triple_sharing']:
                    beds['triple_sharing']['regular'] = 100
                if 'ac' not in beds['triple_sharing']:
                    beds['triple_sharing']['ac'] = 100
            
            if 'quadruple_sharing' not in beds:
                beds['quadruple_sharing'] = {
                    'regular': 100,
                    'ac': 100
                }
            else:
                if 'regular' not in beds['quadruple_sharing']:
                    beds['quadruple_sharing']['regular'] = 100
                if 'ac' not in beds['quadruple_sharing']:
                    beds['quadruple_sharing']['ac'] = 100
            
            # Update the property with new bed structure
            db.hostels.update_one(
                {'_id': property_id},
                {
                    '$set': {
                        'beds': beds,
                        'booking_count': property_doc.get('booking_count', 0),
                        'last_migrated': datetime.utcnow()
                    }
                }
            )
            
            updated_count += 1
            print(f"✓ Updated: {property_name}")
            print(f"  - Double Sharing: Regular=100, AC=100")
            print(f"  - Triple Sharing: Regular=100, AC=100")
            print(f"  - Quadruple Sharing: Regular=100, AC=100")
            print()
        
        print("=" * 60)
        print(f"✓ Migration completed successfully!")
        print(f"  - Total properties updated: {updated_count}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False
    finally:
        client.close()


def update_booking_counts():
    """Update booking counts for each property based on confirmed bookings"""
    
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment variables")
        return False
    
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=False
        )
        client.admin.command('ping')
        db = client["stayfinder"]
        print("✓ Connected to MongoDB for booking count update")
        
        # Get all properties
        properties = db.hostels.find({})
        total_properties = db.hostels.count_documents({})
        updated_count = 0
        
        print(f"\n📊 Updating booking counts for {total_properties} properties")
        print("=" * 60)
        
        for property_doc in properties:
            property_id = property_doc.get('_id')
            property_name = property_doc.get('name', 'Unknown')
            
            # Count confirmed bookings for this property
            confirmed_bookings = db.bookings.count_documents({
                'hostel_id': property_id,
                'status': 'confirmed'
            })
            
            # Update the property with booking count
            db.hostels.update_one(
                {'_id': property_id},
                {
                    '$set': {
                        'booking_count': confirmed_bookings
                    }
                }
            )
            
            updated_count += 1
            print(f"✓ Updated: {property_name}")
            print(f"  - Confirmed bookings: {confirmed_bookings}")
            print()
        
        print("=" * 60)
        print(f"✓ Booking count update completed!")
        print(f"  - Total properties updated: {updated_count}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during booking count update: {e}")
        return False
    finally:
        client.close()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 BED MIGRATION SCRIPT")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Add 100 beds for each room type (double, triple, quadruple)")
    print("2. Add AC and Regular facility options for each room type")
    print("3. Update booking counts for all properties")
    print()
    
    # Run migrations
    success = migrate_beds()
    
    if success:
        update_booking_counts()
        print("\n✅ All migrations completed successfully!")
    else:
        print("\n❌ Migration failed. Please check your MongoDB connection.")
