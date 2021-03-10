import requests

URL_BASE = 'http://localhost:5000/'

# API v1.2 - PUT (Add file)
print('Posting file...')
url = URL_BASE + 'predict'
r = requests.post(url, files={'anonymised_file': open('/home/kc/junk/Devranker/anonymized_elasticray.git.csv', 'rb')})
print(r.status_code)
print(r.headers)
print(r.text)