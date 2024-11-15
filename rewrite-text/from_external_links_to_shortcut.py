# Given a CSV of entities to migrate, this script queries Shortcut for the stories in it
# and populates a file named rewrites_from_external_links_to_shortcut.csv with from and to
# values using the external links as the "from" and the story's application URL as the "to".
import csv
import sys
from lib import sc_get, validate_environment


def main(argv):
    if len(argv) != 2:
        print(f"Error: Incorrect arguments provided to this script: {argv[1:]}")
        print(
            "Usage: python from_external_links_to_shortcut.py <entities.csv>",
            file=sys.stderr,
        )
        sys.exit(1)
    validate_environment()
    entities_file = argv[1]
    out_file = "rewrites_from_external_links_to_shortcut.csv"

    with open(entities_file, "r") as in_file:
        csv_reader = csv.DictReader(in_file)

        print(
            f"Processing stories from {entities_file}, printing a dot per ten stories..."
        )
        with open(out_file, "w") as f:
            f.write("from,to\n")

        with open(out_file, "a") as f:
            progress = 0
            for row in csv_reader:
                progress += 1
                if progress % 10 == 0:
                    print(".", end="", flush=True)
                id = row["id"]  # Stories are the only entities with external_links
                if bool(id):
                    story = sc_get(f"/stories/{id}")
                    to_url = story["app_url"]
                    external_links = story["external_links"]
                    if len(external_links) > 0:
                        for from_url in external_links:
                            f.write(f"{from_url},{to_url}\n")
    print(f"\nFinished writing {out_file}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
