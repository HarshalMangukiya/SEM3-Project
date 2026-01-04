#!/usr/bin/env python3
"""
Test the tojson filter
"""

from flask import Flask, render_template_string
import json

app = Flask(__name__)

# Test template
test_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Test tojson</title>
</head>
<body>
    <div class="container" data-photos="{{ all_photos|tojson|safe }}">
        <h1>Test</h1>
    </div>
    
    <script>
        var photosData = document.querySelector('.container').getAttribute('data-photos');
        console.log('Raw photos data:', photosData);
        console.log('Type:', typeof photosData);
        console.log('Length:', photosData.length);
        
        try {
            var photos = JSON.parse(photosData);
            console.log('Parsed photos:', photos);
            console.log('Length:', photos.length);
        } catch (e) {
            console.error('JSON parse error:', e);
        }
    </script>
</body>
</html>
"""

@app.route('/test')
def test():
    # Sample data like the real hostel
    all_photos = [
        "https://res.cloudinary.com/doe8ybkzu/image/upload/v1767511153/stayfinder/hostels/j8r6u4syfycco1p1qmii.jpg",
        "https://res.cloudinary.com/doe8ybkzu/image/upload/v1767511154/stayfinder/hostels/eq4xeqlqy0zfgod8sd4q.jpg",
        "https://res.cloudinary.com/doe8ybkzu/image/upload/v1767511154/stayfinder/hostels/n0kdmyk1ezihefriqzrj.jpg"
    ]
    
    print(f"DEBUG: all_photos length: {len(all_photos)}")
    print(f"DEBUG: all_photos type: {type(all_photos)}")
    print(f"DEBUG: all_photos content: {all_photos}")
    
    return render_template_string(test_template, all_photos=all_photos)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
