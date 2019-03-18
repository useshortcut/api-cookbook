The support team at Clubhouse uses a version of this script to help us get back to customers about bug fixes and shipped features.
It searches for work completed between the last business day and today, checks for support tickets on each Story, and preps data to send to Slack.
The name of the Story, a link to the Story, and a count of the number of tickets on the Story are sent to a specific Slack channel, so the support team can quickly find Stories where they need to follow up.

To use this script, open send-stories-to-slack.py in a text editor. This file will be in the folder where you downloaded the Cookbook repository.

You'll need to have a Slack App set up to use an [Incoming Webhook URL](https://api.slack.com/incoming-webhooks) to get information from Clubhouse into Slack. [Slack's guide to setting this up](https://api.slack.com/slack-apps) is very friendly!

Place your Slack Incoming Webhooks URL in this line:

    `slack_webhook_url = 'https://hooks.slack.com/services/YOUR_DETAILS'`


If you want to reduce the number of completed Stories that are sent to Slack, you can add extra limiters to this line.
Using the [search operators](https://help.clubhouse.io/hc/en-us/articles/360000046646-Search-Operators) to limit your results to Stories with a specific owner, or to exclude a specific Project. 
If no additional limiters are adding this script will search for all completed Stories in the date range.
`# Add any other search limiters like project names, owners, or keywords.
    limiter = ''`
    
When you've made your changes save the file.

To run the script, navigate to the folder for the script.
From the main Cookbook folder:
`cd stories-to-slack`

Make sure your virtual environment is active.
Then type `python send-stories-to-slack.py` and press Return/Enter to run the script. 
