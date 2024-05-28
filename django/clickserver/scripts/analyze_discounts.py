import json
import csv
import requests
from datetime import datetime
from time import sleep

def fetch_order_data(csv_file):
    output_file = 'output_orders.csv'
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as file, open(output_file, 'w', newline='') as outfile:
            reader = csv.reader(file)
            writer = csv.writer(outfile)
            writer.writerow(['Order ID', 'Total Order Value', 'Coupon Code', 'Total Discount', 'Total Quantity', 'Date Created'])
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            
            ids = [row[0] for row in reader]
            if not ids:
                print("No IDs found in CSV.")
                return

            for id in ids:
                print(f"Fetching order info for order ID: {id}")
                url = f"https://almeapp.co.in/full_order/{id}"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') and data['data']['statusCode'] == 200:
                        order = data['data']['body']['order']
                        order_id = id
                        total_price = order['total_price']
                        total_discount = order['total_discounts']
                        total_quantity = sum(item['quantity'] for item in order['line_items'])
                        created_at = datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None).date()
                        
                        coupon_code = ', '.join(code['code'] for code in order['discount_codes']) if order['discount_codes'] else ''
                        
                        writer.writerow([order_id, total_price, coupon_code, total_discount, total_quantity, created_at])
                else:
                    print(f"Failed to fetch data for order ID: {id} with status code: {response.status_code}")
                    sleep(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    csv_file = '/Users/adityaganguli/alme/staging/clickstream_server/django/clickserver/scripts/shopify_orders_sandook.csv'  # Ensure the CSV filename matches your actual file
    fetch_order_data(csv_file)
