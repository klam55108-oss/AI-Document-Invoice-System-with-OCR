
import requests
import json

url = "http://localhost:8000/api/v1/invoices/process"
payload = {
    "file_path": "grok/1.jpg",
    "force_reprocess": False
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
