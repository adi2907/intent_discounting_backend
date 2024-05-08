import requests

# Create a session object
session = requests.Session()

headers = {
    'Origin': 'https://www.almeapp.co.in',
    'Accept': 'application/json',
}

session.headers.update(headers)
url ='https://almeapp.com/segments/identified-users-list?app_name=desisandook.myshopify.com&action=cart&yesterday=true'


response = session.get(url)
print(response.text)

