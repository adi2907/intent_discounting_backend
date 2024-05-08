import requests

# Create a session object
session = requests.Session()

headers = {
    'Origin': 'https://www.almeapp.co.in',
    'Accept': 'application/json',
}

session.headers.update(headers)
url ='https://almeapp.com/segments/identified-users-sessions?app_name=almestore1.myshopify.com&comparison_field=greater_than&comparison_value=10'


response = session.get(url)
print(response.text)

