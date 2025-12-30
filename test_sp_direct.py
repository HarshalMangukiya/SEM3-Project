import requests
import json

# Test direct API call for 'sp'
try:
    response = requests.post('http://localhost:5000/api/hostels/search', 
                           json={'query': 'sp', 'property_type': 'all'},
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        print(f"Direct API test for 'sp':")
        print(f"  Status: Success")
        print(f"  Found {data.get('count', 0)} results")
        print(f"  Results: {[hostel.get('name', 'N/A') for hostel in data.get('data', [])]}")
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")
