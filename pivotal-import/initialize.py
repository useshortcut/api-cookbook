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
import logging
import sys

from lib import *

# Logging
logger = logging.getLogger(__name__)


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
    msg = "\n  - ".join(unmapped_pt_states)
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
    try:
        with open(users_csv_file, "x") as f:
            pt_all_users = sorted(extract_pt_users(pt_csv_file))
            unmapped_pt_users = []
            sc_user_to_email = fetch_sc_user_to_email()
            writer = csv.DictWriter(f, ["pt_user_name", "shortcut_user_email"])
            writer.writeheader()
            for pt_user in pt_all_users:
                email = sc_user_to_email.get(pt_user, "")
                if email == "":
                    unmapped_pt_users.append(pt_user)
                writer.writerow({"pt_user_name": pt_user, "shortcut_user_email": email})
            if unmapped_pt_users:
                exit_unmapped_pt_users(
                    users_csv_file, unmapped_pt_users, sc_user_to_email
                )
    except FileExistsError:
        logger.debug("[NOT IMPLEMENTED] populate_users_csv when exists")
    return 0


def identity(x):
    return x


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
    pt_users = set()
    with open(pt_csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            pt_users.update(extract_pt_users_from_row(row, header))
    return pt_users


def fetch_sc_user_to_email():
    """
    Returns a dict mapping the Shortcut user's name to their email address
    for all members in the Shortcut workspace.
    """
    return {
        member["profile"]["name"]: member["profile"]["email_address"]
        for member in sc_get("/members")
    }


def exit_unmapped_pt_users(users_csv_file, unmapped_pt_users, sc_user_to_email):
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
1. Review the Shortcut users in your workspace, written to {shortcut_users_csv} for your convenience.
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
        writer = csv.DictWriter(f, ["shortcut_user_name", "shortcut_user_email"])
        writer.writeheader()
        for name, email in sc_user_to_email.items():
            writer.writerow({"shortcut_user_name": name, "shortcut_user_email": email})
    sys.exit(1)


def main():
    """
    Script entry-point for importing a Pivotal Tracker CSV export into a Shortcut workspace.
    """
    cfg = load_config()
    populate_states_csv(cfg["states_csv_file"], cfg["workflow_id"])
    populate_users_csv(cfg["users_csv_file"], cfg["pt_csv_file"])
    print(
        f"""[Success] Pivotal Tracker export and local configuration have been validated.
          Identified %d epics, %d stories, %d iterations, and %d labels to import.

[Next] Run 'python pivotal_import.py' to see a dry-run or to perform the actual import into Shortcut."""
        % (0, 0, 0, 0)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
