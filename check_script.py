#!/usr/bin/env python3
"""
Check the actual script content
"""

import requests

def check_script():
    url = "http://127.0.0.1:5000/hostel/695a14783201a936ebce1e48"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for the container div
            start = html.find('<div class="container mt-5"')
            if start > -1:
                # Get the next 500 characters after the container
                content = html[start:start+500]
                print("Container content:")
                print(content)
            else:
                print("Container not found")
                
        else:
            print(f"Failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_script()
