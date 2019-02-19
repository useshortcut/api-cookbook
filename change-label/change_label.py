import os
import requests

# Get your token from the local environment variable and prep it for use in the URL
clubhouse_api_token = '?token=' + os.getenv('CH_API')


#The name of the existing label you want to search for.
existing_label = 'willowlabeltest'

query = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}


#A list to store each page of search results for processing.
stories_list = []

#API URL and endpoint references.
api_url_base = 'https://api.clubhouse.io/api/beta'
search_endpoint = '/search/stories'
stories_endpoint = '/stories'

def search_request(label_query):
    url = api_url_base + search_endpoint + clubhouse_api_token
    response = requests.get(url, params=label_query)

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

def update_story(id, list_of_labels_on_story):
    url = api_url_base + stories_endpoint + '/' + id + clubhouse_api_token
    params = {'labels': list_of_labels_on_story}
    response = requests.put(url, json=params)
    return response.json()

def update_story_labels(results, existing_label):
    for story in results:
        story_id = str(story['id'])
        labels = story['labels']
        list_of_labels_on_story = [new_label]
        for label in labels:
            if label['name'] != existing_label:
                list_of_labels_on_story.append({'name': label['name']})
        update_story(story_id, list_of_labels_on_story)
    return None

#The name and hex color for the label you want to add
new_label = {'name': name, 'color': hex_color}
search_results = search_request(query)

while search_results['next'] is not None:
    stories_list.append(search_results['data'])
    search_results = paginate(search_results['next'])
else:
    stories_list.append(search_results['data'])
    for results in stories_list:
         update_story_labels(results, existing_label)
    print('Stories updated')
