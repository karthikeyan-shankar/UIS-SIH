import urllib.request
import json
import os

api_key = os.getenv('STITCH_API_KEY', 'YOUR_STITCH_API_KEY')

req = urllib.request.Request(
    'https://stitch.googleapis.com/v1/projects/6986385158396558546',
    headers={'X-Goog-Api-Key': api_key}
)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())

    for s in data.get('design', {}).get('screens', []):
        if 'Command Center' in s.get('title', ''):
            print(f"Found screen: {s['title']} - ID: {s['id']}")
            url = s.get('htmlCode', {}).get('downloadUrl')
            print(url)
            if url:
                req_html = urllib.request.Request(url)
                with urllib.request.urlopen(req_html) as html_res:
                    with open('new_ui.html', 'wb') as f:
                        f.write(html_res.read())
                print("Saved to new_ui.html")
except Exception as e:
    print(f"Set STITCH_API_KEY environment variable to use this utility script: {e}")
