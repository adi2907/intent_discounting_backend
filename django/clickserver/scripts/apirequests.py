import requests

# Create a session object
session = requests.Session()

headers = {
    'Origin': 'https://www.almeapp.co.in',
    'Accept': 'application/json',
}

session.headers.update(headers)

params = {
    'app_name':'millet-amma-store.myshopify.com',
    'token':'1234567890',
}

url = 'https://almeapp.com/api/featured_collection/'
response = session.get(url, params=params)
print(response.text)

