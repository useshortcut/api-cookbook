# Reads a Pivotal export csv in order to prepare mapping CSVs 
# for import into Shortcut.
# See README.md for prerequisites, setup, and usage.

""" 
Given a Pivotal Tracker export file in csv format, writes states.csv and users.csv
corresponding to the states and users found in the export file.

Pivotal export csv fields are explained here at the time of this writing:
https://www.pivotaltracker.com/help/articles/csv_import_export

Note: Pivotal Tracker does not support custom state types. There are only eight states,
which are detailed here at the time of this writing: 
https://www.pivotaltracker.com/help/articles/story_states/
"""