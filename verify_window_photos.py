#!/usr/bin/env python3
"""
Verify that window.allPhotos is working
"""

import requests

def verify_window_photos():
    """Check if window.allPhotos is properly set"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Fetching detail page...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Page loaded successfully")
            
            html = response.text
            
            # Look for window.allPhotos script
            if 'window.allPhotos' in html:
                print("✅ Found window.allPhotos script")
                
                # Extract the script content
                start = html.find('window.allPhotos = ')
                end = html.find(';', start)
                
                if start > -1 and end > start:
                    script_content = html[start:end]
                    print(f"Script content: {script_content}")
                    
                    # Check if it contains valid JSON
                    if '[' in script_content and ']' in script_content:
                        print("✅ Script contains JSON array")
                        
                        # Count the photos
                        photo_count = script_content.count('https://')
                        print(f"✅ Found {photo_count} photo URLs")
                        
                        if photo_count > 0:
                            print("🎉 SUCCESS! The lightbox should now work.")
                            return True
                        else:
                            print("❌ No photo URLs found")
                    else:
                        print("❌ Script doesn't contain valid JSON")
                else:
                    print("❌ Could not extract script content")
            else:
                print("❌ window.allPhotos script not found")
                
                # Look for any script tags
                if '<script>' in html:
                    print("ℹ️  Script tags found but not window.allPhotos")
                else:
                    print("❌ No script tags found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    verify_window_photos()
