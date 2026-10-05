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
        print(f"Error fetching folder {folder_id}: {resp.status_code}")
        return []
    
    html = unescape_string(resp.text)
    pattern = r'\["([a-zA-Z0-9_-]{25,45})",\["([a-zA-Z0-9_-]{25,45})"\]\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"'
    matches = re.findall(pattern, html)
    items = []
    for fid, pid, name, mime in matches:
        items.append({"id": fid, "parent": pid, "name": name, "mime": mime})
    return items

# 1. Fetch src folder (1mNVuasArYC1RjP-IaIOx2m22zPPKVyo0)
print("=== Fetching src folder ===")
src_items = get_folder_items("1mNVuasArYC1RjP-IaIOx2m22zPPKVyo0")
for item in src_items:
    print(f"src item: {item['name']:35s} | ID: {item['id']} | type: {item['mime']}")

# Find slds_core folder in src
slds_core_id = None
for item in src_items:
    if item['name'] == 'slds_core':
        slds_core_id = item['id']

if slds_core_id:
    print(f"\n=== Fetching slds_core folder ({slds_core_id}) ===")
    slds_items = get_folder_items(slds_core_id)
    for item in slds_items:
        print(f"slds_core item: {item['name']:35s} | ID: {item['id']} | type: {item['mime']}")

# 2. Fetch tests folder (1bFuyMJ1Z9nmtxrRl1eWHNe530TBNJW5B)
print("\n=== Fetching tests folder ===")
test_items = get_folder_items("1bFuyMJ1Z9nmtxrRl1eWHNe530TBNJW5B")
for item in test_items:
    print(f"tests item: {item['name']:35s} | ID: {item['id']} | type: {item['mime']}")
