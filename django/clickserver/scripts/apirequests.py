import requests

# Create a session object
session = requests.Session()

headers = {
    'Origin': 'https://www.almeapp.co.in',
    'Accept': 'application/json',
}

session.headers.update(headers)

params = {
    'app_name':'almestore1.myshopify.com',
    'days':'7',
}

#url = 'https://almeapp.com/api/featured_collection/'
url ='https://almeapp.com/analytics/product_visits/?app_name=almestore1.myshopify.com&days=7'
#url = url + '&days=7'
response = session.get(url)
print(response.text)

