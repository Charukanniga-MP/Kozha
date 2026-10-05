import re

with open("scratch/gdrive_folder_page.html", "r", encoding="utf-8") as f:
    html = f.read()

keywords = ["sllsm", "slds", "entity", "locus", "speech", "sign", "decoders", "state", "core", "test", "README", "requirements", "BIDIRECTIONAL"]

for kw in keywords:
    matches = [m.start() for m in re.finditer(re.escape(kw), html, re.IGNORECASE)]
    print(f"Keyword '{kw}': found {len(matches)} occurrences")
    for pos in matches[:5]:
        snippet = html[max(0, pos-100):min(len(html), pos+150)]
        print(f"  Snippet at {pos}: {repr(snippet)}")
