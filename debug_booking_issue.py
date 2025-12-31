import requests
import json

# Test the booking API endpoint
def test_booking_api():
    url = "http://localhost:5003/api/bookings/request"
    
    # Test data that should be sent from frontend
    test_data = {
        "hostel_id": "test_hostel_id",
        "room_id": "test_room_id", 
        "property_type": "Single Sharing",
        "facility": "Regular"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test_token"
    }
    
    try:
        print("Testing booking API endpoint...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("Connection error - server might not be running")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_booking_api()
