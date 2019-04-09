from datetime import datetime, timedelta
import os
import sys
import requests

# Get your token from the local environment variable and prep it for use in the URL
clubhouse_api_token = '?token=' + os.getenv('CLUBHOUSE_API_TOKEN')

# API URL and endpoint references.
api_url_base = 'https://api.clubhouse.io/api/beta'
search_endpoint = '/search/stories'


def date_range_for_search():
    # This gets today's date, and formats it as the name of the weekday.
    day_of_week = datetime.strftime(datetime.now(), '%A')

    # This gets today's date, subtracts one day, and formats the date as YYYY-MM-DD.
    yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')

    # This gets today's date and formats the date as YYYY-MM-DD.
    today = datetime.strftime(datetime.now(), '%Y-%m-%d')
    # Check if we need to search over the weekend.
    if day_of_week == 'Monday':
        start_of_search_date_range = datetime.strftime(datetime.now() - timedelta(days=3), '%Y-%m-%d')
    else:
        start_of_search_date_range = yesterday

    return start_of_search_date_range, today


def search_stories(query):
    try:
        url = api_url_base + search_endpoint + clubhouse_api_token
        response = requests.get(url, params=query)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def paginate_results(next_page_data):
    try:
        url = 'https://api.clubhouse.io' + next_page_data + '&token=' + os.getenv('CLUBHOUSE_API_TOKEN')
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def post_story_details_to_slack(story_details, slack_webhook):
    try:
        response = requests.post(slack_webhook, json=story_details)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def parse_stories(stories_list, slack_webhook):
    for story in stories_list:
        story_details_for_slack = ''

        # Prep Story title and URL for output.
        story_details_for_slack += story['name'] + ', ' + story['app_url'] + ', '

        # Tickets on a Story is an array in the external_tickets key.
        tickets = story['external_tickets']
        ticket_count = 0

        # If there are no attached support tickets the array will be empty.
        if not tickets:
            story_details_for_slack += 'no tickets'
        else:
            # Add up the number of tickets and add the count to the output.
            for t in tickets:
                ticket_count += 1
            story_details_for_slack += str(ticket_count) + ' tickets'

        output_for_slack = {'text': story_details_for_slack}
        # Send each Story to Slack
        post_story_details_to_slack(output_for_slack, slack_webhook)


def main():
    # Use your URL for the Slack webhook.
    slack_webhook_url = 'https://hooks.slack.com/services/YOUR_DETAILS'

    # Add any other search limiters like project names, owners, or keywords, by using additional search operators.
    limiter = ''

    start_of_date_range, end_of_date_range = date_range_for_search()
    date_range_for_completed_stories = 'completed:{}..{}'.format(start_of_date_range, end_of_date_range)
    search_query = {'query': date_range_for_completed_stories + ' ' + limiter, 'page_size': 25}
    search_results = search_stories(search_query)
    pages_of_search_results = []

    while search_results['next'] is not None:
        pages_of_search_results.append(search_results['data'])
        search_results = paginate_results(search_results['next'])
    else:
        pages_of_search_results.append(search_results['data'])
        for page_of_stories in pages_of_search_results:
            parse_stories(page_of_stories, slack_webhook_url)
        print('Stories sent to Slack')


if __name__ == "__main__":
    main()
