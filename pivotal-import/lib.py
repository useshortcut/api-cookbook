"""Helper functions for communicating with the Shortcut API.

Expects the Shortcut token to be set in the SHORTCUT_API_TOKEN
environment variable.

"""

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
import mimetypes
import re
import sys
import csv
import json
import os
import logging

from pyrate_limiter import Duration, InMemoryBucket, Limiter, Rate
import requests

# Logging
logger = logging.getLogger(__name__)

# Rate limiting. See https://developer.shortcut.com/api/rest/v3#Rate-Limiting
# The Shortcut API limit is 200 per minute; the 200th request within 60 seconds
# will receive an HTTP 429 response.
#
# The rate limiting config below sets an in-memory limit that is just below
# Shortcut's rate limit to reduce the possibility of being throttled, and sets
# the amount of time it will wait once it reaches that limit to just
# over a minute to account for possible computer clock differences.
max_requests_per_minute = 200
rate = Rate(max_requests_per_minute - 5, Duration.MINUTE)
bucket = InMemoryBucket([rate])
max_limiter_delay_seconds = 70
limiter = Limiter(
    bucket, raise_when_fail=True, max_delay=Duration.SECOND * max_limiter_delay_seconds
)


def rate_mapping(*args, **kwargs):
    return "shortcut-api-request", 1


rate_decorator = limiter.as_decorator()


def print_rate_limiting_explanation():
    printerr(
        f"""[Note] This importer adheres to the Shortcut API rate limit of {max_requests_per_minute} requests per minute.
       It may pause for up to {max_limiter_delay_seconds} seconds during processing to avoid request throttling."""
    )


# API Helpers
sc_token = os.getenv("SHORTCUT_API_TOKEN")
api_url_base = "https://api.app.shortcut.com/api/v3"
headers = {
    "Shortcut-Token": sc_token,
    "Accept": "application/json; charset=utf-8",
    "Content-Type": "application/json",
    "User-Agent": "pivotal-to-shortcut/0.0.1-alpha2",
}


@rate_decorator(rate_mapping)
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


