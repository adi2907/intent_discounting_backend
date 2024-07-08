import re
from datetime import datetime
import csv

# Define the path to the log file
log_file_path = '/Users/adityaganguli/alme/staging/clickstream_server/django/clickserver/scripts/info.log'

# Define the output CSV file
output_csv_path = 'output.csv'

# Define the start and end dates for filtering the log entries
start_date = datetime(2024, 5, 15)
end_date = datetime(2024, 5, 21, 23, 59, 59)

# Initialize a dictionary to store the counts
date_counts = {}

with open(log_file_path, 'r') as file:
    for line in file:
        # Check if the line contains a date and extract it
        date_match = re.search(r'\[(\d{2}/May/2024 \d{2}:\d{2}:\d{2})\]', line)
        if date_match:
            log_date = datetime.strptime(date_match.group(1), '%d/%b/%Y %H:%M:%S')
            if start_date <= log_date <= end_date:
                date_str = log_date.strftime('%Y-%m-%d')
                if date_str not in date_counts:
                    date_counts[date_str] = {'received': 0, 'errors': 0, 'true': 0, 'false': 0}
                
                if 'Sale notification request received' in line:
                    date_counts[date_str]['received'] += 1
                elif 'Error in sale notification' in line:
                    date_counts[date_str]['errors'] += 1
                elif 'Sale notification true' in line:
                    date_counts[date_str]['true'] += 1
                elif 'Sale notification false' in line:
                    date_counts[date_str]['false'] += 1

# Write the results to a CSV file
with open(output_csv_path, 'w', newline='') as csvfile:
    fieldnames = ['Date', '# of sale notifications received', '# Errors', '# Sale notification True', '# Sale Notification False']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for date, counts in date_counts.items():
        row = {
            'Date': date,
            '# of sale notifications received': counts['received'],
            '# Errors': counts['errors'],
            '# Sale notification True': counts['true'],
            '# Sale Notification False': counts['false']
        }
        writer.writerow(row)

print("CSV file has been created successfully.")
