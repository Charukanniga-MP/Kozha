import sys
import json
from pathlib import Path

# Add server and backend/dellar to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_DIR = REPO_ROOT / "server"
DELLAR_DIR = REPO_ROOT / "backend" / "dellar"
DELLAR_SRC = DELLAR_DIR / "src"

for p in [str(SERVER_DIR), str(DELLAR_DIR), str(DELLAR_SRC)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dellar_service import dellar_service

def test_live_api():
    session_id = "live_demo_test"
    
    # 1. Check initial status
    init_status = dellar_service.get_status(session_id)
    
    # 2. Start DELLAR session
    start_resp = dellar_service.start_session(session_id)
    
    # 3. Process frame with simulated landmarks payload (25 joints x 3 = 75 floats)
    sample_landmarks = [0.05 * (i % 5) for i in range(75)]
    process_resp = dellar_service.process_sign(session_id, sample_landmarks)
    
    # 4. Stop session
    stop_resp = dellar_service.stop_session(session_id)
    
    result = {
        "initial_status": init_status,
        "start_response": start_resp,
        "process_sign_response": process_resp,
        "stop_response": stop_resp
    }
    
    output_path = REPO_ROOT / "scratch" / "captured_output.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print("SUCCESS_CAPTURED")

if __name__ == "__main__":
    test_live_api()