@rate_decorator(rate_mapping)
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
    logger.debug(f"POST response: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    return resp.json()


@rate_decorator(rate_mapping)
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


@rate_decorator(rate_mapping)
def sc_upload_files(files):
    """Upload and associate `files` with the story with given `story_id`"""
    url = f"{api_url_base}/files"
    logger.debug("POST url=%s files=%s headers=%s" % (url, files, headers))
    file_entities = []
    for file in files:
        try:
            with open(file, "rb") as f:
                logger.debug(f"File: {f.name} {guess_mime_type(f.name)}")
                resp = requests.post(
                    url,
                    headers=dissoc(headers, "Content-Type")
                    | {"Accept": "application/json"},
                    files=[
                        (
                            "file0",
                            (os.path.basename(f.name), f, guess_mime_type(f.name)),
                        )
                    ],
                )
                logger.debug(f"POST response: {resp.status_code} {resp.text}")
                resp.raise_for_status()
                resp_json = resp.json()
                file_entities.append(resp_json[0])
        except:
            printerr(f"[Warning] Failed to upload file {file}")
    return file_entities


@rate_decorator(rate_mapping)
def sc_delete(path):
    """
    Make a DELETE api call.

    Typically used to delete an entity.
    """
    url = api_url_base + path
    logger.debug("DELETE url=%s headers=%s" % (url, headers))
    resp = requests.delete(url, headers=headers)
    resp.raise_for_status()
    return resp


def printerr(s):
    print(s, file=sys.stderr)


# File locations
data_pivotal_export_csv = "data/pivotal_export.csv"
data_priorities_csv = "data/priorities.csv"
data_states_csv = "data/states.csv"
data_users_csv = "data/users.csv"
emails_to_invite = "data/emails_to_invite.csv"
shortcut_custom_fields_csv = "data/shortcut_custom_fields.csv"
shortcut_groups_csv = "data/shortcut_groups.csv"
shortcut_imported_entities_csv = "data/shortcut_imported_entities.csv"
shortcut_users_csv = "data/shortcut_users.csv"
shortcut_workflows_csv = "data/shortcut_workflows.csv"


def write_custom_fields_tree(custom_fields):
    """
    Write to `shortcut_custom_fields_csv` the content of all Custom Fields
    in the user's Shortcut workspace, including all Custom Field Values and their IDs.
    """
    with open(shortcut_custom_fields_csv, "w") as f:
        writer = csv.DictWriter(
            f,
            [
                "custom_field_name",
                "custom_field_id",
                "custom_field_value_name",
                "custom_field_value_id",
            ],
        )
        writer.writeheader()
        for custom_field in custom_fields:
            if custom_field["enabled"]:
                for custom_field_value in custom_field["values"]:
                    writer.writerow(
                        {
                            "custom_field_name": custom_field["name"],
                            "custom_field_id": custom_field["id"],
                            "custom_field_value_name": custom_field_value["value"],
                            "custom_field_value_id": custom_field_value["id"],
                        }
                    )


def write_groups_tree(groups):
    """
    Write to `shortcut_groups_csv` the content of all Teams/Groups
    in the user's Shortcut workspace.
    """
    with open(shortcut_groups_csv, "w") as f:
        writer = csv.DictWriter(
            f,
            [
                "group_name",
                "group_id",
            ],
        )
        writer.writeheader()
        for group in groups:
            writer.writerow({"group_name": group["name"], "group_id": group["id"]})


def write_workflows_tree(workflows):
    """
    Write to `shortcut_workflows_csv` the content of all Workflows
    in the user's Shortcut workspace, including all Workflow States and their IDs.
    """
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
            for workflow_state in workflow["states"]:
                writer.writerow(
                    {
                        "workflow_name": workflow["name"],
                        "workflow_id": workflow["id"],
                        "workflow_state_name": workflow_state["name"],
                        "workflow_state_id": workflow_state["id"],
                    }
                )


def default_group_id():
    """
    Determine the default Shortcut Team (Group in the parlance of Shortcut's REST API),
    or provide instructions to the user to select a specific Team if the default Team
    isn't found.
    """
    group_id = None
    groups = sc_get("/groups")
    for group in groups:
        if group["name"] == "Team 1":
            group_id = group["id"]

    if group_id is None:
        printerr(
            f"""
[Warning] Failed to find a Team (called "Group" in the Shortcut API) to automatically assign imported stories and epics to.
          If you would like to assign a Team/Group for the stories and epics you import, please:
  1. Review the Shortcut Teams/Groups printed below (also written to {shortcut_groups_csv} for reference).
  2. Copy the numeric ID of your desired Team/Group (group_id column in the CSV).
  3. Paste it as the "group_id" value in your config.json file.
  4. Rerun initialize.py.
"""
        )
        return None
    else:
        return group_id


def default_priority_custom_field_id():
    """
    Shortcut Workspaces have a built-in "Priority" Custom Field. However,
    users are permitted to disable this in their workspace.

    Return the ID for the Priority Custom Field if it is enabled, else
    return None.
    """
    priority_custom_field_id = None
    custom_fields = sc_get("/custom-fields")
    for custom_field in custom_fields:
        if "canonical_name" in custom_field and custom_field["canonical_name"] == "priority" and custom_field["enabled"]:
            priority_custom_field_id = custom_field["id"]

    if priority_custom_field_id is None:
        printerr(
            f"""
[Problem] The Priority custom field is disabled or not found in your Shortcut workspace. Please:
 1. Review the Shortcut Custom Fields printed below (also written to {shortcut_custom_fields_csv} for reference).
 2. Copy the UUID of your desired Custom Field (custom_field_id column in the CSV).
 3. Paste it as the "priority_custom_field_id" value in your config.json file.
 4. Rerun initialize.py.
"""
        )
        return None
    else:
        return priority_custom_field_id


def default_workflow_id():
    """
    Determine the default Shortcut Workflow, or provide instructions to the user
    to select a specific Workflow if the default "Standard" Workflow is not
    found.
    """
    workflow_id = None
    workflows = sc_get("/workflows")
    for workflow in workflows:
        if workflow["name"] == "Standard":
            workflow_id = workflow["id"]

    if workflow_id is None:
        printerr(
            f"""
[Problem] Failed to find the default Story Workflow in your Shortcut workspace, please:
  1. Review the Shortcut Workflows printed below (also written to {shortcut_workflows_csv} for reference).
  2. Copy the numeric ID of your desired Workflow (workflow_id column in the CSV).
  3. Paste it as the "workflow_id" value in your config.json file.
  4. Rerun initialize.py.
"""
        )
        return None
    else:
        return workflow_id

def current_member_id():
    """
    Returns the member id that this token belongs to.
    """
    member = sc_get("/member")
    return member["id"]


def populate_config():
    """
    Using data from the Shortcut workspace associated with the API token,
    populate a local `config.json` file if one does not already exist.

    Returns the configuration dictionary.
    """
    try:
        with open("config.json", "x", encoding="utf-8") as f:
            group_id = default_group_id()
            priority_custom_field_id = default_priority_custom_field_id()
            workflow_id = default_workflow_id()
            data = {
                "group_id": group_id,
                "pt_csv_file": data_pivotal_export_csv,
                "priorities_csv_file": data_priorities_csv,
                "priority_custom_field_id": priority_custom_field_id,
                "states_csv_file": data_states_csv,
                "users_csv_file": data_users_csv,
                "workflow_id": workflow_id,
            }
            json.dump(data, f, indent=2)
            # Errors are printed to the console in the default_* functions above
            if workflow_id is None or priority_custom_field_id is None:
                sys.exit(1)
            return data
    except FileExistsError:
        logger.debug(
            "Skipping populating config.json, because the file already exists."
        )
        return read_config_from_disk("config.json")


def read_config_from_disk(cfg_file):
    try:
        with open(cfg_file, "r") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError as err:
        printerr(
            f"[Problem] Tried to parse {cfg_file} as JSON but encountered an error:"
        )
        printerr(f"{err}")
        return None


def validate_environment():
    """
    Validate environment settings that must be in place to populate and load
    the default configuration for this importer.
    """
    problems = []
    if sc_token is None:
        problems.append(
            " - You must define a SHORTCUT_API_TOKEN environment variable with your Shortcut API token."
        )
    if not os.path.isfile("data/pivotal_export.csv"):
        problems.append(
            " - Your Pivotal Tracker project export must be located at data/pivotal_export.csv"
        )
    if problems:
        msg = "\n".join(problems)
        printerr(f"Problems:\n{msg}")
        sys.exit(1)


def validate_config(cfg):
    """
    Validate all configuration and setup, printing a description of problems
    and exiting with 1 if any problems found.
    """
    problems = []
    if not isinstance(cfg, Mapping):
        problems.append(
            " - Your config.json file must be a JSON object, please check its formatting."
        )
    else:
        if "group_id" not in cfg:
            problems.append(
                f' - Your config.json file needs a "group_id" entry, which may be set to `null`, or may be set to one of the Teams/Groups listed in {shortcut_groups_csv}'
            )
        if "priorities_csv_file" not in cfg or not cfg["priorities_csv_file"]:
            problems.append(
                f' - Your config.json is missing an expected field "priorities_csv_file" whose default value is {data_priorities_csv}. Add it manually or run `make clean import` to regenerate a valid config.json'
            )
        if "priority_custom_field_id" not in cfg or not cfg["priority_custom_field_id"]:
            problems.append(
                f' - Your config.json file needs a "priority_custom_field_id" entry whose value is the ID of the built-in Shortcut Custom Field called "Priority" which you can find in {shortcut_custom_fields_csv}'
            )
        if "pt_csv_file" not in cfg or not cfg["pt_csv_file"]:
            problems.append(
                f' - Your config.json file needs a "pt_csv_file" entry whose default value is {data_pivotal_export_csv}. Add it manually or run `make clean import` to regenerate a valid config.json'
            )
        if "states_csv_file" not in cfg or not cfg["states_csv_file"]:
            problems.append(
                f' - Your config.json is missing an expected field "states_csv_file" whose default value is {data_states_csv}. Add it manually or run `make clean import` to regenerate a valid config.json'
            )
        if "users_csv_file" not in cfg or not cfg["users_csv_file"]:
            problems.append(
                f' - Your config.json is missing an expected field "users_csv_file" whose default value is {data_users_csv}. Add it manually or run `make clean import` to regenerate a valid config.json'
            )
        if "workflow_id" not in cfg or not cfg["workflow_id"]:
            problems.append(
                f' - Your config.json file needs a "workflow_id" entry whose value is the ID of the Shortcut Workflow this importer should use, refer to {shortcut_workflows_csv} to pick one.'
            )
    if problems:
        msg = "\n".join(problems)
        printerr(f"Problems:\n{msg}")
        sys.exit(1)
    else:
        return cfg


def load_config():
    validate_environment()
    return validate_config(populate_config())


def get_user_info(member):
    profile = member["profile"]
    return {
        "name": profile.get("name"),
        "mention_name": profile.get("mention_name"),
        "email": profile.get("email_address"),
        # the unique id of the member
        "id": member["id"],
        # partial or full based on acceptance state
        "state": member["state"],
    }


def fetch_members():
    return [get_user_info(member) for member in sc_get("/members")]


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
            created_at = parse_date_time(created_at.strip())
        return {"text": txt, "author": author, "created_at": created_at}
    else:
        return {"text": s}


def parse_date(d: str):
    """Parse the string as a date, then return as a string in ISO 8601 format."""
    dt = datetime.strptime(d, "%b %d, %Y").date()
    return dt.strftime("%Y-%m-%d")


def parse_date_time(d: str):
    """Parse the string as a datetime, then return as a string in ISO 8601 format."""
    return datetime.strptime(d, "%b %d, %Y").isoformat()


### Utility functions


def dissoc(dict, key_to_remove):
    """Return a copy of `dict` with `key_to_remove` absent."""
    d = deepcopy(dict)
    if key_to_remove in d:
        del d[key_to_remove]
    return d


def guess_mime_type(file_name):
    (mime_type, _) = mimetypes.guess_type(file_name)
    return mime_type if mime_type is not None else "application/octet-stream"


def identity(x):
    return x


def print_stats(stats):
    plurals = {
        "story": "stories",
        "epic": "epics",
        "file": "files",
        "iteration": "iterations",
    }
    for k, v in stats.items():
        plural = plurals.get(k, k + "s")
        print(f"  - {plural.capitalize()} : {v}")
