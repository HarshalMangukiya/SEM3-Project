#!/usr/bin/env python3
"""
Simple verification of the fix
"""

import requests
import json

def verify_fix():
    """Check if the data-photos attribute is properly set"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Fetching detail page...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Page loaded successfully")
            
            html = response.text
            
            # Look for data-photos attribute
            if 'data-photos=' in html:
                print("✅ Found data-photos attribute")
                
                # Extract the data-photos value
                start = html.find('data-photos="') + len('data-photos="')
                end = html.find('"', start)
                
                if start > -1 and end > start:
                    photos_data = html[start:end]
                    print(f"Raw data: {photos_data[:100]}...")
                    
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
                                return True
                            else:
                                print("❌ Photos are not valid URLs")
                        else:
                            print("❌ Photos array is empty")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse JSON: {e}")
                        
                else:
                    print("❌ Could not extract data-photos value")
            else:
                print("❌ data-photos attribute not found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    verify_fix()
