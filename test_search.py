import requests
import json

# Test the search API
try:
    response = requests.post('http://localhost:5000/api/hostels/search', 
                           json={'query': 'surat', 'property_type': 'all'},
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        print('Search API Status: Success')
        print(f'Found {data.get("count", 0)} results')
        for hostel in data.get('data', [])[:3]:
            print(f'  - {hostel.get("name", "N/A")} in {hostel.get("city", "N/A")}')
    else:
        print(f'Search API Error: {response.status_code}')
        print(response.text)
        
except Exception as e:
    print(f'Error testing search API: {e}')
