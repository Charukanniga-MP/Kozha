import re
import json

with open("scratch/gdrive_folder_page.html", "r", encoding="utf-8") as f:
    html = f.read()

# Decode unicode/hex escapes like \x5b \x22 \x5d
def unescape_string(s):
    s = s.replace('\\x5b', '[').replace('\\x22', '"').replace('\\x5d', ']').replace('\\x2f', '/')
    s = s.replace('\\\\', '\\')
    return s

decoded_html = unescape_string(html)

with open("scratch/gdrive_decoded.html", "w", encoding="utf-8") as f:
    f.write(decoded_html)

# Now match patterns like ["FILE_ID",["PARENT_ID"],"FILE_NAME","MIME_TYPE"]
pattern = r'\["([a-zA-Z0-9_-]{25,45})",\["([a-zA-Z0-9_-]{25,45})"\]\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"'
matches = re.findall(pattern, decoded_html)

print(f"Found {len(matches)} files/folders with parent relationships!")

drive_items = {}
for file_id, parent_id, name, mime in matches:
    drive_items[file_id] = {
        "id": file_id,
        "parent": parent_id,
        "name": name,
        "mime": mime
    }
    print(f"Name: {name:35s} | ID: {file_id} | Parent: {parent_id} | Type: {mime}")

with open("scratch/parsed_drive_items.json", "w", encoding="utf-8") as f:
    json.dump(drive_items, f, indent=2)
