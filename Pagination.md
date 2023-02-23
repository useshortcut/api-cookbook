Some requests will return more than one page of results.

You'll need to use the value returned in the next: key as part of the URL to access the next page.

Set your API token and the next: value as variables, and then create the URL to access the next page.
That may look like this:

```python
shortcut_api_token = os.getenv('SHORTCUT_API_TOKEN')
next_page = results['next']

next_url = 'https://api.shortcut.com' + next_page + '&token='+ shortcut_api_token
```

Use the next_url that you've created to make another call to the API to get the next page of results.

The scripts [change-label.py](https://github.com/useshortcut/api-cookbook/blob/master/change-label/change_label.py) and [send-stories-to-slack.py](https://github.com/useshortcut/api-cookbook/blob/master/stories-to-slack/send-stories-to-slack.py) both contain examples of pagination.

