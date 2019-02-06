import os
import requests

# Get your token from the local environment variable and prep it for use in the URL
myToken = '?token=' + os.getenv('CH_API')

api_url_base = 'https://api.clubhouse.io/api/beta'
epic_endpoint = '/epics'

def csv_document(doc_name):
    document_name = doc_name + '.csv'
    output = 'Epic Title, Average Cycle Time, Average Lead Time' + '\n'
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', document_name), mode='a', encoding='utf-8') as f:
        f.write(output)
    return document_name

def get_request(endpoint, id):
    url = api_url_base + endpoint + '/' + id + myToken
    response = requests.get(url)

    return response.json()

def lead_cycle(get_data, document_name):
    stats = get_data['stats']
    cycle = str(stats['average_cycle_time'])
    lead = str(stats['average_lead_time'])
    output = get_data['name'] + ' ,' + cycle + ' ,' + lead
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', document_name), mode='a', encoding='utf-8') as f:
        f.write(output)

epic_id = 43962

document_name = 'Epic_lead_cycle'

lead_cycle(get_request(epic_endpoint, str(epic_id)), csv_document(document_name))
