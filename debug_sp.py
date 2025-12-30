from app import mongo
import re

# Check exact names for 'sp'
print("=== DEBUGGING SEARCH FOR 'sp' ===")

hostels = list(mongo.db.hostels.find())
print("\n=== HOSTELS STARTING WITH 'sp' ===")
for hostel in hostels:
    name = hostel.get('name', '')
    if name.lower().startswith('sp'):
        print(f"Name: '{name}' (length: {len(name)})")
        print(f"  - Starts with 'sp': {name.lower().startswith('sp')}")
        print(f"  - Exact 'sp': {name.lower() == 'sp'}")
        print(f"  - Contains 'sp': {'sp' in name.lower()}")
        print()

# Test regex patterns
query = 'sp'
print(f"=== TESTING PATTERNS FOR '{query}' ===")

patterns = [
    f'^{re.escape(query)}$',
    f'^{re.escape(query)}',
    r'\b' + re.escape(query) + r'\b',
    r'\b' + re.escape(query)
]

for pattern in patterns:
    print(f"\nPattern: {pattern}")
    matches = []
    for hostel in hostels:
        name = hostel.get('name', '')
        if re.search(pattern, name, re.IGNORECASE):
            matches.append(name)
    print(f"  Matches: {matches}")
