"""
Database utilities for StayFinder application
"""

import math
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import os


def load_colleges():
    """Load colleges data from JSON file"""
    try:
        with open('config/colleges.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠ Colleges data file not found")
        return []
    except Exception as e:
        print(f"⚠ Error loading colleges data: {e}")
        return []


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r


def find_college_by_name(college_name, colleges):
    """Find college by name (partial match)"""
    if not college_name:
        return None
    
    college_name_lower = college_name.lower()
    for college in colleges:
        if college_name_lower in college['Name'].lower():
            return college
    return None


def serialize_doc(doc):
    """Helper function to convert ObjectId to string"""
    if doc and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc


def get_database_connection(mongo_uri):
    """Get MongoDB database connection"""
    try:
        client = MongoClient(
            mongo_uri, 
            serverSelectionTimeoutMS=10000,
            ssl=True,
            tlsAllowInvalidCertificates=True,
            retryWrites=False
        )
        # Test the connection
        client.admin.command('ping')
        print("✓ MongoDB Atlas connection successful")
        
        # Get the database explicitly
        db = client["stayfinder"]
        print(f"✓ Database 'stayfinder' accessible")
        
        # Create a simple mongo object with db attribute
        class SimpleMongo:
            def __init__(self, database):
                self._db = database
                self.cx = client
                
            @property
            def db(self):
                return self._db
        
        return SimpleMongo(db)
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        # Create a mock mongo object for development
        class MockMongo:
            @property
            def db(self):
                return None
            @property 
            def cx(self):
                return None
        return MockMongo()
