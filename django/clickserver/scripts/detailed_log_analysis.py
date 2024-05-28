import re
from datetime import datetime
import csv

# Define the path to the log file
log_file_path = '/Users/adityaganguli/alme/staging/clickstream_server/django/clickserver/scripts/info.log'

# Define the output CSV file
output_csv_path = 'output_detailed.csv'

# Regex to extract payload data
payload_pattern = re.compile(r"{'session_id': \['(.*?)'\], 'token': \['(.*?)'\], 'app_name': \['(.*?)'\]}")

# Open the log file and process each line
entries = []
with open(log_file_path, 'r') as file:
    for line in file:
        date_match = re.search(r'\[(\d{2}/May/2024 \d{2}:\d{2}:\d{2})\]', line)
        if date_match:
            timestamp = datetime.strptime(date_match.group(1), '%d/%b/%Y %H:%M:%S').isoformat()

            # Extract payload data if present
            payload_match = payload_pattern.search(line)
            if payload_match:
                session_id, token, app_name = payload_match.groups()
                entry = {
                    'Session_id': session_id,
                    'Token': token,
                    'app_name': app_name,
                    'Timestamp': timestamp,
                    'Error': 'no',
                    'Sale Notification True': False,
                    'Sale Notification False': False
                }
                entries.append(entry)

            # Check for errors and sale notification status
            if 'Error in sale notification' in line:
                entries[-1]['Error'] = 'yes'
            elif 'Sale notification true' in line:
                entries[-1]['Sale Notification True'] = True
            elif 'Sale notification false' in line:
                entries[-1]['Sale Notification False'] = True

# Write the results to a CSV file
with open(output_csv_path, 'w', newline='') as csvfile:
    fieldnames = ['Session_id', 'Token', 'app_name', 'Timestamp', 'Error', 'Sale Notification True', 'Sale Notification False']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)

print("Detailed CSV file has been created successfully.")
