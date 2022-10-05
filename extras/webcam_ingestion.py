"""
Manually run this script to fetch fresh data from alertca.live which is then
boiled down and saved to ./alertca_processed.json and used by ../firebot.py
"""
import json
import os
import requests

cams_list = []
exec_path = os.path.dirname(os.path.realpath(__file__))

payload = requests.get(
    "https://alertca.live/api/getCameraDataByType?type=both"
)

items = json.loads(payload.content)['data']

for item in items:
    cams_list.append({
        "name": items[item]['camName'],
        "id": int(items[item]['camId']),
        "lat": items[item]['camLat'],
        "lon": items[item]['camLon']
    })

with open(exec_path + '/alertca_processed.json', 'w', encoding='utf8') as fopen:
    fopen.write(json.dumps({
        "cameras": cams_list
    }))
