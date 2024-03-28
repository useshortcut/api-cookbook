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
import csv
import json
import logging
import os
import sys

import requests

# Logging
logger = logging.getLogger(__name__)
# FIXME Make INFO default upon public release
logging.basicConfig(level=logging.DEBUG)  # Change to INFO or DEBUG as needed


def printerr(s):
    print(s, file=sys.stderr)


# File locations
shortcut_workflows_csv = "data/shortcut_workflows.csv"

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
pt_all_states = [
    "unscheduled",
    "unstarted",
    "planned",
    "started",
    "finished",
    "rejected",
    "accepted",
]


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


def populate_states_csv(states_csv_file, workflow_id):
    """
    Writes a CSV file mapping Pivotal Tracker's 7 story states to appropriate
    Shortcut Workflow States in your workspace.

    If an appropriate Shortcut Workflow State cannot be identified,
    an empty entry will be placed and this script will print out the IDs, types, and
    names of all the workflow states in your target workflow so that you can manually
    replace nulls with the appropriate IDs.
    """
    try:
        with open(states_csv_file, "x") as f:
            pt_state_mapping = pt_state_mapping_for_workflow(workflow_id)
            unhandled_pt_states = []
            writer = csv.DictWriter(
                f, ["pt_state", "shortcut_state_id", "shortcut_state_name"]
            )
            writer.writeheader()
            for pt_state in pt_all_states:
                mapping = pt_state_mapping[pt_state]
                if mapping is None:
                    unhandled_pt_states.append(pt_state)
                    writer.writerow(
                        {
                            "pt_state": pt_state,
                            "shortcut_state_id": "",
                            "shortcut_state_name": "",
                        }
                    )
                else:
                    writer.writerow(mapping)
            if unhandled_pt_states:
                exit_unhandled_pt_states(states_csv_file, unhandled_pt_states)
    except FileExistsError:
        unhandled_pt_states = []
        with open(states_csv_file, "r", newline="") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                if not row["shortcut_state_id"]:
                    unhandled_pt_states.append(row["pt_state"])
        if unhandled_pt_states:
            exit_unhandled_pt_states(states_csv_file, unhandled_pt_states)


def exit_unhandled_pt_states(states_csv_file, unhandled_pt_states):
    """
    If there are Pivotal Tracker states for which a Shorcut Workflow State
    mapping could not be determined, notify the user of this and provide
    instructions for rectifying the problem.
    """
    msg = "\n  - ".join(unhandled_pt_states)
    printerr(
        f"[Problem] These Pivotal Tracker states couldn't be automatically mapped to Shortcut workflow states:\n  - {msg}\n"
    )
    printerr(
        f"""To resolve this, please:
1. Review the Shortcut Workflow States printed below (also written to {shortcut_workflows_csv} for reference)
2. Copy the numeric IDs of Workflow States you want to map to Pivotal states where there are blanks in your {states_csv_file} file.
3. Save your {states_csv_file} file and rerun initalize.py to validate it.
"""
    )
    workflows = sc_get("/workflows")
    print_workflow_tree(workflows)
    sys.exit(1)


def pt_state_mapping_for_workflow(workflow_id):
    """
    Returns a dict mapping Pivotal Tracker story states to Shortcut Workflow States.
    If no mapping can be determined automatically for a particular Pivotal Tracker
    state, then it is mapped to `None`.
    """
    workflow = sc_get(f"/workflows/{workflow_id}")
    pt_state_mapping = {k: None for k in pt_all_states}
    for wf_state in workflow["states"]:
        match (wf_state["type"], wf_state["name"]):
            case ("unstarted", "Unscheduled"):
                pt_state_mapping["unscheduled"] = {
                    "pt_state": "unscheduled",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Unscheduled",
                }
            case ("unstarted", "Ready for Development"):
                pt_state_mapping["unstarted"] = {
                    "pt_state": "unstarted",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Ready for Development",
                }
                pt_state_mapping["planned"] = {
                    "pt_state": "planned",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Ready for Development",
                }
            case ("started", "In Development"):
                pt_state_mapping["started"] = {
                    "pt_state": "started",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "In Development",
                }
            case ("started", "Ready for Review"):
                pt_state_mapping["finished"] = {
                    "pt_state": "finished",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Ready for Review",
                }
            case ("done", "Completed"):
                pt_state_mapping["rejected"] = {
                    "pt_state": "rejected",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Completed",
                }
                pt_state_mapping["accepted"] = {
                    "pt_state": "accepted",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": "Completed",
                }

    return pt_state_mapping


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


def main():
    """
    Script entry-point for importing a Pivotal Tracker CSV export into a Shortcut workspace.
    """
    cfg = populate_config()
    validate_config(cfg)
    populate_states_csv(cfg["states_csv_file"], cfg["workflow_id"])
    print(
        f"""[Success] Pivotal Tracker export and local configuration have been validated.
          Identified %d epics, %d stories, %d iterations, and %d labels to import.

[Next] Run 'python pivotal_import.py' to see a dry-run or to perform the actual import into Shortcut."""
        % (0, 0, 0, 0)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
