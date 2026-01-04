#!/usr/bin/env python3
"""
Final verification of the lightbox fix
"""

import requests
import json

def final_verification():
    """Final verification that the fix works"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Final verification...")
        response = requests.get(url)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for data-photos with single quotes
            start = html.find("data-photos='") + len("data-photos='")
            end = html.find("'", start)
            
            if start > -1 and end > start:
                photos_data = html[start:end]
                print(f"✅ Found data-photos with single quotes")
                print(f"✅ Raw data length: {len(photos_data)}")
                
                try:
                    photos = json.loads(photos_data)
                    print(f"✅ Successfully parsed {len(photos)} photos")
                    
                    if len(photos) > 0:
                        print(f"✅ First photo: {photos[0][:50]}...")
                        print("🎉 LIGHTBOX FIX SUCCESSFUL!")
                        print("📸 The lightbox should now work when clicking on images")
                        return True
                    else:
                        print("❌ No photos found")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    
            else:
                print("❌ data-photos attribute not found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    final_verification()
