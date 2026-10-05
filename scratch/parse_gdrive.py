import re
import json

with open("scratch/gdrive_page.html", "r", encoding="utf-8") as f:
    html = f.read()

print("HTML Length:", len(html))

# Search for file names and IDs in GDrive initial data
# GDrive embeds file data in JS arrays: ["item_id", ["file_name", ...]]
items = re.findall(r'\["([a-zA-Z0-9_-]{28,40})",\["([^"]+)"', html)
print(f"Found {len(items)} items using pattern 1")

# Alternative pattern for file listings in GDrive HTML
items2 = re.findall(r'data-id="([a-zA-Z0-9_-]{28,40})"[^>]*data-name="([^"]+)"', html)
print(f"Found {len(items2)} items using pattern 2")

# Search for any strings ending with .py, .md, .txt, .json, .sh
code_files = re.findall(r'([a-zA-Z0-9_-]+\.(?:py|md|json|txt|csv|yaml|yml|sh))', html)
print(f"Found {len(set(code_files))} code file names mentioned in HTML:")
for f in sorted(list(set(code_files)))[:40]:
    print("  -", f)
