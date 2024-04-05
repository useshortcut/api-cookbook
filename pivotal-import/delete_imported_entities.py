import sys
import logging
import argparse
import csv
from collections import Counter

import requests

from lib import *

parser = argparse.ArgumentParser(
    description="Deletes entities created in a previous Pivotal import",
)
parser.add_argument(
    "--apply", action="store_true", help="Actually deletes the entities inside Shortcut"
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


def delete_entity(entity_type, entity_id):
    prefix = None
    if entity_type == "story":
        prefix = "/stories/"
    elif entity_type == "epic":
        prefix = "/epics/"

    if prefix:
        try:
            sc_delete(f"{prefix}{entity_id}")
        except requests.HTTPError:
            printerr(f"Unable to delete {entity_type} {entity_id}")
            return None

    return True


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    counter = Counter()
    with open(shortcut_imported_entities_csv) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entity_id = row["id"]
            entity_type = row["type"]

            if args.apply:
                if delete_entity(entity_type, entity_id):
                    counter[entity_type] += 1
            else:
                counter[entity_type] += 1

    if not args.apply:
        print("Dry run! Rerun with --apply to actually delete!")

    if counter:
        print("Deletion stats")
        print_stats(counter)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
