"""Helper functions for communicating with the Shortcut API.

Expects the Shortcut token to be set in the SHORTCUT_API_TOKEN
environment variable.

"""

from collections.abc import Mapping
from datetime import datetime
import re
import sys
import csv
import json
import os
import logging

import requests

# FIXME Make INFO default upon public release
logging.basicConfig(level=logging.DEBUG)  # Change to INFO or DEBUG as needed

# Logging
logger = logging.getLogger(__name__)

# API Helpers
sc_token = os.getenv("SHORTCUT_API_TOKEN")
api_url_base = "https://api.app.shortcut.com/api/v3"
headers = {
    "Shortcut-Token": sc_token,
    "Accept": "application/json; charset=utf-8",
    "Content-Type": "application/json",
}


def sc_get(path, params={}):
    """
    Make a GET api call.

    Serializes params as url query parameters.
    """
    url = api_url_base + path
    logger.debug("GET url=%s params=%s headers=%s" % (url, params, headers))
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def sc_post(path, data={}):
    """Make a POST api call.

    Typically used to create an entity. Other types of requests that
    are either expensive or need consistent parameter serialization
    may also use a POST request.  Serializes params as JSON in the
    request body.

    """
    url = api_url_base + path
    logger.debug("POST url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def sc_put(path, data={}):
    """
    Make a PUT api call.

    Typically used to update an entity.
    Serializes params as JSON in the request body.
    """
    url = api_url_base + path
    logger.debug("PUT url=%s params=%s headers=%s" % (url, data, headers))
    resp = requests.put(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()


def printerr(s):
    print(s, file=sys.stderr)


# File locations
shortcut_workflows_csv = "data/shortcut_workflows.csv"
shortcut_users_csv = "data/shortcut_users.csv"
emails_to_invite = "data/emails_to_invite.csv"


def print_workflow_tree(workflows):
    """
    Print and write to `shortcut_workflows_csv` the content of all Workflows
    in the user's Shortcut workspace, including all Workflow States and their IDs.
    """
    output_lines = []
    with open(shortcut_workflows_csv, "w") as f:
        writer = csv.DictWriter(
            f,
            [
                "workflow_name",
                "workflow_id",
                "workflow_state_name",
                "workflow_state_id",
            ],
        )
        writer.writeheader()
        for workflow in workflows:
            output_lines.append('Workflow {id} : "{name}"'.format_map(workflow))
            for workflow_state in workflow["states"]:
                writer.writerow(
                    {
                        "workflow_name": workflow["name"],
                        "workflow_id": workflow["id"],
                        "workflow_state_name": workflow_state["name"],
                        "workflow_state_id": workflow_state["id"],
                    }
                )
                output_lines.append(
                    '    Workflow State {id} : [{type}] "{name}"'.format_map(
                        workflow_state
                    )
                )
    printerr("\n".join(output_lines))


def default_workflow_id():
    """
    Determine the default Shortcut Workflow, or provide instructions to the user
    to select a specific Workflow if the default "Engineering" Workflow is not
    found.
    """
    workflow_id = None
    workflows = sc_get("/workflows")
    for workflow in workflows:
        if workflow["name"] == "Engineering":
            workflow_id = workflow["id"]

    if workflow_id is None:
        printerr(
            f"""[Problem] Failed to find the default Story Workflow in your Shortcut workspace, please:
  1. Review the Shortcut Workflows printed below (also written to {shortcut_workflows_csv} for reference)
  2. Copy the numeric ID of your desired Workflow below
  3. Paste it as the "workflow_id" value in your config.json file.
  4. Rerun initialize.py.
"""
        )
        print_workflow_tree(workflows)
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
            data = {
                "pt_csv_file": "data/pivotal_export.csv",
                "states_csv_file": "data/states.csv",
                "users_csv_file": "data/users.csv",
                "workflow_id": workflow_id,
            }
            json.dump(data, f, indent=2)
            if workflow_id is None:
                sys.exit(1)
            return data
    except FileExistsError:
        logger.debug(
            "Skipping populating config.json, because the file already exists."
        )
        with open("config.json", "r") as f:
            return json.load(f)


def validate_config(cfg):
    """
    Validate all configuration and setup, printing a description of problems
    and exiting with 1 if any problems found.
    """
    problems = []
    if sc_token is None:
        problems.append(
            "- You must define a SHORTCUT_API_TOKEN environment variable with your Shortcut API token."
        )
    if not os.path.isfile("data/pivotal_export.csv"):
        problems.append(
            "- Your Pivotal Tracker project export must be located at data/pivotal_export.csv"
        )
    if not isinstance(cfg, Mapping):
        problems.append(
            "- Your config.json file must be a JSON object, please check its formatting."
        )
    else:
        if "workflow_id" not in cfg or not cfg["workflow_id"]:
            problems.append(
                '- Your config.json file needs a "workflow_id" entry whose value is the ID of the Shortcut Workflow this importer should use.'
            )
        if "pt_csv_file" not in cfg or not cfg["pt_csv_file"]:
            problems.append(
                '- Your config.json file needs a "pt_csv_file" entry whose value is the path to your Pivotal Tracker export CSV.'
            )
    if problems:
        msg = "\n".join(problems)
        printerr(f"Problems:\n{msg}")
        sys.exit(1)


def load_config():
    cfg = populate_config()
    validate_config(cfg)
    return cfg


#
# Pivotal Parsing Functions
#


def parse_comment(s):
    """Parse comment text into a dict with entries:
    - text (comment text, excluding final authorship content)
    - author (Pivotal user name of commenter)
    - created_at (date time, ISO 8601)"""
    match = re.match(r"(.*)\((.*) - (.*)\)", s, re.DOTALL)
    if match:
        txt = match.group(1)
        if txt is not None:
            txt = txt.strip()
        author = match.group(2)
        if author is not None:
            author = author.strip()
        created_at = match.group(3)
        if created_at is not None:
            created_at = parse_date(created_at.strip())
        return {"text": txt, "author": author, "created_at": created_at}
    else:
        return {"text": s}


def parse_date(d: str):
    """Parse the string as a datetime, then return as a string in ISO 8601 format."""
    return datetime.strptime(d, "%b %d, %Y").isoformat()
