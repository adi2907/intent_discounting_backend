import requests

# Create a session object
session = requests.Session()

headers = {
    'Origin': 'https://www.almeapp.co.in',
    'Accept': 'application/json',
}

session.headers.update(headers)
url ='https://almeapp.com/segments/identified-users-last-visit?app_name=millet-amma-store.myshopify.com&date_field=before&date=2024-05-07'


response = session.get(url)
print(response.text)

