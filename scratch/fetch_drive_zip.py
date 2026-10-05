import urllib.request
import urllib.parse
import re
import os
import sys

file_id = "1QnAniCuV1oW6rK4CU3Tc4HgmO55bjo"
url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

print(f"Targeting URL: {url}")

req = urllib.request.Request(
    url,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        content_type = resp.headers.get('Content-Type', '')
        content_disp = resp.headers.get('Content-Disposition', '')
        print("Status:", resp.status)
        print("Content-Type:", content_type)
        print("Content-Disposition:", content_disp)

        if 'text/html' in content_type:
            html = resp.read().decode('utf-8', errors='ignore')
            print("HTML Length:", len(html))
            # Save HTML to inspect
            with open("scratch/drive_warning.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Saved HTML to scratch/drive_warning.html")

            # Extract form action or download link
            forms = re.findall(r'<form[^>]+action="([^"]+)"[^>]*>(.*?)</form>', html, re.DOTALL)
            print("Found forms:", len(forms))
            for action, form_body in forms:
                print("Action:", action)
                inputs = re.findall(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', form_body)
                print("Inputs:", inputs)
                
                # Build POST or GET request
                params = {k: v for k, v in inputs}
                if action.startswith('/'):
                    action_url = "https://drive.usercontent.google.com" + action
                else:
                    action_url = action

                print(f"Executing form action to: {action_url} with params {params}")
                data = urllib.parse.urlencode(params).encode('utf-8')
                req2 = urllib.request.Request(action_url, data=data, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })
                with urllib.request.urlopen(req2) as resp2:
                    print("Form Response Status:", resp2.status)
                    print("Form Response Content-Type:", resp2.headers.get('Content-Type'))
                    print("Form Response Content-Disposition:", resp2.headers.get('Content-Disposition'))
                    out_path = "C:/Users/bc/Downloads/dellar_drive_archive.zip"
                    with open(out_path, 'wb') as out_f:
                        chunk_size = 1024 * 1024
                        total = 0
                        while True:
                            chunk = resp2.read(chunk_size)
                            if not chunk:
                                break
                            out_f.write(chunk)
                            total += len(chunk)
                            print(f"Downloaded {total} bytes...")
                    print(f"Successfully downloaded {total} bytes to {out_path}")
        else:
            out_path = "C:/Users/bc/Downloads/dellar_drive_archive.zip"
            with open(out_path, 'wb') as out_f:
                chunk_size = 1024 * 1024
                total = 0
                while True:
                    chunk = resp2.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    total += len(chunk)
                    print(f"Downloaded {total} bytes...")
            print(f"Successfully downloaded {total} bytes to {out_path}")
except Exception as e:
    print("Error during download:", e)
    import traceback
    traceback.print_exc()
