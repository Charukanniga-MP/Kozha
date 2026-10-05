import json
import urllib.request

def run():
    base_url = "http://127.0.0.1:8000"
    
    # 1. Fetch Status (DELLAR OFF)
    req1 = urllib.request.Request(f"{base_url}/api/dellar/status")
    with urllib.request.urlopen(req1) as resp1:
        off_status = json.loads(resp1.read().decode())
        
    # 2. Toggle DELLAR ON
    req2 = urllib.request.Request(
        f"{base_url}/api/dellar/toggle",
        data=json.dumps({"enabled": True}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req2) as resp2:
        toggle_on = json.loads(resp2.read().decode())
        
    # 3. Process Sign Frame
    landmarks = [0.05 * (i % 5) for i in range(75)]
    req3 = urllib.request.Request(
        f"{base_url}/api/dellar/process-sign",
        data=json.dumps({"landmarks": landmarks}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as resp3:
        process_sign_resp = json.loads(resp3.read().decode())
        
    # 4. Toggle DELLAR OFF
    req4 = urllib.request.Request(
        f"{base_url}/api/dellar/toggle",
        data=json.dumps({"enabled": False}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req4) as resp4:
        toggle_off = json.loads(resp4.read().decode())
        
    captured = {
        "1_initial_off_status": off_status,
        "2_toggle_on": toggle_on,
        "3_process_sign_response": process_sign_resp,
        "4_toggle_off": toggle_off
    }
    
    with open("scratch/captured_http_response.json", "w") as f:
        json.dump(captured, f, indent=2)
    print("HTTP_TEST_SUCCESS")

if __name__ == "__main__":
    run()
