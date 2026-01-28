#!/usr/bin/env python3
"""Debug script to check MongoDB connection and data"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')

print("=" * 60)
print("MongoDB Connection Debugger")
print("=" * 60)

if not MONGO_URI:
    print("❌ ERROR: MONGO_URI not found in .env file")
    exit(1)

print(f"✓ MONGO_URI found")
print(f"  Connecting to: mongodb+srv://***@***")

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Test connection
    client.admin.command('ping')
    print("✓ Connected to MongoDB successfully!")
    
    # Get database
    db = client["stayfinder"]
    print(f"✓ Database 'stayfinder' accessible")
    
    # List all collections
    collections = db.list_collection_names()
    print(f"\n📁 Collections in 'stayfinder' database:")
    for col in collections:
        count = db[col].count_documents({})
        print(f"   - {col}: {count} documents")
    
    # Check hostels collection specifically
    print("\n" + "=" * 60)
    print("Checking 'hostels' collection:")
    print("=" * 60)
    
    if "hostels" in collections:
        count = db.hostels.count_documents({})
        print(f"✓ Collection 'hostels' found with {count} documents")
        
        if count > 0:
            # Show first document
            sample = db.hostels.find_one()
            print(f"\n📄 Sample document (first hostel):")
            print(f"   Name: {sample.get('name', 'N/A')}")
            print(f"   City: {sample.get('city', 'N/A')}")
            print(f"   Price: {sample.get('price', 'N/A')}")
            print(f"   Status: {sample.get('status', 'No status field')}")
            print(f"\n   Full data (first 500 chars):")
            print(f"   {str(sample)[:500]}")
        else:
            print("⚠️  Collection is empty!")
    else:
        print("❌ Collection 'hostels' NOT found!")
        print(f"   Available collections: {', '.join(collections)}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print("If you see hostels with count > 0 above:")
    print("✓ Data is in MongoDB")
    print("✓ Connection is working")
    print("→ The app should show the properties")
    print("\nIf hostels count is 0 or collection doesn't exist:")
    print("→ Need to check if data is in a different collection")
    print("→ Or data needs to be added to MongoDB")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\nPossible issues:")
    print("1. MONGO_URI is incorrect")
    print("2. Network connection problem")
    print("3. MongoDB Atlas cluster not accessible")
    print("4. Wrong credentials")

finally:
    if 'client' in locals():
        client.close()
