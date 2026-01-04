#!/usr/bin/env python3
"""
Debug the actual hostel data being sent to the template
"""

import requests
import json

def debug_hostel_data():
    """Debug what data is being sent to the template"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Fetching detail page...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Page loaded successfully")
            
            html = response.text
            
            # Look for hostel name
            if '<h1' in html:
                start = html.find('<h1')
                end = html.find('</h1>', start) + 5
                h1_tag = html[start:end]
                print(f"Hostel name found: {h1_tag}")
            
            # Look for main photo
            if 'mainPhoto' in html:
                start = html.find('id="mainPhoto" src="') + len('id="mainPhoto" src="')
                end = html.find('"', start)
                if start > -1 and end > start:
                    main_photo = html[start:end]
                    print(f"Main photo: {main_photo}")
            
            # Look for thumbnails
            thumbnails = html.count('class="thumbnail"')
            print(f"Number of thumbnails found: {thumbnails}")
            
            # Look for data-photos again
            start = html.find('data-photos="') + len('data-photos="')
            end = html.find('"', start)
            
            if start > -1 and end > start:
                photos_data = html[start:end]
                print(f"Data-photos: {photos_data}")
                
                if photos_data == '[]':
                    print("❌ Photos array is empty - this is the problem!")
                    
                    # Let's check if there are photos in the HTML but not in the data-photos
                    if 'thumbnail' in html:
                        print("🤔 Thumbnails exist in HTML but data-photos is empty")
                        print("This suggests the template logic has an issue")
                    
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_hostel_data()
