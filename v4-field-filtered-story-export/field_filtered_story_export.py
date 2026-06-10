import argparse
import csv
import logging
import os
import sys

from lib import now_ts, print_rate_limiting_explanation, sc_get, sc_get_url, validate_environment

parser = argparse.ArgumentParser(
    description="Export stories in a workflow state to CSV, with optional field filtering",
)
parser.add_argument(
    "-w",
    "--workflow-state-id",
    dest="workflow_state_id",
    required=True,
    help="The ID of the workflow state to export stories for",
)
parser.add_argument(
    "--fields",
    dest="fields",
    default="id,name,workflow_state,owners",
    help="Comma-separated list of fields to include in the response (default: id,name,workflow_state,owners)",
)
parser.add_argument(
    "--output-file",
    dest="output_file",
    help="Path to write CSV output to (defaults to ~/Downloads/)",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


def fetch_all_stories(workflow_state_id, fields):
    """
    Return all stories in a workflow state, requesting only the specified fields.

    The fields parameter reduces the response payload to only the data you need.
    Pagination is handled automatically via next_page_url.
    """
    all_stories = []
    data = sc_get(f"/workflow-states/{workflow_state_id}/stories", {"fields": fields})
    all_stories.extend(data.get("entities", []))
    logging.info(f"Fetching {data['total_items']} stories...")
    while data.get("next_page_url"):
        data = sc_get_url(data["next_page_url"])
        all_stories.extend(data.get("entities", []))
    return all_stories


def flatten_story(story):
    """Flatten nested v4 fields to scalar values suitable for CSV."""
    row = dict(story)
    if "workflow_state" in row and isinstance(row["workflow_state"], dict):
        row["workflow_state"] = row["workflow_state"].get("name", "")
    if "owners" in row and isinstance(row["owners"], dict):
        row["owners"] = "; ".join(
            o["name"] for o in row["owners"].get("entities", [])
        )
    if "deadline" in row and row["deadline"]:
        row["deadline"] = row["deadline"][:10]
    return row


def csv_file_name(workflow_state_id):
    ts = now_ts()
    return os.path.join(
        os.path.expanduser("~"), "Downloads", f"workflow-state-{workflow_state_id}-stories_{ts}.csv"
    )


def write_stories_csv(out_file_name, stories):
    if not stories:
        logging.info("No stories found.")
        return
    rows = [flatten_story(s) for s in stories]
    fieldnames = list(rows[0].keys())
    logging.info(f"Writing {len(rows)} stories to {out_file_name}")
    with open(out_file_name, "w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    stories = fetch_all_stories(args.workflow_state_id, args.fields)
    out_file = args.output_file or csv_file_name(args.workflow_state_id)
    write_stories_csv(out_file, stories)
    print(f"Wrote {len(stories)} stories to {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
