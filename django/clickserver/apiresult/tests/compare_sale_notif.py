# %%
import pandas as pd
import re
import mysql.connector
from sqlalchemy import create_engine
from urllib.parse import quote_plus

def parse_log_file(file_path):
    pattern = r'\[(\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\] INFO.*Session: ([a-f0-9]+).*Show notification: (\w+)'
   
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                timestamp, session_key, show_notification = match.groups()
                data.append({
                    'timestamp': timestamp,
                    'session_key': session_key,
                    'show_notification': show_notification.lower() == 'true'
                })

    return pd.DataFrame(data)

log_file_path = '/Users/adityaganguli/alme/staging/clickstream_server/django/clickserver/logs/info.log'
log_df = parse_log_file(log_file_path)

# %%

def get_db_data():
    db_user = 'readonlyuser'
    db_password = 'Alme@123'
    db_host = '3.6.225.178'
    db_port = '3306'  # Default MySQL port
    db_name = 'events1'
    # URL-encode the password
    db_password_encoded = quote_plus(db_password)
    # Create the database connection string with the encoded password
    connection_string = f'mysql+pymysql://{db_user}:{db_password_encoded}@{db_host}:{db_port}/{db_name}'
    # Create a SQLAlchemy engine
    engine = create_engine(connection_string)
    # SQL query to fetch session_key and has_purchased
    query = "SELECT session_key, has_purchased FROM apiresult_sessions where logged_time >'2024-08-15 00:00:00'"
    df = pd.read_sql(query,engine)
    return df

db_df = get_db_data()


# %%
# Merge dataframes
merged_df = pd.merge(log_df, db_df, on='session_key', how='inner')
merged_df.head(5)

# %%
# Calculate accuracy
merged_df['is_accurate'] = merged_df['show_notification'] != merged_df['has_purchased']
accuracy = (merged_df['is_accurate'].sum() / len(merged_df)) * 100

print(f"Accuracy: {accuracy:.2f}%")

# %%

