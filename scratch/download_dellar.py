import os
import re
import urllib.request
import gdown

print("=== DELLAR Downloader ===")
folder_id = "1TuBdM5CUznobaf65eL4UIjytFvtlzcrr"
url = f"https://drive.google.com/drive/folders/{folder_id}"

target_dir = os.path.join(os.getcwd(), "backend", "dellar")
os.makedirs(target_dir, exist_ok=True)

print(f"Downloading Google Drive folder {folder_id} into {target_dir}...")

# Use gdown folder download
try:
    gdown.download_folder(id=folder_id, output=target_dir, quiet=False, use_cookies=False)
    print("Download completed successfully!")
except Exception as e:
    print(f"gdown error: {e}")

# Check files in target_dir
files_downloaded = []
for root, dirs, files in os.walk(target_dir):
    for file in files:
        rel_path = os.path.relpath(os.path.join(root, file), target_dir)
        files_downloaded.append(rel_path)

print(f"Total files downloaded in {target_dir}: {len(files_downloaded)}")
for f in files_downloaded[:30]:
    print(f"  - {f}")
