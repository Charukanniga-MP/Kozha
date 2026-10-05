import urllib.request
import re
import json
import os
import sys

print("=== Fetching DELLAR Sources Directly ===")
folder_id = "1TuBdM5CUznobaf65eL4UIjytFvtlzcrr"
url = f"https://drive.google.com/drive/folders/{folder_id}"

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

try:
    html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
    print(f"Fetched HTML, length: {len(html)}")
    
    # Save HTML to scratch for inspection
    with open("scratch/gdrive_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved page to scratch/gdrive_page.html")

    # Find JSON data structures embedded in the GDrive page
    matches = re.findall(r'window\[\'_AF_initDataCallback\'\]\s*=\s*(\{.*?\});', html, re.DOTALL)
    print(f"Found {len(matches)} data callbacks")
    
    # Extract file IDs and names from JS variables
    file_tuples = re.findall(r'\[\"([a-zA-Z0-9_-]{28,40})\",\[\"([^\"]+)\"', html)
    print(f"Extracted {len(file_tuples)} potential file ID-name pairs:")
    for fid, fname in file_tuples[:30]:
        print(f"  ID: {fid}  ->  Name: {fname}")

except Exception as e:
    print(f"Error fetching Google Drive page: {e}")
