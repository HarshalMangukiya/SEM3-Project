from app import mongo
import re

# Check what's in the database for 'sa' search
print("=== DEBUGGING SEARCH FOR 'sa' ===")

# Get all hostels
hostels = list(mongo.db.hostels.find())
print(f"Total hostels in database: {len(hostels)}")

print("\n=== ALL HOSTEL NAMES ===")
for hostel in hostels:
    name = hostel.get('name', '').lower()
    city = hostel.get('city', '').lower()
    location = hostel.get('location', '').lower()
    print(f"Name: '{name}' | City: '{city}' | Location: '{location}'")

print("\n=== TESTING REGEX PATTERNS ===")
query = 'sa'

# Test prefix matching
prefix_pattern = f'^{query}'
print(f"\nPrefix pattern: {prefix_pattern}")
for hostel in hostels:
    name = hostel.get('name', '')
    if re.search(prefix_pattern, name, re.IGNORECASE):
        print(f"  MATCH: {name}")

# Test word boundary matching  
word_boundary_pattern = r'\b' + re.escape(query) + r'\b'
print(f"\nWord boundary pattern: {word_boundary_pattern}")
for hostel in hostels:
    name = hostel.get('name', '')
    if re.search(word_boundary_pattern, name, re.IGNORECASE):
        print(f"  MATCH: {name}")

# Test what the current MongoDB query returns
print("\n=== MONGODB QUERY RESULTS ===")
search_conditions = [
    {"name": {"$regex": f'^{query}', "$options": "i"}},
    {"city": {"$regex": f'^{query}', "$options": "i"}},
    {"location": {"$regex": f'^{query}', "$options": "i"}}
]

search_query = {"$or": search_conditions}
results = list(mongo.db.hostels.find(search_conditions))
print(f"Query returned {len(results)} results:")
for result in results:
    print(f"  - {result.get('name', 'N/A')}")
