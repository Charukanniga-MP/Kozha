import json
import urllib.request
import time

def run_test():
    base_url = "http://127.0.0.1:8000"
    report = []
    
    report.append("=== 1. INITIAL STATUS (DELLAR OFF) ===")
    req1 = urllib.request.Request(f"{base_url}/api/dellar/status")
    with urllib.request.urlopen(req1) as r1:
        off_data = json.loads(r1.read().decode())
    report.append(json.dumps(off_data, indent=2))
    assert off_data["status"] == "OFF"
    assert off_data["active_entities"] == 0
    assert off_data["total_associations"] == 0
    assert off_data["rebindings"] == 0
    assert off_data["lost_entities"] == 0
    
    report.append("\n=== 2. TOGGLE DELLAR ON ===")
    req2 = urllib.request.Request(
        f"{base_url}/api/dellar/toggle",
        data=json.dumps({"enabled": True}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2) as r2:
        on_data = json.loads(r2.read().decode())
    report.append(json.dumps(on_data, indent=2))
    assert on_data["status"] == "RUNNING"
    
    report.append("\n=== 3. PROCESS LIVE SIGN FRAME (75 floats) ===")
    landmarks = [0.02 * (i % 7) for i in range(75)]
    req3 = urllib.request.Request(
        f"{base_url}/api/dellar/process-sign",
        data=json.dumps({"landmarks": landmarks}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as r3:
        frame_data = json.loads(r3.read().decode())
    report.append(json.dumps(frame_data, indent=2))
    assert frame_data["status"] == "RUNNING"
    assert "active_entities" in frame_data
    assert "entities" in frame_data
    
    report.append("\n=== 4. TOGGLE DELLAR OFF (RESET SESSION) ===")
    req4 = urllib.request.Request(
        f"{base_url}/api/dellar/toggle",
        data=json.dumps({"enabled": False}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req4) as r4:
        reset_data = json.loads(r4.read().decode())
    report.append(json.dumps(reset_data, indent=2))
    assert reset_data["status"] == "OFF"
    assert reset_data["active_entities"] == 0
    assert reset_data["total_associations"] == 0
    assert reset_data["rebindings"] == 0
    assert reset_data["lost_entities"] == 0
    
    report.append("\n=== ALL LIVE REST API TESTS PASSED SUCCESSFULLY ===")
    
    with open("scratch/api_report.txt", "w") as f:
        f.write("\n".join(report))
    print("VERIFICATION_COMPLETE", flush=True)

if __name__ == "__main__":
    run_test()
