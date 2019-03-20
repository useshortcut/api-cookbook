import os
import sys
import requests

# This gets your token from the local environment variable.
clubhouse_api_token = '?token=' + os.getenv('CLUBHOUSE_API_TOKEN')

api_url_base = 'https://api.clubhouse.io/api/beta'
milestone_endpoint = '/milestones'


def create_csv_with_milestone_headers(document_name):
    named_csv_file = document_name + '.csv'
    csv_headers = 'Milestone Title, Average Cycle Time, Average Lead Time' + '\n'
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', named_csv_file), mode='a', encoding='utf-8') as f:
        f.write(csv_headers)
    return named_csv_file


def get_api_response(endpoint, entity_id):
    try:
        url = api_url_base + endpoint + '/' + entity_id + clubhouse_api_token
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    return response.json()


def milestone_lead_cycle_times(get_milestone_api_response):
    stats = get_milestone_api_response['stats']
    milestone_average_cycle_time = str(stats['average_cycle_time'])
    milestone_average_lead_time = str(stats['average_lead_time'])
    milestone_name = get_milestone_api_response['name']
    comma_separated_values = milestone_name + ' ,' + milestone_average_cycle_time + ' ,' + milestone_average_lead_time
    return comma_separated_values


def write_to_csv(milestone_name_cycle_lead_values, csv_document_name):
    with open(os.path.join(os.path.expanduser('~'), 'Downloads', csv_document_name), mode='a', encoding='utf-8') as f:
        f.write(milestone_name_cycle_lead_values)


def main():

    # Set up the name for the CSV document that will capture the cycle and lead time for the specified Milestone.
    # Do not include file type in the name.

    new_document_name = input('Enter the name for your file. Do not include file type in the name: ')
    milestone_id = str(input('Enter the ID of the Milestone: '))

    output_csv = create_csv_with_milestone_headers(new_document_name)
    milestone_output_details = milestone_lead_cycle_times(get_api_response(milestone_endpoint, milestone_id))
    write_to_csv(milestone_output_details, output_csv)
    print(new_document_name + ".csv is now in your Downloads folder.")


if __name__ == "__main__":
    main()