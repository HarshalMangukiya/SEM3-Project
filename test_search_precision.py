import requests
import json

def test_search_precision():
    """Test search precision with short queries"""
    
    test_cases = [
        {"query": "sa", "should_not_contain": ["sardardham"]},
        {"query": "surat", "should_contain": ["sp"]},
        {"query": "ahmedabad", "should_contain": ["sardardham", "sp hostel"]},
        {"query": "sp", "should_contain": ["sp hostel", "sp"]},
    ]
    
    for test_case in test_cases:
        query = test_case["query"]
        print(f"\nTesting search for: '{query}'")
        
        try:
            response = requests.post('http://localhost:5000/api/hostels/search', 
                                   json={'query': query, 'property_type': 'all'},
                                   headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Found {data.get('count', 0)} results")
                
                hostel_names = [hostel.get('name', '').lower() for hostel in data.get('data', [])]
                print(f"  Results: {hostel_names}")
                
                # Check should not contain
                if "should_not_contain" in test_case:
                    for bad_name in test_case["should_not_contain"]:
                        if bad_name.lower() in hostel_names:
                            print(f"  ❌ ERROR: Found '{bad_name}' which should not appear")
                        else:
                            print(f"  ✅ GOOD: '{bad_name}' correctly not found")
                
                # Check should contain
                if "should_contain" in test_case:
                    for good_name in test_case["should_contain"]:
                        found = any(good_name.lower() in name for name in hostel_names)
                        if found:
                            print(f"  ✅ GOOD: Found expected result containing '{good_name}'")
                        else:
                            print(f"  ❌ ERROR: Expected to find '{good_name}' but didn't")
            else:
                print(f"  ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Test Error: {e}")

if __name__ == "__main__":
    test_search_precision()
