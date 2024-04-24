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

import argparse
import csv
import difflib
import logging
import sys


from lib import *

# CLI arguments
parser = argparse.ArgumentParser(
    description="""Run this script with no arguments to configure how story state and users will be mapped from Pivotal to Shortcut.""",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")

# Logging
logger = logging.getLogger(__name__)


# Pivotal Tracker story states, including "planned" which is used
# if automatic Pivotal iterations are disabled.
pt_all_states = [
    "unscheduled",
    "unstarted",
    "planned",
    "started",
    "finished",
    "delivered",
    "rejected",
    "accepted",
]

# Pivotal Tracker story priorities. The "None" priority is not mapped
# because the importer interprets that as "do not set a Priority".
pt_all_priorities = [
    "p0 - critical",
    "p1 - high",
    "p2 - medium",
    "p3 - low",
]


def populate_priorities_csv(priorities_csv_file, priority_custom_field_id):
    """
    Writes a CSV file mapping Pivotal Tracker's 5 story priorities to appropriate
    Shortcut Custom Field Values.

    Shortcut workspaces are configured with a Custom Field called "Priority" by default
    that maps well to Pivotal's priority values. This is used if it is enabled in the
    workspace.

    If the default Priority Custom Field is disabled, then empty entries will be placed in the
    priorities_csv_file; all of the Custom Fields in your workspace will be written to
    data/shortcut_custom_fields.csv so that you can review them, and then you can manually
    paste the Custom Field Value IDs into the priorities_csv_file to specify the mapping of
    Pivotal priority to Shortcut Custom Field Value that you want.
    """
    try:
        with open(priorities_csv_file, "x") as f:
            pt_priority_mapping = pt_priority_mapping_for_custom_field(
                priority_custom_field_id
            )
            unmapped_pt_priorities = []
            writer = csv.DictWriter(
                f,
                [
                    "pt_priority",
                    "shortcut_custom_field_value_id",
                    "shortcut_custom_field_value_name",
                ],
            )
            writer.writeheader()
            for pt_priority in pt_all_priorities:
                mapping = pt_priority_mapping[pt_priority]
                if mapping is None:
                    unmapped_pt_priorities.append(pt_priority)
                    writer.writerow(
                        {
                            "pt_priority": pt_priority,
                            "shortcut_custom_field_value_id": "",
                            "shortcut_custom_field_value_name": "",
                        }
                    )
                else:
                    writer.writerow(mapping)
            if unmapped_pt_priorities:
                exit_unmapped_pt_priorities(priorities_csv_file, unmapped_pt_priorities)
    except FileExistsError:
        unmapped_pt_priorities = []
        with open(priorities_csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["shortcut_custom_field_value_id"]:
                    unmapped_pt_priorities.append(row["pt_priority"])
        if unmapped_pt_priorities:
            exit_unmapped_pt_priorities(priorities_csv_file, unmapped_pt_priorities)


def exit_unmapped_pt_priorities(priorities_csv_file, unmapped_pt_priorities):
    """
    If there are Pivotal Tracker priorities for which a Shortcut Custom Field Value
    mapping could not be determined, notify the user of this and provide
    instructions for rectifying the problem.
    """
    msg = "\n  - ".join(f'"{s}"' for s in unmapped_pt_priorities)
    printerr(
        f"[Problem] These Pivotal Tracker priorities couldn't be automatically mapped to Shortcut Custom Field Values:\n  - {msg}\n"
    )
    printerr(
        f"""To resolve this, please:
1. Review the Shortcut Custom Fields written to {shortcut_custom_fields_csv}
2. Copy the UUIDs of Custom Field Values (custom_field_value_id column in the CSV) that you want to map to Pivotal priorities where there are blanks in your {priorities_csv_file} file.
3. Save your {priorities_csv_file} file and rerun initalize.py to validate it.
"""
    )
    sys.exit(1)


def pt_priority_mapping_for_custom_field(priority_custom_field_id):
    """
    Returns a dict mapping Pivotal Tracker story priorities to Shortcut Custom Field Values.
    If no mapping can be determined automatically for a particular Pivotal Tracker
    priority, then it is mapped to `None`.

    Instead of relying on editable names like we must for Shortcut Workflow States,
    Custom Field Values have a `position`, and for the built-in Priority Custom Field,
    those positions are fixed.
    """
    custom_field = sc_get(f"/custom-fields/{priority_custom_field_id}")
    pt_priority_mapping = {k: None for k in pt_all_priorities}
    for custom_field_value in custom_field["values"]:
        match (custom_field_value["position"]):
            case 0:
                pt_priority_mapping["p0 - critical"] = {
                    "pt_priority": "p0 - critical",
                    "shortcut_custom_field_value_id": custom_field_value["id"],
                    # Default is "Highest"
                    "shortcut_custom_field_value_name": custom_field_value["value"],
                }
            case 1:
                pt_priority_mapping["p1 - high"] = {
                    "pt_priority": "p1 - high",
                    "shortcut_custom_field_value_id": custom_field_value["id"],
                    # Default is "High"
                    "shortcut_custom_field_value_name": custom_field_value["value"],
                }
            case 2:
                pt_priority_mapping["p2 - medium"] = {
                    "pt_priority": "p2 - medium",
                    "shortcut_custom_field_value_id": custom_field_value["id"],
                    # Default is "Medium"
                    "shortcut_custom_field_value_name": custom_field_value["value"],
                }
            case 3:
                pt_priority_mapping["p3 - low"] = {
                    "pt_priority": "p3 - low",
                    "shortcut_custom_field_value_id": custom_field_value["id"],
                    # Default is "Low"
                    "shortcut_custom_field_value_name": custom_field_value["value"],
                }

    return pt_priority_mapping


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
            unmapped_pt_states = []
            writer = csv.DictWriter(
                f, ["pt_state", "shortcut_state_id", "shortcut_state_name"]
            )
            writer.writeheader()
            for pt_state in pt_all_states:
                mapping = pt_state_mapping[pt_state]
                if mapping is None:
                    unmapped_pt_states.append(pt_state)
                    writer.writerow(
                        {
                            "pt_state": pt_state,
                            "shortcut_state_id": "",
                            "shortcut_state_name": "",
                        }
                    )
                else:
                    writer.writerow(mapping)
            if unmapped_pt_states:
                exit_unmapped_pt_states(states_csv_file, unmapped_pt_states)
    except FileExistsError:
        unmapped_pt_states = []
        with open(states_csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["shortcut_state_id"]:
                    unmapped_pt_states.append(row["pt_state"])
        if unmapped_pt_states:
            exit_unmapped_pt_states(states_csv_file, unmapped_pt_states)


def exit_unmapped_pt_states(states_csv_file, unmapped_pt_states):
    """
    If there are Pivotal Tracker states for which a Shorcut Workflow State
    mapping could not be determined, notify the user of this and provide
    instructions for rectifying the problem.
    """
    msg = "\n  - ".join(f'"{s}"' for s in unmapped_pt_states)
    printerr(
        f"[Problem] These Pivotal Tracker states couldn't be automatically mapped to Shortcut workflow states:\n  - {msg}\n"
    )
    printerr(
        f"""To resolve this, please:
1. Review the Shortcut Workflow States written to {shortcut_workflows_csv}
2. Copy the numeric IDs of Workflow States (workflow_state_id column in the CSV) that you want to map to Pivotal states where there are blanks in your {states_csv_file} file.
3. Save your {states_csv_file} file and rerun initalize.py to validate it.
"""
    )
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
            case ("backlog", "Backlog"):
                pt_state_mapping["unscheduled"] = {
                    "pt_state": "unscheduled",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
            case ("unstarted", "To Do"):
                pt_state_mapping["unstarted"] = {
                    "pt_state": "unstarted",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
                pt_state_mapping["planned"] = {
                    "pt_state": "planned",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
            case ("started", "In Progress"):
                pt_state_mapping["started"] = {
                    "pt_state": "started",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
            case ("started", "In Review"):
                pt_state_mapping["finished"] = {
                    "pt_state": "finished",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
                pt_state_mapping["delivered"] = {
                    "pt_state": "delivered",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
            case ("done", "Done"):
                pt_state_mapping["rejected"] = {
                    "pt_state": "rejected",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }
                pt_state_mapping["accepted"] = {
                    "pt_state": "accepted",
                    "shortcut_state_id": wf_state["id"],
                    "shortcut_state_name": wf_state["name"],
                }

    return pt_state_mapping


def populate_users_csv(users_csv_file, pt_csv_file):
    """
    Writes a CSV file mapping the users found in the Pivotal Tracker export with
    users in your Shortcut Workspace.

    The Pivotal export only includes users' full names, so this script makes a best-effort
    attempt to match those names with the names of users in your Shortcut Workspace.

    If a matching full name is found, it will be mapped automatically. The mapping
    is from Pivotal user name to Shortcut user email address.

    If a matching full name is not found, a blank will be written to your users.csv file.
    In order for this importer to work, you must supply an email address for each of
    these blanks. If the user is one you don't plan to have in Shortcut (e.g., a former
    employee whose Pivotal account is disabled but who is still a participant on Pivotal
    stories), make sure you either (a) run this importer while still in your Shortcut trial
    period, or (b) reach out to support@shortcut.com to request assistance so you're not
    billed for extraneous users.
    """
    sc_users = fetch_members()
    user_matching_map = _build_user_matching_map(sc_users)
    try:
        with open(users_csv_file, "x") as f:
            pt_all_users = sorted(extract_pt_users(pt_csv_file))
            unmapped_pt_users = []
            writer = csv.DictWriter(
                f, ["pt_user_name", "shortcut_user_email", "shortcut_user_mention_name"]
            )
            writer.writeheader()
            for pt_user in pt_all_users:
                user_info = find_sc_user_from_pt_user(pt_user, user_matching_map)
                email = ""
                mention_name = ""
                if not user_info:
                    unmapped_pt_users.append(pt_user)
                else:
                    email = user_info["email"]
                    mention_name = user_info["mention_name"]

                writer.writerow(
                    {
                        "pt_user_name": pt_user,
                        "shortcut_user_email": email,
                        "shortcut_user_mention_name": mention_name,
                    }
                )
            if unmapped_pt_users:
                exit_unmapped_pt_users(users_csv_file, unmapped_pt_users, sc_users)
    except FileExistsError:
        unmapped_pt_users = []
        uninvited_pt_users = []
        invited_emails = set(
            [user_info["email"] for user_info in user_matching_map.values()]
        )
        with open(users_csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row["shortcut_user_email"]:
                    unmapped_pt_users.append(row["pt_user_name"])
                elif row["shortcut_user_email"] not in invited_emails:
                    uninvited_pt_users.append(row["shortcut_user_email"])
        if unmapped_pt_users:
            exit_unmapped_pt_users(users_csv_file, unmapped_pt_users, sc_users)
        if uninvited_pt_users:
            exit_uninvited_pt_users(uninvited_pt_users)
    return 0


def parse_comment_author(s):
    """
    Extract the author from a Pivotal comment.

    Returns None if the comment wasn't parsable.
    """
    comment_data = parse_comment(s)
    if comment_data is not None:
        return comment_data["author"]
    else:
        return None


user_cols = {
    "requested by": identity,
    "owned by": identity,
    "reviewer": identity,
    "comment": parse_comment_author,
}


def extract_pt_users_from_row(row, header):
    """
    Extract all Pivotal users from a given CSV row.

    Pivotal's CSV is structured such that only one user is specified
    per "cell" of the sheet.

    Columns that include a user:
     - Requested By (value itself)
     - Owned By (value itself)
     - Reviewer (value itself)
     - Comment (authorship is indicated by a suffix)
    """
    users_in_row = set()
    for ix, val in enumerate(row):
        v = val.strip()
        if not v:
            continue

        col = header[ix]
        if col in user_cols:
            translator = user_cols[col]
            user = translator(v)
            if user is not None:
                users_in_row.add(user)
    return users_in_row


def extract_pt_users(pt_csv_file):
    """
    Given the Pivotal export CSV, return a unique set of all users found in all rows.
    """
    pt_users = set()
    with open(pt_csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            pt_users.update(extract_pt_users_from_row(row, header))
    return pt_users


def _casefold_then_remove_spaces_and_specials(s):
    return re.sub(r"[\W_]", "", s.casefold())


def find_sc_user_from_pt_user(pt_user, user_map):
    """
    Return the Shortcut user that maps to the given Pivotal user.
    Compares full names (since that is was the Pivotal export contains).

    Return None if a suitable Shortcut user could not be identified.
    """
    simplified_user = _casefold_then_remove_spaces_and_specials(pt_user)

    user_info = user_map.get(simplified_user)
    if user_info:
        logger.debug("Found user %s: %s", pt_user, user_info)
        return user_info

    all_identifiers = user_map.keys()

    best_matches = difflib.get_close_matches(simplified_user, all_identifiers)
    if best_matches:
        return user_map[best_matches[0]]

    return None


def _build_user_matching_map(user_info_list):
    user_map = {}
    indexed_keys = ["name", "mention_name"]
    transformers = [identity, _casefold_then_remove_spaces_and_specials]
    for user_info in user_info_list:
        for k in indexed_keys:
            val = user_info.get(k)
            if val:
                for transformer in transformers:
                    transformed_val = transformer(val)
                    if transformed_val and transformed_val not in user_map:
                        user_map[transformed_val] = user_info

    return user_map


def exit_unmapped_pt_users(users_csv_file, unmapped_pt_users, user_info_list):
    """
    If there are Pivotal Tracker users which could not be mapped automatically
    to Shortcut users, notify the user of this and provide instructions for
    rectifying the problem.
    """
    msg = "\n  - ".join(unmapped_pt_users)
    printerr(
        f"[Problem] These Pivotal Tracker users couldn't be automatically mapped to Shortcut users in your workspace:\n  - {msg}\n"
    )
    printerr(
        f"""To resolve this, please:
1. Review the Shortcut users in your workspace, written to {shortcut_users_csv}
2. For users you've already invited to Shortcut, copy their email address from {shortcut_users_csv}
   and fill in the appropriate blank entries in {users_csv_file} for them.
3. For users you haven't already invited to Shortcut, you can enter their email addresses manually into
   {users_csv_file}.
3. Save your {users_csv_file} file and rerun initalize.py to validate it.

Once you've resolved these problems, the initialize.py script will also print out
a list of email addresses that you've provided but aren't in your Shortcut workspace yet,
so you can easily invite them to your workspace.
"""
    )
    with open(shortcut_users_csv, "w") as f:
        writer = csv.DictWriter(
            f,
            ["shortcut_user_name", "shortcut_user_email", "shortcut_user_mention_name"],
        )
        writer.writeheader()
        for user_info in user_info_list:
            writer.writerow(
                {
                    "shortcut_user_name": user_info["name"],
                    "shortcut_user_email": user_info["email"],
                    "shortcut_user_mention_name": user_info["mention_name"],
                }
            )
    sys.exit(1)


def exit_uninvited_pt_users(uninvited_pt_users):
    """
    Users can add people to data/users.csv that have not been added to their Shortcut
    workspace. This step identifies that situation and provides instructions to the user.
    """
    msg = "\n  ".join(uninvited_pt_users)
    printerr(
        f"[Problem] No users in your Shortcut workspace have these emails:\n  {msg}\n"
    )
    printerr(
        f"""To resolve this, invite these people to your Shortcut workspace.

1. Copy the list of emails written to {emails_to_invite}
2. Navigate to https://app.shortcut.com/settings/users/invite
3. Click "Invite Emails".
4. Paste the list of emails into the text area.
5. Submit the form.

Run the initialize.py script again to verify that all users have been mapped and
have accounts in your Shortcut workspace.
"""
    )
    with open(emails_to_invite, "w") as f:
        writer = csv.DictWriter(f, ["email_to_invite"])
        writer.writeheader()
        for email in uninvited_pt_users:
            writer.writerow({"email_to_invite": email})
    sys.exit(1)


def main(argv):
    """
    Script entry-point for initializing an import of Pivotal data into Shortcut.

    Once initialized, use pivotal_import.py to see a dry-run and perform the import.
    """
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # Configuration consists of the environment variable SHORTCUT_API_TOKEN and all values
    # found in the local config.json file (which is written by this script if absent).
    cfg = load_config()

    # Ensure local data/shortcut_*.csv files are populated with user's workspace data,
    # so they can review what's available for mapping in the steps that follow.
    custom_fields = sc_get("/custom-fields")
    write_custom_fields_tree(custom_fields)
    groups = sc_get("/groups")
    write_groups_tree(groups)
    workflows = sc_get("/workflows")
    write_workflows_tree(workflows)

    # Populate local data/priorities.csv, data/states.csv, and data/users.csv files,
    # automatically where possible, and print problems to the console where mappings
    # are not 100% complete.
    populate_priorities_csv(cfg["priorities_csv_file"], cfg["priority_custom_field_id"])
    populate_states_csv(cfg["states_csv_file"], cfg["workflow_id"])
    populate_users_csv(cfg["users_csv_file"], cfg["pt_csv_file"])
    print(
        "[Success] Pivotal Tracker export and local configuration have been validated."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
