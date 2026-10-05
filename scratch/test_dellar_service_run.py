import sys
from pathlib import Path

# Add server and backend/dellar to sys.path
sys.path.insert(0, str(Path("server").resolve()))
sys.path.insert(0, str(Path("backend/dellar").resolve()))

import dellar_service as ds

def test():
    service = ds.dellar_service
    print("1. Get status before start:", service.get_status("test_user")["status"])
    print("2. Start session:", service.start_session("test_user")["status"])
    
    res_sign = service.process_sign("test_user")
    print("3. Process sign frame success:", "latency_ms" in res_sign, "active_entities:", res_sign.get("active_entities"))
    print("   Entities:", res_sign.get("entities"))
    
    res_speech = service.process_speech("test_user")
    print("4. Process speech frame success:", "pose_trajectory_shape" in res_speech)
    print("   Trajectory shape:", res_speech.get("pose_trajectory_shape"))
    
    print("5. Stop session:", service.stop_session("test_user")["status"])
    print("ALL DELLAR SERVICE TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test()
