import requests
import re
import json

folder_id = "1TuBdM5CUznobaf65eL4UIjytFvtlzcrr"
url = f"https://drive.google.com/drive/folders/{folder_id}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

resp = requests.get(url, headers=headers)
print("Folder Page Status:", resp.status_code)
html = resp.text

# Extract initial data / JSON embedded in Google Drive page
with open("scratch/gdrive_folder_page.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Saved HTML to scratch/gdrive_folder_page.html")

# Look for AF_initDataCallback or window._DRIVE_data
matches = re.findall(r'AF_initDataCallback\(({.*?})\);', html, re.DOTALL)
print(f"Found {len(matches)} AF_initDataCallback blocks")

for i, m in enumerate(matches):
    if "1TuBdM5CUznobaf65eL4UIjytFvtlzcrr" in m or "sllsm" in m or "slds" in m or ".py" in m:
        print(f"Block {i} mentions target files!")
        with open(f"scratch/af_data_{i}.json", "w", encoding="utf-8") as f:
            f.write(m)
