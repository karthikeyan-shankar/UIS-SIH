import urllib.request
import json

with open('screens.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for s in data.get('screens', []):
    if s['name'].endswith('7de8a2b77bf4434299b8edddf373080f'):
        url = s.get('htmlCode', {}).get('downloadUrl')
        print(f"Downloading...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res, open('stitch_light_ui.html', 'wb') as out:
            out.write(res.read())
        print('Saved to stitch_light_ui.html')
