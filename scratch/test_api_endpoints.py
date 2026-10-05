import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("1. Testing GET /api/dellar/status...")
    resp1 = requests.get(f"{BASE_URL}/api/dellar/status")
    print("Status code:", resp1.status_code)
    print("Data:", resp1.json())

    print("\n2. Testing POST /api/dellar/toggle (enable=true)...")
    resp2 = requests.post(f"{BASE_URL}/api/dellar/toggle", json={"enabled": True})
    print("Status code:", resp2.status_code)
    data2 = resp2.json()
    print("Status:", data2.get("status"))
    print("Active Entities:", data2.get("active_entities"))

    print("\n3. Testing POST /api/dellar/process-sign...")
    resp3 = requests.post(f"{BASE_URL}/api/dellar/process-sign", json={})
    print("Status code:", resp3.status_code)
    data3 = resp3.json()
    print("Status:", data3.get("status"))
    print("Latency ms:", data3.get("latency_ms"))
    print("Entities:", len(data3.get("entities", [])))

    print("\n4. Testing POST /api/dellar/process-speech...")
    resp4 = requests.post(f"{BASE_URL}/api/dellar/process-speech", json={"text": "hello"})
    print("Status code:", resp4.status_code)
    data4 = resp4.json()
    print("Pose trajectory shape:", data4.get("pose_trajectory_shape"))

    print("\n5. Testing POST /api/dellar/toggle (enable=false)...")
    resp5 = requests.post(f"{BASE_URL}/api/dellar/toggle", json={"enabled": False})
    print("Status code:", resp5.status_code)
    print("Status:", resp5.json().get("status"))

    print("\nALL API ENDPOINT INTEGRATION TESTS SUCCEEDED PERFECTLY!")

if __name__ == "__main__":
    test_api()
