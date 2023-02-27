import os
import sys
import requests

# Get your token from the local environment variable and prep it for use in the URL
shortcut_api_token = '?token=' + os.getenv('SHORTCUT_API_TOKEN')

# API URL and endpoint references.
api_url_base = 'https://api.app.shortcut.com/api/beta'
search_endpoint = '/search/stories'
stories_endpoint = '/stories'


def assess_story_labels(story_results, old_label, new_label):
    for story in story_results:
        story_id = str(story['id'])
        list_of_labels_on_story = story['labels']
        list_of_labels_to_keep = [new_label]
        for label in list_of_labels_on_story:
            if label['name'] != old_label:
                list_of_labels_to_keep.append({'name': label['name']})
        change_story_labels(story_id, list_of_labels_to_keep)
    return None


def change_story_labels(story_id, labels_on_story):
    url = api_url_base + stories_endpoint + '/' + story_id + shortcut_api_token
    params = {'labels': labels_on_story}
    response = requests.put(url, json=params)
    return response.json()


def paginate_results(next_page_data):
    try:
        url = 'https://api.app.shortcut.com' + next_page_data + '&token=' + os.getenv('SHORTCUT_API_TOKEN')
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def search_stories(query):
    try:
        url = api_url_base + search_endpoint + shortcut_api_token
        response = requests.get(url, params=query)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def main():

    existing_label = input('Enter the name of the existing label you want to search for: ')

    # The name and hex color for the label you want to add
    new_label_name = input('Enter the name for the new label: ')

    label_color_hex = input('Enter the hex value for your label color. Include the #: ')

    new_label = {'name': new_label_name, 'color': label_color_hex}

    search_for_label_with_incomplete_work = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}

    # A list to store each page of search results for processing.
    pages_of_search_results = []

    search_results = search_stories(search_for_label_with_incomplete_work)

    while search_results['next'] is not None:
        pages_of_search_results.append(search_results['data'])
        search_results = paginate_results(search_results['next'])
    else:
        pages_of_search_results.append(search_results['data'])
        for page_of_stories in pages_of_search_results:
            assess_story_labels(page_of_stories, existing_label, new_label)
        print('Stories updated')


if __name__ == "__main__":
    main()
