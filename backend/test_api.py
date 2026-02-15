import requests
import json

try:
    print("Testing Voice API...")
    response = requests.post(
        "http://localhost:5000/api/voice/listen",
        json={"duration": 1},
        timeout=10
    )
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Test Failed: {e}")
