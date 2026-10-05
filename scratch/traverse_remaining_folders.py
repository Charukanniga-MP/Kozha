import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def unescape_string(s):
    return s.replace('\\x5b', '[').replace('\\x22', '"').replace('\\x5d', ']').replace('\\x2f', '/').replace('\\\\', '\\')

def get_folder_items(folder_id):
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return []
    html = unescape_string(resp.text)
    pattern = r'\["([a-zA-Z0-9_-]{25,45})",\["([a-zA-Z0-9_-]{25,45})"\]\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"'
    matches = re.findall(pattern, html)
    items = []
    for fid, pid, name, mime in matches:
        items.append({"id": fid, "parent": pid, "name": name, "mime": mime})
    return items

other_folders = {
    "demo": "1-pU1_OS53gk6iTYvbF9qCZfsph7tNyJ7",
    "plots": "19CdQY2BCeGYXWwTMV0ah785x9-pOt0rD",
    "research": "1Hu2yo0edGssRrhfDduhU6ivwcpuWlVDp",
    "scripts": "1jknnbymV_uKMXGEZdLTHy0stX2xi0jjW",
}

all_drive_files = {}

for fname, fid in other_folders.items():
    print(f"\n=== Fetching {fname} folder ({fid}) ===")
    items = get_folder_items(fid)
    for item in items:
        print(f"{fname} item: {item['name']:35s} | ID: {item['id']} | type: {item['mime']}")
        all_drive_files[f"{fname}/{item['name']}"] = item['id']
