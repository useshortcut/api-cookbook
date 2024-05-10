import argparse
import csv
import logging
import sys

from lib import now_ts, print_rate_limiting_explanation, sc_get, validate_environment

parser = argparse.ArgumentParser(
    description="Exports Epic comments as a CSV",
)
parser.add_argument(
    "-e",
    "--epic-id",
    dest="epic_id",
    help="Export comments for the Epic with the given ID from your Shortcut Workspace",
)
parser.add_argument(
    "--all-epics",
    dest="all_epics",
    action="store_true",
    help="Export comments for all Epics in your Shortcut Workspace",
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")

key_parent_id = "parent_id"
key_comments = "comments"
csv_keys = [
    "id",
    "author_id",
    "text",
    key_parent_id,
]


def write_epic_comment(writer, epic_comment, parent_id):
    """
    Given a CSV writer, an epic comment, and a possibly-None parent comment id,
    write a row of the final CSV with the epic comment's data. Then, recursively
    process any comments nested within this one.
    """
    writer.writerow(
        {k: epic_comment[k] if k != key_parent_id else parent_id for k in csv_keys}
    )
    nested_epic_comments = epic_comment[key_comments]
    for nested_epic_comment in nested_epic_comments:
        write_epic_comment(writer, nested_epic_comment, epic_comment["id"])


def write_epic_comments(out_file, epic_comments):
    """
    Fetch the comments for the epic with the given ID, then write
    to a CSV that contains the epic id and a timestamp all of the
    comments (and nested comments) associated with this epic.

    Writes a CSV with only the column headers if the epic has
    no comments.
    """
    writer = csv.DictWriter(out_file, fieldnames=csv_keys)
    writer.writeheader()
    for epic_comment in epic_comments:
        write_epic_comment(writer, epic_comment, None)


def fetch_and_write_epic_comments(epic_id):
    """
    Send a request to the 'List Epic Comments' endpoint in Shortcut's
    API, then write the comments to disk in CSV format.
    """
    epic_comments = sc_get(f"/epics/{epic_id}/comments")
    out_file_name = csv_file_name(epic_id)
    logging.info(f"Writing CSV with epic comments to {out_file_name}")
    with open(out_file_name, "w") as f:
        write_epic_comments(f, epic_comments)


def csv_file_name(epic_id):
    """
    Return a file name for the CSV file containing the given epic's
    comments.
    """
    ts = now_ts()
    return f"epic-{epic_id}-comments_{ts}.csv"


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    if args.all_epics:
        epics = sc_get("/epics")
        logging.info(f"Fetching and writing comments for {len(epics)} epics...")
        for epic in epics:
            fetch_and_write_epic_comments(epic["id"])
    elif args.epic_id:
        fetch_and_write_epic_comments(args.epic_id)
    else:
        logging.error("One of --epic-id or --all-epics is required.")
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
