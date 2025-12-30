from app import mongo
import re

# Debug the exact MongoDB query for 'sp'
query = 'sp'
query_clean = query.strip()

print(f"=== DEBUGGING MONGODB QUERY FOR '{query}' ===")
print(f"Query length: {len(query_clean)}")

# Build the exact search conditions as per the code
search_conditions = []

if len(query_clean) <= 2:
    print("Using 2-char logic")
    search_conditions.extend([
        {"name": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
        {"city": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
        {"location": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}}
    ])
elif len(query_clean) <= 3:
    print("Using 3-char logic")
    word_boundary_pattern = r'\b' + re.escape(query_clean) + r'\b'
    search_conditions.extend([
        {"name": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
        {"city": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
        {"location": {"$regex": f'^{re.escape(query_clean)}$', "$options": "i"}},
        {"name": {"$regex": word_boundary_pattern, "$options": "i"}},
        {"city": {"$regex": word_boundary_pattern, "$options": "i"}},
        {"location": {"$regex": word_boundary_pattern, "$options": "i"}},
        # Allow prefix matching for 3-char queries
        {"name": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}},
        {"city": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}},
        {"location": {"$regex": f'^{re.escape(query_clean)}', "$options": "i"}}
    ])

print(f"\nSearch conditions ({len(search_conditions)}):")
for i, condition in enumerate(search_conditions):
    print(f"  {i+1}. {condition}")

# Test each condition individually
hostels = list(mongo.db.hostels.find())
print(f"\n=== TESTING EACH CONDITION ===")

for i, condition in enumerate(search_conditions):
    try:
        results = list(mongo.db.hostels.find(condition))
        print(f"  Condition {i+1}: {len(results)} results")
        for result in results:
            print(f"    - {result.get('name', 'N/A')}")
    except Exception as e:
        print(f"  Condition {i+1}: ERROR - {e}")

# Test the combined OR query
if search_conditions:
    print(f"\n=== TESTING COMBINED OR QUERY ===")
    search_query = {"$or": search_conditions}
    try:
        results = list(mongo.db.hostels.find(search_query))
        print(f"Combined query: {len(results)} results")
        for result in results:
            print(f"  - {result.get('name', 'N/A')}")
    except Exception as e:
        print(f"Combined query ERROR: {e}")
