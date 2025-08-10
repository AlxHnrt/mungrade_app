import requests

url = "http://127.0.0.1:5000/score"

payload = {"criteria": ["profitability", "growth"]}

r = requests.post(url, json=payload)

print(r.status_code, r.text)
 