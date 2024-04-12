#!/usr/bin/env python
# This imports a pivotal export CSV into Shortcut. Requires that users
# and states are properly mapped in users.csv and states.csv.
# See README.md for prerequisites, setup, and usage.
import argparse
import csv
import re
import sys
from datetime import datetime
from collections import Counter

from lib import *

parser = argparse.ArgumentParser(
    description="Imports the Pivotal Tracker CSV export to Shortcut",
)
parser.add_argument(
    "--apply", action="store_true", help="Actually creates the entities inside Shortcut"
)
parser.add_argument("--debug", action="store_true", help="Turns on debugging logs")


"""The batch size when running in batch mode"""
BATCH_SIZE = 100

"""The labels associated with all stories and epics that are created with this import script."""
PIVOTAL_TO_SHORTCUT_LABEL = "pivotal->shortcut"
_current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
PIVOTAL_TO_SHORTCUT_RUN_LABEL = f"pivotal->shortcut {_current_datetime}"

"""The label associated with all chore stories created from release types in Pivotal."""
PIVOTAL_RELEASE_TYPE_LABEL = "pivotal-release"

"""The label indicating a story had reviews in Pivotal."""
PIVOTAL_HAD_REVIEW_LABEL = "pivotal-had-review"


def sc_creator(items):
    """Create Shortcut entities utilizing bulk APIs whenever possible.

    Accepts a list of dicts that must have at least two keys `type`
    and `entity`. `type` must be either story or epic. `entity` must
    be the payload that is sent to the Shortcut API.

    Returns back the list of items with two new keys:
    - `imported_id`: the id of the entity that was created
    - `imported_entity`: the full entity that was created

    """
    batch_stories = []

    def create_stories(stories):
        entities = [s["entity"] for s in stories]
        created_entities = sc_post("/stories/bulk", {"stories": entities})
        for created, story in zip(created_entities, stories):
            story["imported_entity"] = created
        return stories

    for item in items:
        if item["type"] == "story":
            batch_stories.append(item)
        elif item["type"] == "epic":
            res = sc_post("/epics", item["entity"])
            item["imported_entity"] = res
        elif item["type"] == "label":
            res = sc_post("/labels", item["entity"])
            item["imported_entity"] = res
        else:
            raise RuntimeError("Unknown entity type {}".format(item["type"]))

        if len(batch_stories) >= BATCH_SIZE:
            create_stories(batch_stories)
            batch_stories.clear()

    if batch_stories:
        create_stories(batch_stories)

    return items


def url_to_external_links(url):
    return [url]


def parse_labels(labels: str):
    return [{"name": label} for label in re.split(r"\s*,\s*", labels)]


def parse_priority(priority):
    lowered = priority.lower()
    if lowered == "none":
        return None
    else:
        return lowered


col_map = {
    "id": "external_id",
    "title": "name",
    "description": "description",
    "type": "story_type",
    "estimate": ("estimate", int),
    "priority": ("priority", parse_priority),
    "current state": "pt_state",
    "labels": ("labels", parse_labels),
    "url": ("external_links", url_to_external_links),
    "created at": ("created_at", parse_date),
    "accepted at": ("accepted_at", parse_date),
    "deadline": ("deadline", parse_date),
    "requested by": "requester",
}

nested_col_map = {
    "blocker status": "blocker_state",
    "blocker": "blocker",
    "comment": ("comments", parse_comment),
    "owned by": "owners",
    "reviewer": "reviewers",
    "review type": "review_types",
    "review status": "review_states",
    "task status": "task_states",
    "task": "task_titles",
}

# These are the keys that are currently correctly populated in the
# build_entity map. They can be passed to the SC api unchanged. This
# list is effectively an allow list of top level attributes.
select_keys = {
    "story": [
        "comments",
        "created_at",
        "custom_fields",
        "description",
        "estimate",
        "external_id",
        "external_links",
        "follower_ids",
        "group_id",
        "labels",
        "name",
        "owner_ids",
        "requested_by_id",
        "story_type",
        "tasks",
        "workflow_state_id",
    ],
    "epic": [
        "created_at",
        "description",
        "external_id",
        "group_ids",
        "labels",
        "name",
    ],
}

review_as_comment_text_prefix = """\\[Pivotal Importer\\] Reviewers have been added as followers on this Shortcut Story.

The following table describes the state of their reviews when they were imported into Shortcut from Pivotal Tracker:

| Reviewer | Review Type | Review Status |
|---|---|---|"""


def escape_md_table_syntax(s):
    return s.replace("|", "\\|")


def parse_row(row, headers):
    d = dict()
    for ix, val in enumerate(row):
        v = val.strip()
        if not v:
            continue

        col = headers[ix]
        if col in col_map:
            col_info = col_map[col]
            if isinstance(col_info, str):
                d[col_info] = v
            else:
                (key, translator) = col_info
                d[key] = translator(v)

        if col in nested_col_map:
            col_info = nested_col_map[col]
            key = None
            if isinstance(col_info, str):
                key = col_info
            else:
                (key, translator) = col_info
                v = translator(v)
            d.setdefault(key, []).append(v)
    return d


