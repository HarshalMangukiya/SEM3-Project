#!/usr/bin/env python3
"""
Test if the image URLs are accessible
"""

import requests

def test_image_urls():
    """Test if the Cloudinary image URLs are accessible"""
    
    # Sample URLs from the debug output
    test_urls = [
        "https://res.cloudinary.com/doe8ybkzu/image/upload/v1767511153/stayfinder/hostels/j8r6u4syfycco1p1qmii.jpg",
        "https://res.cloudinary.com/doe8ybkzu/image/upload/v1767511154/stayfinder/hostels/eq4xeqlqy0zfgod8sd4q.jpg"
    ]
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            response = requests.head(url, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Content-Length: {response.headers.get('Content-Length', 'N/A')}")
            
            if response.status_code == 200:
                print("✅ URL is accessible")
            else:
                print("❌ URL returned error")
                
        except Exception as e:
            print(f"❌ Error accessing URL: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_image_urls()
