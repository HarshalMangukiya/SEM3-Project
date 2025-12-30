from app import mongo
from datetime import datetime

# Check existing hostels
hostels = list(mongo.db.hostels.find())
print(f'Number of hostels: {len(hostels)}')

if len(hostels) == 0:
    print('No hostels found. Adding sample data...')
    
    # Sample hostels for testing
    sample_hostels = [
        {
            "name": "Surat Boys Hostel",
            "city": "Surat",
            "location": "Adajan",
            "price": 5000,
            "original_price": 6000,
            "image": "https://via.placeholder.com/400x300?text=Surat+Boys+Hostel",
            "photos": [],
            "desc": "Comfortable boys hostel in Surat with all modern amenities",
            "type": "Boys",
            "amenities": ["WiFi", "AC", "TV", "Laundry", "Food"],
            "appliances": [],
            "room_types": [],
            "longitude": 72.8311,
            "latitude": 21.1702,
            "neighborhood_highlights": [],
            "contact_phone": "9876543210",
            "contact_email": "suratboyshostel@example.com",
            "address": "Adajan, Surat, Gujarat",
            "property_type": "Hostel",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Surat Girls PG",
            "city": "Surat", 
            "location": "Piplod",
            "price": 4500,
            "original_price": 5500,
            "image": "https://via.placeholder.com/400x300?text=Surat+Girls+PG",
            "photos": [],
            "desc": "Safe and secure girls PG in Surat with 24/7 security",
            "type": "Girls",
            "amenities": ["WiFi", "AC", "TV", "Laundry", "Food", "Security"],
            "appliances": [],
            "room_types": [],
            "longitude": 72.8311,
            "latitude": 21.1702,
            "neighborhood_highlights": [],
            "contact_phone": "9876543211",
            "contact_email": "suratgirlspg@example.com",
            "address": "Piplod, Surat, Gujarat",
            "property_type": "PG",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Mumbai Student Apartment",
            "city": "Mumbai",
            "location": "Andheri",
            "price": 8000,
            "original_price": 10000,
            "image": "https://via.placeholder.com/400x300?text=Mumbai+Apartment",
            "photos": [],
            "desc": "Fully furnished apartment for students in Mumbai",
            "type": "Co-ed",
            "amenities": ["WiFi", "AC", "TV", "Laundry", "Gym", "Parking"],
            "appliances": [],
            "room_types": [],
            "longitude": 72.8311,
            "latitude": 19.0760,
            "neighborhood_highlights": [],
            "contact_phone": "9876543212",
            "contact_email": "mumbaiapartment@example.com",
            "address": "Andheri, Mumbai, Maharashtra",
            "property_type": "Apartment",
            "created_at": datetime.utcnow()
        },
        {
            "name": "Delhi University Hostel",
            "city": "Delhi",
            "location": "North Campus",
            "price": 6000,
            "original_price": 7000,
            "image": "https://via.placeholder.com/400x300?text=Delhi+Hostel",
            "photos": [],
            "desc": "Premier hostel near Delhi University with excellent facilities",
            "type": "Boys",
            "amenities": ["WiFi", "AC", "TV", "Laundry", "Food", "Library"],
            "appliances": [],
            "room_types": [],
            "longitude": 77.2090,
            "latitude": 28.6139,
            "neighborhood_highlights": [],
            "contact_phone": "9876543213",
            "contact_email": "delhihostel@example.com",
            "address": "North Campus, Delhi",
            "property_type": "Hostel",
            "created_at": datetime.utcnow()
        }
    ]
    
    # Insert sample hostels
    result = mongo.db.hostels.insert_many(sample_hostels)
    print(f'Added {len(result.inserted_ids)} sample hostels')
else:
    print('Existing hostels:')
    for hostel in hostels[:5]:
        print(f'  - {hostel.get("name", "N/A")} in {hostel.get("city", "N/A")} ({hostel.get("property_type", "N/A")})')
