import os
import requests

# Get your token from the local environment variable and prep it for use in the URL
myToken = '?token=' + os.getenv('CH_API')


#The name of the existing label you want to search for.
label_name = 'sprint1'

query = {'query': '!is:done label:"' + label_name + '"', 'page_size': 25}


#A list to store each page of search results for processing.
stories_list = []

#API URL and endpoint references.
api_url_base = 'https://api.clubhouse.io/api/beta'
search_endpoint = '/search/stories'
stories_endpoint = '/stories'

def search_request(label_query):
    url = api_url_base + search_endpoint + myToken
    response = requests.get(url, params=label_query)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    return response.json()

def get_request(endpoint, id):
    url = api_url_base + endpoint + '/' + id + myToken
    response = requests.get(url)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    return response.json()

def paginate(nextdata):
    url = 'https://api.clubhouse.io' + nextdata + '&' + os.getenv('CH_API')
    response = requests.get(url)

    if response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    return response.json()

def update_story(id, label_names):
    url = api_url_base + stories_endpoint + '/' + id + myToken
    params = {'labels': label_names}
    response = requests.put(url, json=params)
    return response.json()

def add_label(name, hex_color):
    new_label = {'name': name, 'color': hex_color}
    return new_label

def update_story_labels(data):
    for story in data:
        story_id = str(story['id'])
        labels = story['labels']
        label_names = [new_label]
        for label in labels:
            if label['name'] != label_name:
                label_names.append({'name': label['name']})
        update_story(story_id, label_names)
    return None

#The name and hex color for the label you want to add
new_label = add_label('sprint2', '#ff00d5')
search_results = search_request(query)

while search_results['next'] is not None:
    stories_list.append(search_results['data'])
    search_results = paginate(search_results['next'])
else:
    stories_list.append(search_results['data'])
    for results in stories_list:
         update_story_labels(results)
    print('Stories updated')
