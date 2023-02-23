If you're using labels to model sprints, you may need to change the label on incomplete work to move it to the next sprint.

This script searches for incomplete work in an existing label and replaces the existing label with a new label.

To use this script:
Make sure your virtual environment is active.`source cookbook/bin/activate` for Mac and `cookbook\Scripts\activate` for Windows.
Then type `python change_label.py` and press Return/Enter to run the script.

You'll be asked to enter:
1. The name of the existing label you want to search for.
2. The name of the label you want to create and apply.
3. The hex value for the label color.

When the script finishes running, you'll see "Stories Updated" in your command prompt.

----

If you want to modify this script for other uses, consider starting with the included [search operators](https://help.shortcut.com/hc/en-us/articles/360000046646-Search-Operators).

`search_for_label_with_incomplete_work = {'query': '!is:done label:"' + existing_label + '"', 'page_size': 25}`
