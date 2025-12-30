import requests
import json

# Test the booking API
url = "http://localhost:5003/test-token"
response = requests.post(url)
token_data = response.json()
print("Token response:", token_data)

if token_data['success']:
    token = token_data['token']
    
    # Test booking
    booking_url = "http://localhost:5003/api/bookings/request"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    booking_data = {
        'hostel_id': 'test_hostel_id',
        'room_id': 'double_regular',
        'property_type': 'Double Sharing',
        'facility': 'Regular'
    }
    
    print("\nSending booking request...")
    print("Headers:", headers)
    print("Data:", booking_data)
    
    response = requests.post(booking_url, headers=headers, json=booking_data)
    print("\nBooking response status:", response.status_code)
    print("Booking response data:", response.json())
else:
    print("Failed to get token")
