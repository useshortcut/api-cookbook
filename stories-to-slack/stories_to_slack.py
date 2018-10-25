import os
import requests
import json
import time
from datetime import datetime, timedelta

# set up date info
#------------------------------------------------------------------------------------

#this gets today's date, and formats it as the name of the weekday
check_weekend = datetime.strftime(datetime.now(), '%A')

# this gets today's date, subtracts one day, and formats the date as YYYY-MM-DD
yesterday = datetime.strftime(datetime.now() - timedelta(days=1), '%Y-%m-%d')

# This gets today's date and formats the date as YYYY-MM-DD
today = datetime.strftime(datetime.now(), '%Y-%m-%d')

#set the beginning of the search string to the completed: operator
completed_date = 'completed:'

#check if we need to search over the weekend
if check_weekend == 'Monday':
	completed_date += datetime.strftime(datetime.now() - timedelta(days=3), '%Y-%m-%d')
else:
	completed_date += yesterday



# set up some handy variables
#-------------------------------------------------------------------------------------

#This gets your token from the local envirnoment variable
myToken = os.getenv("CH_API")

# exclude label:followupsent and marketing projects in the query
query = {'query': completed_date + '..' + today + '!project:ideas', 'page_size': 25}

url = 'https://api.clubhouse.io/api/beta/search/stories?token='+myToken

#the URL for the Slack webhook
postURL = 'https://hooks.slack.com/services/YOUR_DETAILS'

# Do the GET request to fetch data from Clubhouse
response = requests.get(url, params=query)

# Check for HTTP codes other than 200
if response.status_code != 200:
    print('Status:', response.status_code, 'Problem with the request. Exiting.')
    exit()
# ------------------------------------------------------------------------------------------

#define function that uses the data from Clubhouse and sends to Slack

def slack(x):

    # Decode the JSON response into a dictionary and use the data
    data = x.json()

    #'data' is used here because that is the key for the array that contains the Story data
    story_list = data['data']

    
    for story in story_list:
        output = ''
        # Story title and URL prepped for output

        output += story['name'] + ', ' + story['app_url'] + ', '

        # Tickets on a Story is an array in the support_tickets key
        tickets= story['support_tickets']
        ticket_count = 0

        #if there's no attached support tickets the array will be empty
        if not tickets:
            output += 'no tickets'

        else:
            # add up the number of tickets and add the count to the output
            for t in tickets:
                ticket_count += 1
            output += str(ticket_count) + ' tickets'

    #make a temporary dictionary item out of the output with 'Text" as the key, turn it into a json object, and send it to Slack
        temp_dict = {'text': output}
        post = requests.post(postURL, json=temp_dict)

#display number of Stories from query in Terminal, just so you know what to check against
    print(data['total'])

    return data



#  make sure there's a way to handles searches with a second page of results
# ------------------------------------------------------------------------------------------

# part of the data returned from the search is the next value: None if there are 25 or fewer results, and a url if there is another page of results
next_page = slack(response)['next']

#if there's something other than None, use the next url to make another GET request and use the data
if next_page != None:
    next_url = 'https://api.clubhouse.io' + next_page + '&token='+myToken
    time.sleep(.3)
    next_response = requests.get(next_url)

    if next_response.status_code != 200:
        print('Status:', response.status_code, 'Problem with the request. Exiting.')
        exit()

    slack(next_response)





