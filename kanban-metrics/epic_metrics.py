import os
import sys
import requests

# Get your token from the local environment variable and prep it for use in the URL
shortcut_api_token = '?token=' + os.getenv('shortcut_api_token')

api_url_base = 'https://api.shortcut.com/api/beta'
epic_endpoint = '/epics'


def create_csv_with_epic_headers(document_name):
    named_csv_file = document_name + '.csv'
    csv_headers = 'Epic Title, Average Cycle Time, Average Lead Time' + '\n'
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', named_csv_file), mode='a', encoding='utf-8') as f:
        f.write(csv_headers)
    return named_csv_file


def epic_lead_cycle_times(get_epic_api_response):
    epic_stats = get_epic_api_response['stats']
    epic_average_cycle_time = str(epic_stats['average_cycle_time'])
    epic_average_lead_time = str(epic_stats['average_lead_time'])
    epic_name = get_epic_api_response['name']
    comma_separated_values = epic_name + ' ,' + epic_average_cycle_time + ' ,' + epic_average_lead_time
    return comma_separated_values


def get_api_response(endpoint, entity_id):
    try:
        url = api_url_base + endpoint + '/' + entity_id + shortcut_api_token
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def write_to_csv(epic_name_cycle_lead_values, csv_document_name):
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', csv_document_name), mode='a', encoding='utf-8') as f:
        f.write(epic_name_cycle_lead_values)


def main():
    # Set up the name for the CSV document that will capture the cycle and lead time for the specified Epic.
    # Do not include file type in the name.
    new_document_name = input('Enter the name for your file. Do not include file type in the name: ')
    epic_id = str(input('Enter the ID of the Epic: '))

    output_csv = create_csv_with_epic_headers(new_document_name)
    epic_output_details = epic_lead_cycle_times(get_api_response(epic_endpoint, epic_id))
    write_to_csv(epic_output_details, output_csv)
    print(new_document_name + ".csv is now in your Downloads folder.")


if __name__ == "__main__":
    main()