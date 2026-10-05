import os
import sys
import requests
import time

files_to_download = {
    # src/slds_core
    "backend/dellar/src/slds_core/__init__.py": "1ciNE8stSzeKBMRBUPe5Lm_t15H6sDyDC",
    "backend/dellar/src/slds_core/sllsm_core.py": "1n23u1r_Em-3UO0wuoY42kG2bcwTFo8E9",
    "backend/dellar/src/slds_core/core.py": "1QnAniCuV1oW6rK4CU3Tc4HgmO55bjoB8",
    "backend/dellar/src/slds_core/entity.py": "14iEAJhA9bm3YjioDbQlqOFK3Tl_nLQvb",
    "backend/dellar/src/slds_core/locus.py": "1qDdo2xEBSBHZJTMsAcTutKjsdNS54LOp",
    "backend/dellar/src/slds_core/locus_fsm.py": "1Gzsj5VTxCfbe1QkoJHv-umsGf6tB3kPD",
    "backend/dellar/src/slds_core/memory.py": "1yeM7kb9Q1VsZEGVwnXauwlm0L4TJwbpM",
    "backend/dellar/src/slds_core/relation.py": "1g_HhsxNk3KKxe_lnH9lpObYviWTEAURb",
    "backend/dellar/src/slds_core/speech_adapter.py": "1_WtHnBZvd3YJS2K3KgjXd70EcCrJ8aB5",
    "backend/dellar/src/slds_core/sign_adapter.py": "1VrADXG7k3eJLgsYBs7xZkHBP4eRA292c",
    "backend/dellar/src/slds_core/decoders.py": "1w0IfdYtBtdriagEaKfh5kDgon7WQwnrq",
    "backend/dellar/src/slds_core/state.py": "1xvMty-oD9S_T4KWvD2INLhhcIYEQfBye",
    "backend/dellar/src/slds_core/bidirectional_pipeline.py": "116kXjQ347JdAIsOGRvwMKoUTfY3w0tOy",
    "backend/dellar/src/slds_core/common_representation.py": "1q3v-BUV1QmeqB6c6uXPKK17Wvhv6Ykhw",

    # tests
    "backend/dellar/tests/__init__.py": "1mdiBgcx0F63uiXBULLq1LvYydbYN-bk5",
    "backend/dellar/tests/test_dellar_bidirectional.py": "1EgTo_4fbUAyCNKF3oXz5hTxUDfGf1cm9",
    "backend/dellar/tests/test_phase8_bidirectional.py": "1xmv3TVbaBaHv4pALSxHjDE6uyLCnOlfT",
    "backend/dellar/tests/test_sllsm_adversarial.py": "1tmsqTNsO2L0mjhYMZBGFUg4yizIzj0n1",
    "backend/dellar/tests/test_sllsm_core.py": "1vxm2oqAbNXo4A5llMvV1OLkXc12Aic18",
    "backend/dellar/tests/test_sllsm_counterfactual.py": "1FSQdkXdQN1_eesAgBRtp77a5Pt4PVFF8",

    # root
    "backend/dellar/README.md": "1220CnyhGM3-iDWI-YnYvj9hoVqNs2ADu",
    "backend/dellar/.gitignore": "1GZDF9VzH0MTS1LSK_94DsvCAQIMh_QCR",
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def download_file(target_path, file_id):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Try method 1: uc direct export download link
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 0 and not r.content.startswith(b'<!DOCTYPE html>'):
            with open(target_path, 'wb') as f:
                f.write(r.content)
            print(f"[SUCCESS Direct] {target_path} ({len(r.content)} bytes)")
            return True
    except Exception as e:
        print(f"[FAIL Direct] {target_path}: {e}")

    # Try method 2: drive.usercontent.google.com with confirm
    url2 = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    try:
        r2 = requests.get(url2, headers=headers, timeout=15)
        if r2.status_code == 200 and len(r2.content) > 0 and not r2.content.startswith(b'<!DOCTYPE html>'):
            with open(target_path, 'wb') as f:
                f.write(r2.content)
            print(f"[SUCCESS Usercontent] {target_path} ({len(r2.content)} bytes)")
            return True
    except Exception as e:
        print(f"[FAIL Usercontent] {target_path}: {e}")

    # Try method 3: gdown
    try:
        import gdown
        res = gdown.download(id=file_id, output=target_path, quiet=True, fuzzy=True)
        if res and os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print(f"[SUCCESS gdown] {target_path} ({os.path.getsize(target_path)} bytes)")
            return True
    except Exception as e:
        print(f"[FAIL gdown] {target_path}: {e}")

    print(f"[FAILED ALL METHODS] {target_path}")
    return False

success_count = 0
total_count = len(files_to_download)

for target_path, file_id in files_to_download.items():
    print(f"Downloading {target_path} (ID: {file_id})...")
    if download_file(target_path, file_id):
        success_count += 1
    time.sleep(1)

print(f"\nCompleted: {success_count}/{total_count} files downloaded successfully.")
