# Given a label id, writes a CSV to entities_with_label.csv with either an id or epic_id
# value on each row for the stories and epics respectively that have this label.
#
# The output CSV can be passed to the main rewrite_text.py script's --entities argument
# to rewrite these entities' textual components.

import re
import sys
from lib import sc_get, validate_environment


def main(argv):
    if len(argv) != 2:
        print(f"Error: Incorrect arguments provided to this script: {argv[1:]}")
        print("Usage: python entities_with_label.py <label-id>", file=sys.stderr)
        sys.exit(1)
    validate_environment()
    label_id = argv[1]
    if not bool(re.match(r"^[0-9]+$", label_id)):
        print(
            f"Error: Argument must be the label's numeric id, instead received a {type(label_id)} : {label_id}"
        )
        print("Usage: python entities_with_label.py <label-id>", file=sys.stderr)
        sys.exit(1)

    stories = sc_get(f"/labels/{label_id}/stories")
    epics = sc_get(f"/labels/{label_id}/epics")
    out_file = "entities_with_label.csv"
    print(f"Writing {len(stories)} story IDs and {len(epics)} epic IDs to {out_file}")
    with open(out_file, "w") as f:
        f.write("id,epic_id\n")

    with open(out_file, "a") as f:
        for story in stories:
            f.write(f"{story['id']},\n")
        for epic in epics:
            f.write(f",{epic['id']}\n")

    print(f"Finished writing {out_file}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
