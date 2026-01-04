#!/usr/bin/env python3
"""
Check the debug info on the page
"""

import requests

def check_debug():
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for debug info
            if 'DEBUG INFO' in html:
                start = html.find('DEBUG INFO')
                end = html.find('</div>', start) + 6
                
                debug_section = html[start:end]
                print("Found debug section:")
                print(debug_section)
            else:
                print("No debug section found")
                
                # Look for data-photos
                start = html.find('data-photos="') + len('data-photos="')
                end = html.find('"', start)
                
                if start > -1 and end > start:
                    photos_data = html[start:end]
                    print(f"data-photos: {repr(photos_data)}")
                    print(f"Length: {len(photos_data)}")
                    
                    # Look for more context
                    context_start = max(0, start - 100)
                    context_end = min(len(html), end + 100)
                    context = html[context_start:context_end]
                    print(f"Context: {repr(context)}")
        else:
            print(f"Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_debug()
