import requests
import json

url = 'http://127.0.0.1:8000/'
payload = {'prompt': 'Quem descobriu o Brasil?'}
try:
    # Allow longer timeout in case model generation takes a while
    r = requests.post(url, json=payload, timeout=60)
    print('Status code:', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception as e:
        print('Response text:', r.text)
except Exception as e:
    print('Error while sending request:', e)
