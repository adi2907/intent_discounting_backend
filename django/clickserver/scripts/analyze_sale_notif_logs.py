from concurrent.futures import ThreadPoolExecutor, as_completed
import mysql.connector
import re

# Function to fetch session details from the database
def fetch_session_details(session_keys, db_config):
    local_conn = mysql.connector.connect(**db_config)
    local_cursor = local_conn.cursor(dictionary=True)
    results = []
    query = "SELECT * FROM apiresult_sessions WHERE session_key IN (%s)" % ','.join(['%s'] * len(session_keys))
    local_cursor.execute(query, session_keys)
    for result in local_cursor:
        results.append(result)
    local_cursor.close()
    local_conn.close()
    return results

# Helper function to divide the list into chunks of size n
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Reading session IDs from the log file
session_ids = set()
log_file_path = '/Users/adityaganguli/alme/staging/clickstream_server/django/clickserver/scripts/info.log'
with open(log_file_path, 'r') as file:
    for line in file:
        if "Payload:" in line:
            match = re.search(r"session_id': \['(.+?)'\]", line)
            if match:
                session_ids.add(match.group(1))

# Convert set to list and get only the first 1000 session IDs if more are present
session_ids = list(session_ids)[:1000]  # Ensuring we only process up to 1000 session IDs total

# Using ThreadPoolExecutor to fetch details in batches of 100 using 10 threads
all_session_details = []
with ThreadPoolExecutor(max_workers=10) as executor:
    # Submit tasks to the executor
    futures = [executor.submit(fetch_session_details, chunk, db_config) for chunk in chunks(session_ids, 100)]
    # Gather results as they are completed
    for future in as_completed(futures):
        all_session_details.extend(future.result())

# Write to CSV
with open(output_csv_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['Date', 'Time', 'Token', 'Session ID', 'App Name', 'Events Count', 'Session Start', 'Session End'])
    for details in all_session_details:
        csvwriter.writerow([
            details['logged_time'].strftime("%d/%b/%Y"),  # Format datetime as string
            details['logged_time'].strftime("%H:%M:%S"),
            details.get('token', 'N/A'),  # Token might need to be fetched or set differently
            details['session_key'],
            details['app_name'],
            details['events_count'],
            details['session_start'],
            details['session_end']
        ])
