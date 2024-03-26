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

from collections.abc import Mapping
import json
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


# Mapping of Pivotal Tracker story states to Shortcut ones
pt_states = {
    "Unscheduled": {"type": "unstarted", "default_workflow_state": "Unscheduled"},
    "Unstarted": {"type": "unstarted", "default_workflow_state": "Unscheduled"},
    "Planned": {"type": "unstarted", "default_workflow_state": "Ready for Development"},
    "Started": {"type": "started", "default_workflow_state": "In Development"},
    "Finished": {"type": "started", "default_workflow_state": "Ready for Review"},
    "Rejected": {"type": "done", "default_workflow_state": "Completed"},
    "Accepted": {"type": "done", "default_workflow_state": "Completed"},
}


def default_workflow_id():
    workflow_id = None
    workflows = sc_get("/workflows")
    output_lines = []
    for workflow in workflows:
        if workflow["name"] == "Engineering":
            workflow_id = workflow["id"]

    if workflow_id is None:
        print(
            """Failed to find the default Story Workflow in your Shortcut workspace, please:
  1. Review the Shortcut Story Workflows printed below
  2. Copy the numeric ID of your desired Workflow below
  3. Paste it as the "workflow_id" value in your config.json file.
  4. Rerun initialize.py.
""",
            file=sys.stderr,
        )
        for workflow in workflows:
            output_lines.append('Workflow {id} : "{name}"'.format_map(workflow))
            for workflow_state in workflow["states"]:
                output_lines.append(
                    '    Worflow State {id} : [{type}] "{name}"'.format_map(
                        workflow_state
                    )
                )
        print("\n".join(output_lines), file=sys.stderr)
        return None
    else:
        return workflow_id


def populate_config():
    """
    Using data from the Shortcut workspace associated with the API token,
    populate a local `config.json` file if one does not already exist.

    Returns the configuration dictionary.
    """
    try:
        with open("config.json", "x", encoding="utf-8") as f:
            workflow_id = default_workflow_id()
            if workflow_id is None:
                sys.exit(1)
            data = {"workflow_id": default_workflow_id()}
            json.dump(data, f, indent=2)
            return data
    except FileExistsError:
        logger.debug(
            "Skipping populating config.json, because the file already exists."
        )
        with open("config.json", "r") as f:
            return json.load(f)


def validate_config(cfg):
    problems = []
    if sc_token is None:
        problems.append(
            "- You must define a SHORTCUT_API_TOKEN environment variable with your Shortcut API token."
        )
    if not isinstance(cfg, Mapping):
        problems.append(
            "- Your config.json file must be a JSON object, please check its formatting."
        )
        if cfg["workflow_id"] is None:
            problems.append(
                '- Your config.json file needs a "workflow_id" entry whose value is the ID of the Shortcut Story Workflow this importer should use.'
            )
    if problems:
        msg = "\n".join(problems)
        print(msg, file=sys.stderr)


def main():
    cfg = populate_config()
    validate_config(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
