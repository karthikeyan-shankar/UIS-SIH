import json
import urllib.request
import os

filepath = r'C:\Users\karth\.gemini\antigravity\brain\3326fe28-57ed-469a-af0f-d3fb07a51d7b\.system_generated\steps\300\output.txt'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

screens = data.get('design', {}).get('screens', [])
for s in screens:
    url = s.get('htmlCode', {}).get('downloadUrl')
    if url:
        print(f"Downloading {s['id']}...")
        urllib.request.urlretrieve(url, f"stitch_{s['id']}.html")
        print(f"Saved stitch_{s['id']}.html")
