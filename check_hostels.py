from flask import Flask
from flask_pymongo import PyMongo

# Connect to database
app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Stayfinder'
mongo = PyMongo(app)

# Get all hostels
hostels = list(mongo.db.hostels.find())
print(f'Total hostels in database: {len(hostels)}')

# Check how many have coordinates
with_coords = [h for h in hostels if h.get('latitude') and h.get('longitude')]
print(f'Hostels with coordinates: {len(with_coords)}')

# Show first few hostels with their coordinate status
for i, hostel in enumerate(hostels[:5]):
    print(f'Hostel {i+1}: {hostel.get("name", "Unknown")}')
    print(f'  Has latitude: {bool(hostel.get("latitude"))}')
    print(f'  Has longitude: {bool(hostel.get("longitude"))}')
    print(f'  City: {hostel.get("city", "Unknown")}')
    print()

# If no hostels have coordinates, let's add some sample coordinates for Ahmedabad hostels
if len(with_coords) == 0:
    print("No hostels have coordinates. Adding sample coordinates for Ahmedabad hostels...")
    
    # Sample coordinates around Ahmedabad
    sample_coords = [
        {"name": "Test Hostel 1", "lat": 23.03423441, "lon": 72.54660545},
        {"name": "Test Hostel 2", "lat": 23.04074287, "lon": 72.54267832},
        {"name": "Test Hostel 3", "lat": 23.0385313, "lon": 72.55444507},
    ]
    
    for i, hostel in enumerate(hostels[:3]):
        if hostel.get('city', '').lower() == 'ahmedabad':
            coord = sample_coords[i % len(sample_coords)]
            mongo.db.hostels.update_one(
                {"_id": hostel["_id"]},
                {"$set": {
                    "latitude": coord["lat"],
                    "longitude": coord["lon"]
                }}
            )
            print(f"Added coordinates to: {hostel.get('name', 'Unknown')}")

print("Check complete!")
