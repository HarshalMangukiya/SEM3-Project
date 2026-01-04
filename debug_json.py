#!/usr/bin/env python3
"""
Debug the JSON issue
"""

import requests

def debug_json():
    """Debug the JSON parsing issue"""
    
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        print("🔍 Fetching detail page...")
        response = requests.get(url)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for data-photos attribute
            start = html.find('data-photos="') + len('data-photos="')
            end = html.find('"', start)
            
            if start > -1 and end > start:
                photos_data = html[start:end]
                print(f"Raw data-photos: {repr(photos_data)}")
                print(f"Length: {len(photos_data)}")
                print(f"First 100 chars: {photos_data[:100]}")
                print(f"Last 100 chars: {photos_data[-100:]}")
                
                # Check if it's valid JSON
                import json
                try:
                    photos = json.loads(photos_data)
                    print(f"✅ Valid JSON with {len(photos)} items")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Error: {e}")
                    print(f"Error position: {e.pos if hasattr(e, 'pos') else 'N/A'}")
                    
                    # Show character around error position
                    if hasattr(e, 'pos') and e.pos < len(photos_data):
                        start_pos = max(0, e.pos - 20)
                        end_pos = min(len(photos_data), e.pos + 20)
                        print(f"Context around error: {repr(photos_data[start_pos:end_pos])}")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_json()
