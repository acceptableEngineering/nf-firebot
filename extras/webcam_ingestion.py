"""
Manually run this script to fetch fresh data from alertwildfire.org which is then
boiled down and saved to ./alertwildfire_processed.json and used by ../firebot.py
"""
import json
import os
import requests

cams_list = []
exec_path = os.path.dirname(os.path.realpath(__file__))

payload = requests.get(
    "https://s3-us-west-2.amazonaws.com/alertwildfire-data-public/all_cameras-v2.json",
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Cache-Control": "no-cache",
        "Origin": "https://www.alertwildfire.org",
        "Pragma": "no-cache",
        "Referer": "https://www.alertwildfire.org/"
    }
)

for item in json.loads(payload.content)['features']:
    cams_list.append({
        "name": item['properties']['name'],
        "id": item['properties']['id'],
        "lat": item['geometry']['coordinates'][1],
        "lon": item['geometry']['coordinates'][0]
    })

with open(exec_path + '/alertwildfire_processed.json', 'w', encoding='utf8') as fopen:
    fopen.write(json.dumps({
        "cameras": cams_list
    }))
