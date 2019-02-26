If you're using labels to model sprint, you may need to change the label on incomplete work to move it to the next sprint.

This script searches for incomplete work in an existing label and replaces the existing label with a new label.


You'll need to make two changes in the file:

1. The name of the existing label you want to search for.
    existing_label = 'Sprint 1'

2. The name and hex color for the label you want to add
    new_label = {'name': 'Sprint 2', 'color': '#ff0022'}
    

You may also adjust the included search operators to adapt this for other use cases.


search_for_label_with_incomplete_work = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}
