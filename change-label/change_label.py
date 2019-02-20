import os
import requests

# Get your token from the local environment variable and prep it for use in the URL
clubhouse_api_token = '?token=' + os.getenv('CH_API')

# API URL and endpoint references.
api_url_base = 'https://api.clubhouse.io/api/beta'
search_endpoint = '/search/stories'
stories_endpoint = '/stories'

# The name of the existing label you want to search for.
existing_label = 'Sprint 1'

search_query = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}

# The name and hex color for the label you want to add
new_label = {'name': 'Sprint 2', 'color': '#ff0022'}

# A list to store each page of search results for processing.
stories_list = []


def search_request(query):
    url = api_url_base + search_endpoint + clubhouse_api_token
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


def change_story_labels(story_id, labels_on_story):
    url = api_url_base + stories_endpoint + '/' + story_id + clubhouse_api_token
    params = {'labels': labels_on_story}
    response = requests.put(url, json=params)
    return response.json()


def assess_story_labels(story_results, remove_label, add_label):
    for story in story_results:
        story_id = str(story['id'])
        list_of_labels_on_story = story['labels']
        list_of_labels_to_keep = [add_label]
        for label in list_of_labels_on_story:
            if label['name'] != remove_label:
                list_of_labels_to_keep.append({'name': label['name']})
        change_story_labels(story_id, list_of_labels_to_keep)
    return None


search_results = search_request(search_query)

while search_results['next'] is not None:
    stories_list.append(search_results['data'])
    search_results = paginate(search_results['next'])
else:
    stories_list.append(search_results['data'])
    for results in stories_list:
        assess_story_labels(results, existing_label, new_label)
    print('Stories updated')
