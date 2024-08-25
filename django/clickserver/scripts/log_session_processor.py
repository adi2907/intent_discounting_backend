import datetime
import re

def parse_log_line(line):
    match = re.match(r'\[(\d{2}/\w{3}/\d{4} \d{2}:\d{2}:\d{2})\] INFO \[views\.py:\d+\] (.+)', line)
    if match:
        timestamp = datetime.datetime.strptime(match.group(1), '%d/%b/%Y %H:%M:%S')
        message = match.group(2)
        return timestamp, message
    return None, None

def process_log_file(file_path):
    current_session = None
    last_event_timestamp = None
    errors = []

    with open(file_path, 'r') as file:
        for line in file:
            timestamp, message = parse_log_line(line)
            if not timestamp:
                continue

            if "Last event timestamp is" in message:
                last_event_timestamp = datetime.datetime.strptime(message.split("is ")[-1].strip(), '%Y-%m-%d %H:%M:%S')
                
                # Check if last event timestamp is more than an hour old
                if (timestamp - last_event_timestamp) > datetime.timedelta(hours=1):
                    next_line = next(file, None)
                    if next_line:
                        _, next_message = parse_log_line(next_line)
                        if "Session flag is True" not in next_message:
                            errors.append(f"Expected session change after old timestamp: {line.strip()}")
            
            elif "Session flag is" in message:
                session_flag = "True" in message
                new_session = re.search(r'new session id is (\w+)', message)
                old_session = re.search(r'old session id is (\w+)', message)
                
                if session_flag and new_session:
                    current_session = new_session.group(1)
                elif not session_flag and old_session:
                    current_session = old_session.group(1)
            
            elif "Event click time is" in message:
                event_click_time = datetime.datetime.strptime(re.search(r'Event click time is ([\d-]+ [\d:]+)', message).group(1), '%Y-%m-%d %H:%M:%S')
                event_session = re.search(r'event session is (\w+)', message).group(1)
                token = re.search(r'for token (\w+)', message).group(1)
                
                if (timestamp - event_click_time) > datetime.timedelta(hours=1) and event_session != current_session:
                    errors.append(f"Mismatched session for old event: Token {token}, Expected {current_session}, Got {event_session}")

    return errors

# Usage
log_file_path = '/home/ubuntu/clickstream/django/clickserver/logs/trial.log'
errors = process_log_file(log_file_path)

if errors:
    print("Errors found:")
    for error in errors:
        print(error)
else:
    print("No errors found in the log file processing.")
