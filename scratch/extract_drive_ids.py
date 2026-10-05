import json
import re
import os

def extract_files_from_data():
    files_found = {} # id -> (name, mimeType, parent_id)
    
    for filename in os.listdir("scratch"):
        if filename.startswith("af_data_") or filename == "gdrive_folder_page.html":
            filepath = os.path.join("scratch", filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find all file entry patterns in Google Drive JSON
            # Pattern in Google Drive: [file_id, file_name, mime_type, ...]
            # File ID is usually 28-40 chars base64url-like: [a-zA-Z0-9_-]{25,45}
            matches = re.findall(r'\["([a-zA-Z0-9_-]{25,45})",\s*"([^"]+)",\s*"([^"]+)"', content)
            for file_id, name, mime in matches:
                files_found[file_id] = (name, mime)

            # Also search for standalone file patterns like ["id", "name.py"]
            matches_py = re.findall(r'\["([a-zA-Z0-9_-]{25,45})",\s*"([^"]+\.(?:py|md|txt|json|yml|yaml|sh|csv|png|jpg|ipynb|zip|gz|tar))"', content)
            for file_id, name in matches_py:
                files_found[file_id] = (name, "file")

    print(f"Total Unique Items Extracted: {len(files_found)}")
    for fid, info in files_found.items():
        print(f"ID: {fid} | Name: {info[0]} | Type: {info[1]}")

    with open("scratch/extracted_drive_items.json", "w", encoding="utf-8") as f:
        json.dump(files_found, f, indent=2)

if __name__ == "__main__":
    extract_files_from_data()
