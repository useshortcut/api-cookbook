from datetime import datetime, timedelta
import os
import requests

# Use your URL for the Slack webhook.
postURL = 'https://hooks.slack.com/services/YOUR_DETAILS'

# Get your token from the local environment variable and prep it for use in the URL
myToken = '?token=' + os.getenv('CH_API')

# API URL and endpoint references.
api_url_base = 'https://api.clubhouse.io/api/beta'
search_endpoint = '/search/stories'

# A list to store each page of search results for processing.
stories_list = []


def dates():
    # This gets today's date, and formats it as the name of the weekday.
    day_of_week = datetime.strftime(datetime.now(), '%A')

    # This gets today's date, subtracts one day, and formats the date as YYYY-MM-DD.
    yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')

    # This gets today's date and formats the date as YYYY-MM-DD.
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')

    # Set the beginning of the search string to the completed: operator
    completed_date = ''

    # Check if we need to search over the weekend.
    if day_of_week == 'Monday':
        completed_date = datetime.strftime(datetime.now() - timedelta(days=3), '%Y-%m-%d')
    else:
        completed_date = yesterday

    return completed_date, today


def set_query(date_start, date_end):
    completed_range = 'completed:{}..{}'.format(date_start, date_end)
    # Add any other search limiters like project names, owners, or keywords.
    limiter = ''
    query = {'query': completed_range + ' ' + limiter, 'page_size': 5}

    return query


def search_request(query):
    url = api_url_base + search_endpoint + myToken
    response = requests.get(url, params=query)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()
    return response.json()


def paginate(nextdata):
    url = 'https://api.clubhouse.io' + nextdata + '&token=' + os.getenv('CH_API')
    response = requests.get(url)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    return response.json()


def post_to_slack(data):
    response = requests.post(postURL, json=data)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    return response.json()


def parse_stories(stories_list):
    # story_list = stories_list['data']

    for story in stories_list:
        output = ''

        # Prep Story title and URL for output.

        output += story['name'] + ', ' + story['app_url'] + ', '

        # Tickets on a Story is an array in the support_tickets key.
        tickets = story['support_tickets']
        ticket_count = 0

        # If there's no attached support tickets the array will be empty.
        if not tickets:
            output += 'no tickets'

        else:
            # Add up the number of tickets and add the count to the output.
            for t in tickets:
                ticket_count += 1
            output += str(ticket_count) + ' tickets'

        # Make a temporary dictionary item out of the output with 'Text" as the key.
        temp_dict = {'text': output}
        # Send each Story to Slack
        post_to_slack(temp_dict)


date_range = dates()
query = set_query(date_range[0], date_range[1])
search_results = search_request(query)

while search_results['next'] is not None:
    stories_list.append(search_results['data'])
    search_results = paginate(search_results['next'])
else:
    stories_list.append(search_results['data'])
    for results in stories_list:
        parse_stories(results)
    print('Stories sent to Slack')