def build_run_label_entity():
    return {"type": "label", "entity": {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}}


def build_entity(ctx, d):
    """Process the row to generate the payload needed to create the entity in Shortcut."""
    # ensure Shortcut entities have a Label that identifies this import
    d.setdefault("labels", []).extend(
        [{"name": PIVOTAL_TO_SHORTCUT_LABEL}, {"name": PIVOTAL_TO_SHORTCUT_RUN_LABEL}]
    )

    # The Shortcut Team/Group ID to assign to stories/epics,
    # may be None which the REST API interprets correctly.
    group_id = ctx["group_id"]

    # reconcile entity types
    type = "story"
    if d["story_type"] == "epic":
        type = "epic"

    # process comments
    comments = []
    for comment in d.get("comments", []):
        new_comment = comment.copy()
        author = new_comment.get("author")
        if author:
            del new_comment["author"]
            author_id = ctx["user_config"].get(author)
            if author_id:
                new_comment["author_id"] = author_id
        comments.append(new_comment)
    # other things we process are reified as comments,
    # so we'll add comments to the d later in processing

    # releases become Shortcut Stories of type "chore"
    if d["story_type"] == "release":
        d["story_type"] = "chore"
        d.setdefault("labels", []).append({"name": PIVOTAL_RELEASE_TYPE_LABEL})

    if type == "story":
        # assign to team/group
        d["group_id"] = group_id
        # process workflow state
        pt_state = d.get("pt_state")
        if pt_state:
            d["workflow_state_id"] = ctx["workflow_config"][pt_state]

        # process tasks
        tasks = [
            {"description": title, "complete": state == "completed"}
            for (title, state) in zip(
                d.get("task_titles", []), d.get("task_states", [])
            )
        ]
        if tasks:
            d["tasks"] = tasks

        # process user fields
        user_to_sc_id = ctx["user_config"]
        requester = d.get("requester")
        if requester:
            # if requester isn't found, this will cause the api to use
            # the owner of the token as the requester
            sc_requester_id = user_to_sc_id.get(requester)
            if sc_requester_id:
                d["requested_by_id"] = sc_requester_id

        owners = d.get("owners")
        if owners:
            d["owner_ids"] = [
                # filter out owners that aren't found
                user_to_sc_id[owner]
                for owner in owners
                if owner in user_to_sc_id
            ]

        reviewers = d.get("reviewers")
        if reviewers:
            d["follower_ids"] = [
                user_to_sc_id[reviewer]
                for reviewer in reviewers
                if reviewer in user_to_sc_id
            ]
            d.setdefault("labels", []).append({"name": PIVOTAL_HAD_REVIEW_LABEL})

        # format table of all reviewers, types, and statuses as a comment on the imported story
        if reviewers:
            comment_text = review_as_comment_text_prefix
            for reviewer, review_type, review_status in zip(
                d.get("reviewers", []),
                d.get("review_types", []),
                d.get("review_states", []),
            ):
                reviewer = escape_md_table_syntax(reviewer)
                review_type = escape_md_table_syntax(review_type)
                review_status = escape_md_table_syntax(review_status)
                comment_text += f"\n|{reviewer}|{review_type}|{review_status}|"
            comments.append(
                {"author_id": d.get("requested_by_id", None), "text": comment_text}
            )

        # Custom Fields
        custom_fields = []
        # process priority as Priority custom field
        pt_priority = d.get("priority")
        if pt_priority:
            custom_fields.append(
                {
                    "field_id": ctx["priority_custom_field_id"],
                    "value_id": ctx["priority_config"][pt_priority],
                }
            )

        if custom_fields:
            d["custom_fields"] = custom_fields

        # as a last step, ensure comments (both those that were comments
        # in Pivotal, and those we add during import to fill feature gaps)
        # are all added to the d dict
        if comments:
            d["comments"] = comments
        elif "comments" in d:
            del d["comments"]

    elif type == "epic":
        # While Pivotal's model does not have a requester or owners for
        # Epics, we can still apply the provided Team/Group assignment.
        d["group_ids"] = [group_id] if group_id is not None else []

    entity = {k: d[k] for k in select_keys[type] if k in d}
    return {"type": type, "entity": entity, "parsed_row": d}


def load_mapping_csv(csv_file, from_key, to_key, to_transform=identity):
    d = {}
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            val_str = row.get(to_key)
            val = None
            if val_str:
                val = to_transform(val_str)
            d[row[from_key]] = val

    return d


def load_priorities(csv_file):
    logger.debug(f"Loading priorities from {csv_file}")
    return load_mapping_csv(csv_file, "pt_priority", "shortcut_custom_field_value_id")


def load_users(csv_file):
    logger.debug(f"Loading users from {csv_file}")
    email_to_id = {user["email"]: user["id"] for user in fetch_members()}
    user_to_email = load_mapping_csv(csv_file, "pt_user_name", "shortcut_user_email")
    return {
        pt_user: email_to_id.get(sc_email)
        for pt_user, sc_email in user_to_email.items()
        if sc_email
    }


