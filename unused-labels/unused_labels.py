import argparse
import csv
import logging
import os
import sys

from lib import print_rate_limiting_explanation, sc_get, sc_put, validate_environment

parser = argparse.ArgumentParser(
    description="Write CSV of unused labels in your Shortcut workspace",
)
parser.add_argument(
    "--archive-labels",
    dest="input_file",
    help="WARNING: If provided, this CSV file is read and all labels listed in it are archived in your Shortcut workspace.",
)
parser.add_argument(
    "--include-completed",
    dest="include_completed",
    action="store_true",
    default=False,
    help="Include labels that have all their stories & epics completed.",
)
parser.add_argument(
    "--output-file",
    dest="output_file",
    default="labels-to-archive.csv",
    help="Name of file to write CSV results to.",
)

parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


output_csv_keys = [
    "id",
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

    if args.input_file:
        input_file = args.input_file
        if not os.path.exists(input_file):
            print(f"\nERROR: File {input_file} does not exist.\n")
            parser.print_usage()
            return 1
        archive_labels(input_file)
    else:
        output_file = args.output_file
        include_completed = args.include_completed
        labels = calculate_archivable_labels(include_completed)
        write_labels_to_archive(output_file, labels)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
