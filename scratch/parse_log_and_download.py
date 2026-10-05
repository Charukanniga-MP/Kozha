import re
import os
import gdown

log_path = r"C:\Users\bc\.gemini\antigravity-ide\brain\d4f6bb2c-ce60-4119-9efd-5a9e6008e15b\.system_generated\tasks\task-198.log"

if not os.path.exists(log_path):
    print("Log file not found:", log_path)
    exit(1)

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    log_content = f.read()

print(f"Log content length: {len(log_content)}")

# Regex for lines like: Processing file <FILE_ID> <FILE_NAME>
matches = re.findall(r"Processing file\s+([a-zA-Z0-9_-]{25,45})\s+(.+)", log_content)
print(f"Total file matches in log: {len(matches)}")

non_git_files = []
for fid, fname in matches:
    fname = fname.strip()
    if not (".git" in fname or ".cpython" in fname or ".pytest_cache" in fname):
        non_git_files.append((fid, fname))

print(f"Found {len(non_git_files)} non-git source files:")
for fid, fname in non_git_files:
    print(f"  ID: {fid} -> {fname}")

target_dir = os.path.join(os.getcwd(), "backend", "dellar")
os.makedirs(target_dir, exist_ok=True)

print("\nDownloading non-git source files...")
for fid, fname in non_git_files:
    out_path = os.path.join(target_dir, fname)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"Downloading {fname} (ID: {fid})...")
    try:
        gdown.download(id=fid, output=out_path, quiet=True)
        print(f"  ✓ Saved to {out_path}")
    except Exception as e:
        print(f"  ✗ Error downloading {fname}: {e}")

print("Done downloading key source files!")
