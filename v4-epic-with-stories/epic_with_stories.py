import argparse
import csv
import logging
import os
import sys

from lib import now_ts, print_rate_limiting_explanation, sc_get, sc_get_url, validate_environment

parser = argparse.ArgumentParser(
    description="Export all stories in a Shortcut epic as a CSV",
)
parser.add_argument(
    "-e",
    "--epic-id",
    dest="epic_id",
    required=True,
    help="The ID of the epic to export stories for",
)
parser.add_argument(
    "--output-file",
    dest="output_file",
    help="Path to write CSV output to (defaults to ~/Downloads/)",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")

csv_keys = ["id", "name", "state", "owners", "due_date"]


def fetch_all_stories(epic):
    """
    Return all stories in an epic.

    The epic response includes inline story summaries and a list_url pointing
    to the full paginated stories list. We always follow list_url to get full
    story objects (including workflow state, owners, and deadlines).
    """
    stories_collection = epic["entity"]["stories"]
    total = stories_collection["total_items"]

    if total == 0:
        return []

    logging.info(f"Fetching stories from {stories_collection['list_url']}")
    all_stories = []
    data = sc_get_url(stories_collection["list_url"])
    all_stories.extend(data.get("entities", []))
    while data.get("next_page_url"):
        data = sc_get_url(data["next_page_url"])
        all_stories.extend(data.get("entities", []))
    logging.info(f"Fetched {len(all_stories)} stories (excludes archived)")
    return all_stories


def story_to_row(story):
    owners = "; ".join(o["name"] for o in story.get("owners", {}).get("entities", []))
    deadline = story.get("deadline") or ""
    if deadline:
        deadline = deadline[:10]
    state = story.get("workflow_state", {}).get("name", story.get("workflow_state_id", ""))
    return {
        "id": story["id"],
        "name": story["name"],
        "state": state,
        "owners": owners,
        "due_date": deadline,
    }


def write_stories_csv(out_file_name, stories):
    logging.info(f"Writing {len(stories)} stories to {out_file_name}")
    with open(out_file_name, "w") as f:
        writer = csv.DictWriter(f, fieldnames=csv_keys)
        writer.writeheader()
        for story in stories:
            writer.writerow(story_to_row(story))


def csv_file_name(epic_id):
    ts = now_ts()
    return os.path.join(
        os.path.expanduser("~"), "Downloads", f"epic-{epic_id}-stories_{ts}.csv"
    )


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    epic = sc_get(f"/epics/{args.epic_id}")
    stories = fetch_all_stories(epic)
    out_file = args.output_file or csv_file_name(args.epic_id)
    write_stories_csv(out_file, stories)
    print(f"Wrote {len(stories)} stories to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
