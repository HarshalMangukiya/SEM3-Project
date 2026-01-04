#!/usr/bin/env python3
"""
Verify that the fix works by checking the rendered HTML
"""

import requests
import json
from bs4 import BeautifulSoup

def verify_fix():
    """Check if the data-photos attribute is properly set"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Fetching detail page...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Page loaded successfully")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the container with data-photos
            container = soup.find('div', {'class': 'container'})
            
            if container and container.get('data-photos'):
                photos_data = container.get('data-photos')
                print("✅ Found data-photos attribute")
                
                try:
                    photos = json.loads(photos_data)
                    print(f"✅ Successfully parsed {len(photos)} photos")
                    
                    if len(photos) > 0:
                        print("✅ Photos array is not empty")
                        print(f"First photo: {photos[0][:50]}...")
                        
                        # Check if photos are valid URLs
                        valid_photos = 0
                        for photo in photos:
                            if photo.startswith('http'):
                                valid_photos += 1
                        
                        print(f"✅ {valid_photos}/{len(photos)} photos are valid URLs")
                        
                        if valid_photos > 0:
                            print("🎉 FIX SUCCESSFUL! The lightbox should now work.")
                        else:
                            print("❌ Photos are not valid URLs")
                    else:
                        print("❌ Photos array is empty")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Raw data: {photos_data[:100]}...")
                    
            else:
                print("❌ data-photos attribute not found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_fix()
