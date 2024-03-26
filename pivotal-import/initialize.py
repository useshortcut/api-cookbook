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

import logging
import os
import sys

import requests

# Logging
logger = logging.getLogger(__name__)
# FIXME Make INFO default upon public release
logging.basicConfig(level=logging.DEBUG)  # Change to INFO or DEBUG as needed

# API Helpers
sc_token = os.getenv("SHORTCUT_API_TOKEN")
api_url_base = "https://api.app.shortcut.com/api/v3"
headers = {
    "Shortcut-Token": sc_token,
    "Accept": "application/json; charset=utf-8",
    "Content-Type": "application/json",
}


def sc_get(path, params={}):
    url = api_url_base + path
    logger.debug("GET url=%s params=%s headers=%s" % (url, params, headers))
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def sc_post(path, data={}):
    url = api_url_base + path
    logger.debug("POST url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def sc_put(path, data={}):
    url = api_url_base + path
    logger.debug("PUT url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.put(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


# Mapping of Pivotal Tracker story states to Shortcut default Story Workflow State names
pt_states = {
    "Unscheduled": "Unscheduled",
    "Unstarted": "Unscheduled",
    "Planned": "Ready for Development",
    "Started": "In Development",
    "Finished": "Ready for Review",
    "Rejected": "Completed",
    "Accepted": "Completed",
}


def validate_config():
    if sc_token is None:
        logger.fatal(
            "You must define a SHORTCUT_API_TOKEN environment variable with your Shortcut API token."
        )
        sys.exit(1)


def main():
    validate_config()
    workflows = sc_get("/workflows")
    print("Your Shortcut workspace's Story Worklows:")
    for workflow in workflows:
        if workflow["name"] == "Engineering":
            print('  {id} : "{name}" [default]'.format_map(workflow))
        else:
            print('  {id} : "{name}"'.format_map(workflow))
        for workflow_state in workflow["states"]:
            print('    {id} : [{type}] "{name}"'.format_map(workflow_state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
