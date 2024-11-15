import argparse
import csv
import logging
import sys

from lib import print_rate_limiting_explanation, sc_get, sc_put, validate_environment

parser = argparse.ArgumentParser(
    description="Write CSV of unused labels in your Shortcut workspace",
)
parser.add_argument(
    "--rewrites",
    dest="rewrites_file",
    default="rewrites.csv",
    help="CSV of 'from' and 'to' values to rewrite.",
)
parser.add_argument(
    "--entities",
    dest="entities_file",
    default="entities.csv",
    help="CSV with each row having either 'id' (story id), 'epic_id', 'iteration_id', 'milestone_id', or 'objective_id' for entities to be rewritten.",
)

parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


output_csv_keys = [
    "id",
    "entity_type",
    "name",
    "app_url",
]


def write_labels_to_archive(out_file_name, labels):
    logging.info(f"Writing {len(labels)} labels to archive to {out_file_name}")
    with open(out_file_name, "w") as f:
        writer = csv.DictWriter(f, fieldnames=output_csv_keys)
        writer.writeheader()
        for label in labels:
            writer.writerow({k: label[k] for k in output_csv_keys})


def calculate_archivable_labels(include_completed):
    to_archive = []
    logging.info(
        "Fetching all labels with all associated stories & epics from your Shortcut workspace..."
    )
    all_labels = sc_get("/labels")
    len_labels = len(all_labels)
    logging.info(f"Processing {len_labels} labels...")
    for idx, label in enumerate(all_labels):
        if idx % 10 == 0:
            logging.info("Progress: %.0f%%" % (100 * (idx + 1) / len_labels))
        id = label["id"]
        label_stories = sc_get(f"/labels/{id}/stories")
        label_epics = sc_get(f"/labels/{id}/epics")
        no_stories = len(label_stories) == 0
        no_epics = len(label_epics) == 0
        if no_stories and no_epics:
            to_archive.append(label)
            continue
        if include_completed:
            incomplete_stories = []
            for story in label_stories:
                if not story["completed"]:
                    incomplete_stories.append(story)
                    continue
            incomplete_epics = []
            for epic in label_epics:
                if not epic["completed"]:
                    incomplete_epics.append(epic)
                    continue
            no_incomplete_stories = len(incomplete_stories) == 0
            no_incomplete_epics = len(incomplete_epics) == 0
            if no_incomplete_stories and no_epics:
                to_archive.append(label)
                continue
            if no_incomplete_epics and no_stories:
                to_archive.append(label)
                continue
            if no_incomplete_stories and no_incomplete_epics:
                to_archive.append(label)
                continue
    return to_archive


def archive_labels(input_csv_file_name):
    with open(input_csv_file_name) as f:
        reader = csv.DictReader(f)
        for row in reader:
            label_id = row.get("id")
            logging.info(
                f"Archiving https://app.shortcut.com/settings/label/{label_id}"
            )
            sc_put(f"/labels/{label_id}", {"archived": True})


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    validate_environment()
    print_rate_limiting_explanation()

    rewrites_file = args.rewrites_file
    entities_files = args.entities_file
    print(f"Rewrite & Entity CSVs {rewrites_file} and {entities_files}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
