import requests
import json

# Test the college search API
def test_college_search():
    # Test 1: Get colleges
    print("=== Testing /api/colleges ===")
    try:
        response = requests.get('http://localhost:5000/api/colleges')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"College count: {data.get('count')}")
            
            # Find L.D. College
            colleges = data.get('data', [])
            ld_college = None
            for college in colleges:
                if 'L.D. College' in college['Name']:
                    ld_college = college
                    break
            
            if ld_college:
                print(f"Found L.D. College: {ld_college['Name']}")
                print(f"Coordinates: {ld_college['Latitude']}, {ld_college['Longitude']}")
                
                # Test 2: Search hostels near L.D. College
                print("\n=== Testing /api/hostels/search/college ===")
                search_response = requests.post(
                    'http://localhost:5000/api/hostels/search/college',
                    json={
                        'college_name': 'L.D. College Of Engineering',
                        'property_type': 'all',
                        'max_distance': 5
                    }
                )
                print(f"Search Status: {search_response.status_code}")
                print(f"Search Response: {search_response.text}")
                
            else:
                print("L.D. College not found in database")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_college_search()
