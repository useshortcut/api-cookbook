If you're using labels to model sprint, you may need to change the label on incomplete work to move it to the next sprint.

This script searches for incomplete work in an existing label and replaces the existing label with a new label.

To use this script, open change_label.py in a text editor. This file will be in the folder where you downloaded the Cookbook repository.

You'll need to make two changes in the file:

1. The name of the existing label you want to search for.
   Line 57: `existing_label = 'Sprint 1'`
   Change Sprint 1 to the name of the label you want to search for. Keep the single quotes around the label name.

2. The name and hex color for the label you want to add
    Line 60: `new_label = {'name': 'Sprint 2', 'color': '#ff0022'}`
    Change Sprint 2 to the name of the label you want to add. Change #ff0022 to the hex color you want to add. Keep the single quotes around the label name and the hex color.
    
    

You may also adjust the included [search operators](https://help.clubhouse.io/hc/en-us/articles/360000046646-Search-Operators) to adapt this for other use cases. You should only make these adjustments if you can confidently change the query value.

`search_for_label_with_incomplete_work = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}`

When you've made your changes save the file.

To run the script, navigate to the folder for the script.
From the main Cookbook folder `api-cookbook`:
`cd change-label`

Make sure your virtual environment is active.
Then type `python change_label.py` and press Return/Enter to run the script. 
