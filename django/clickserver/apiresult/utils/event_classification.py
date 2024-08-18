from datetime import datetime
def strip_url_parameters(source_url):
    url_parts = source_url.split('?')
    return url_parts[0]
def convert_to_datetime(events):
    for event in events:
        if isinstance(event['click_time'], str):
            try:
                event['click_time'] = datetime.strptime(event['click_time'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                event['click_time'] = datetime.strptime(event['click_time'], '%Y-%m-%dT%H:%M:%S')
        
        if event.get('logged_time') and isinstance(event['logged_time'], str):
            try:
                event['logged_time'] = datetime.strptime(event['logged_time'], '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                event['logged_time'] = datetime.strptime(event['logged_time'], '%Y-%m-%dT%H:%M:%S')
                
    return events
def event_classifier(session_events,app_name):
    session_events = convert_to_datetime(session_events)
    # sort the events by click_time
    session_events = sorted(session_events,key=lambda x:x['click_time'])

    classified_events = []
    time_diff_events = []
    
    # iterate over the session_events
    for i,event in enumerate(session_events):
        # strip the url parameters
        event['source_url'] = strip_url_parameters(event['source_url'])
        next_product_id = session_events[i+1]['product_id'] if i+1 < len(session_events) else None
        
        if event['event_type'] == 'click':
            # for add to cart, home page or search page clicks
            if app_name == 'desisandook.myshopify.com':
                if 'add to cart' in str(event['click_text']).lower():
                    classified_events.append('add_cart_click')
                    continue
                elif str(event['source_url']).lower() == 'https://www.desisandook.com/':
                    classified_events.append('home_page_click')
                    continue
                elif str(event['source_url']).lower() == 'https://www.desisandook.com/search':
                    classified_events.append('search_page_click')
                    continue
            elif app_name == 'sujatra-sarees.myshopify.com':
                # if event+1 has source_url = 'https://www.sujatra.com/cart' then it is an add to cart event, first check for index out of range
                if i+1 < len(session_events):
                    if session_events[i+1]['source_url'] == 'https://www.sujatra.com/cart':
                        classified_events.append('add_cart_click')
                        continue
                if str(event['source_url']).lower() == 'https://www.sujatra.com/':
                    classified_events.append('home_page_click')
                    continue
                elif str(event['source_url']).lower() == 'https://www.sujatra.com/search':
                    classified_events.append('search_page_click')
                    continue

            if 'buy it now' in str(event['click_text']).lower() or 'checkout' in str(event['click_text']).lower():
                classified_events.append('buy_event_click')
                continue
            elif 'collections' in str(event['source_url']).lower() and next_product_id:
                classified_events.append('catalog_to_product_click')
                continue
            elif 'collections' in str(event['source_url']).lower():
                classified_events.append('catalog_page_click')
                continue
            
            elif event['product_id']:
                classified_events.append('product_page_click')
                continue
            elif 'account' in str(event['source_url']).lower():
                classified_events.append('account_page_click')
                continue

            
            classified_events.append('other_click')
            continue
            
        elif event['event_type'] == 'page_load':
            if app_name == 'desisandook.myshopify.com':
                if str(event['source_url']).lower() == 'https://www.desisandook.com/':
                    classified_events.append('home_page_visit')
                    continue
                elif str(event['source_url']).lower() == 'https://www.desisandook.com/search':
                    classified_events.append('search_page_visit')
                    continue
            elif app_name == 'sujatra-sarees.myshopify.com':
                if str(event['source_url']).lower() == 'https://www.sujatra.com/':
                    classified_events.append('home_page_visit')
                    continue
                elif str(event['source_url']).lower() == 'https://www.sujatra.com/search':
                    classified_events.append('search_page_visit')
                    continue

            if event['product_id']:
                classified_events.append('product_visit')
                continue
            elif 'collections' in str(event['source_url']).lower():
                classified_events.append('catalog_page_visit')
                continue
            elif 'cart' in str(event['source_url']).lower():
                classified_events.append('cart_page_visit')
                continue
            elif 'account' in str(event['source_url']).lower():
                classified_events.append('account_page_visit')
                continue

            classified_events.append('other_page_visit')
            continue

        elif event['event_type'] == 'purchase':
            classified_events.append('purchase')
            continue
        else:
            classified_events.append('other')
            continue
    # create time diff list with time difference between various events in the session
    for i in range(len(session_events)-1):
        time_diff_events.append((session_events[i+1]['click_time'] - session_events[i]['click_time']).total_seconds())
    time_diff_events.append(0)
    
    return classified_events,time_diff_events

            
        