def load_workflow_states(csv_file):
    logger.debug(f"Loading workflow states from {csv_file}")
    return load_mapping_csv(csv_file, "pt_state", "shortcut_state_id", int)


def get_mock_emitter():
    _mock_global_id = 0

    def _get_next_id():
        nonlocal _mock_global_id
        id = _mock_global_id
        _mock_global_id += 1
        return id

    def mock_emitter(items):
        for item in items:
            entity_id = _get_next_id()
            created_entity = item["entity"].copy()
            created_entity["id"] = entity_id
            created_entity["entity_type"] = item["type"]
            created_entity["app_url"] = f"https://example.com/entity/{entity_id}"
            item["imported_entity"] = created_entity
            print("Creating {} {}".format(entity_id, item["entity"]["name"]))
        return items

    return mock_emitter


class EntityCollector:
    """Collect and process entities for import into Shortcut.

    The emitter is a function that takes a list of entities and
    performs the actions needed to create those entities in
    Shortcut. Must return a list of ids that represent the created
    entities.
    """

    def __init__(self, emitter=None):
        _mock_global_id = 0
        self.epics = []
        self.stories = []
        self.labels = []
        if emitter is None:
            emitter = get_mock_emitter()
        self.emitter = emitter

    def collect(self, item):
        if item["type"] == "story":
            self.stories.append(item)
        elif item["type"] == "epic":
            self.epics.append(item)
        elif item["type"] == "label":
            self.labels.append(item)
        else:
            raise RuntimeError("Unknown entity type {}".format(item["type"]))

        return {item["type"]: 1}

    def link_entities(self):
        # find all epics and their associated label
        # find all stories
        pass

    def commit(self):
        # create all the default labels
        self.labels = self.emitter(self.labels)
        for label in self.labels:
            if PIVOTAL_TO_SHORTCUT_RUN_LABEL == label["entity"]["name"]:
                label_url = label["imported_entity"]["app_url"]
                print(f"Import Started\n\nVisit {label_url} to monitor import progress")

        # create all the epics and find their associated epic ids
        self.epics = self.emitter(self.epics)

        print("Finished creating {} epics".format(len(self.epics)))
        epic_label_map = {}
        for epic in self.epics:
            for label in epic["entity"]["labels"]:
                label_name = label["name"]
                if label_name is not PIVOTAL_TO_SHORTCUT_LABEL:
                    epic_label_map[label_name] = epic["imported_entity"]["id"]

        # update all the stories with the appropriate epic ids
        for story in self.stories:
            for label in story["entity"].get("labels", []):
                label_name = label["name"]
                epic_id = epic_label_map.get(label_name)
                if epic_id is not None:
                    story["entity"]["epic_id"] = epic_id

        # create all the stories
        self.stories = self.emitter(self.stories)
        print("Finished creating {} stories".format(len(self.stories)))

        # Aggregate all the created stories and epics and labels into a list of maps
        created_entities = []
        created_set = set()
        for item in self.epics + self.stories:
            # add item
            entity = item["imported_entity"]
            if entity["id"] not in created_set:
                created_entities.append(entity)
                created_set.add(entity["id"])

        return created_entities


def process_pt_csv_export(ctx, pt_csv_file, entity_collector):
    stats = Counter()
    stats.update(entity_collector.collect(build_run_label_entity()))

    with open(pt_csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            row_info = parse_row(row, header)
            entity = build_entity(ctx, row_info)
            logger.debug("Emitting Entity: %s", entity)
            stats.update(entity_collector.collect(entity))

    print("Summary of data to be imported")
    print_stats(stats)


def write_created_entities_csv(created_entities):
    with open(shortcut_imported_entities_csv, "w") as f:
        writer = csv.DictWriter(f, ["id", "type", "name", "url"])
        writer.writeheader()
        for entity in created_entities:
            writer.writerow(
                {
                    "id": entity["id"],
                    "name": entity["name"],
                    "type": entity["entity_type"],
                    "url": entity["app_url"],
                }
            )


def build_ctx(cfg):
    ctx = {
        "group_id": cfg["group_id"],
        "priority_config": load_priorities(cfg["priorities_csv_file"]),
        "priority_custom_field_id": cfg["priority_custom_field_id"],
        "user_config": load_users(cfg["users_csv_file"]),
        "workflow_config": load_workflow_states(cfg["states_csv_file"]),
    }
    logger.debug("Built context %s", ctx)
    return ctx


def main(argv):
    args = parser.parse_args(argv[1:])
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    emitter = None
    if args.apply:
        emitter = sc_creator

    entity_collector = EntityCollector(emitter)

    cfg = load_config()
    ctx = build_ctx(cfg)
    print_rate_limiting_explanation()
    process_pt_csv_export(ctx, cfg["pt_csv_file"], entity_collector)

    created_entities = entity_collector.commit()
    write_created_entities_csv(created_entities)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
