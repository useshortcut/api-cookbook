import os
import requests

# This gets your token from the local environment variable.
clubhouse_api_token = '?token=' + os.getenv('CH_API')

api_url_base = 'https://api.clubhouse.io/api/beta'
milestone_endpoint = '/milestones'

def get_request(endpoint, id):
    url = api_url_base + endpoint + '/' + id + clubhouse_api_token
    response = requests.get(url)

    return response.json()

def create_csv_document(doc_name):
    document_name = doc_name + '.csv'
    output = 'Milestone Title, Average Cycle Time, Average Lead Time' + '\n'
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', document_name), mode='a', encoding='utf-8') as f:
        f.write(output)
    return document_name

def lead_cycle(get_data, document_name):
   # data = get_data['data']
    stats = get_data['stats']
    cycle = str(stats['average_cycle_time'])
    lead = str(stats['average_lead_time'])
    output = get_data['name'] + ' ,' + cycle + ' ,' + lead
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', document_name), mode='a', encoding='utf-8') as f:
        f.write(output)


milestone_id = '38900'

document_name = 'Milestone_lead_cycle'

lead_cycle(get_request(milestone_endpoint, strmilestone_id), csv_document(document_name))
