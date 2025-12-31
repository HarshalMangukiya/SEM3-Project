import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

# Test the detail page route
def test_detail_page():
    # Connect to MongoDB to get a real hostel ID
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['stayfinder']
        
        # Get a sample hostel
        hostel = db.hostels.find_one()
        if hostel:
            hostel_id = str(hostel['_id'])
            print(f"Found hostel: {hostel.get('name', 'Unknown')} with ID: {hostel_id}")
            
            # Test the detail page
            url = f"http://localhost:5003/hostel/{hostel_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                # Check if data-hostel-id is in the response
                if f'data-hostel-id="{hostel_id}"' in response.text:
                    print("✅ data-hostel-id is properly set in template")
                else:
                    print("❌ data-hostel-id is NOT set in template")
                    print("Looking for data-hostel-id attribute...")
                    
                    # Find the data-hostel-id in response
                    import re
                    matches = re.findall(r'data-hostel-id="([^"]*)"', response.text)
                    if matches:
                        print(f"Found data-hostel-id values: {matches}")
                    else:
                        print("No data-hostel-id attributes found")
                        
            else:
                print(f"❌ Failed to load detail page: {response.status_code}")
        else:
            print("❌ No hostels found in database")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_detail_page()
