#!/usr/bin/env python
# This imports a pivotal export CSV into Shortcut. Requires that users
# and states are properly mapped in users.csv and states.csv.
# See README.md for prerequisites, setup, and usage.
import argparse
import csv
import logging
import re
import sys
from datetime import datetime
from collections import Counter

from lib import *

parser = argparse.ArgumentParser(
    description="Imports the Pivotal Tracker CSV export to Shortcut",
)
parser.add_argument("--apply", action="store_true", required=False)
parser.add_argument("--bulk", action="store_true", required=False)

"""The batch size when running in batch mode"""
BATCH_SIZE = 20

"""The label associated with all stories and epics that are created with this import script."""
PIVOTAL_TO_SHORTCUT_LABEL = "pivotal->shortcut"

"""The label associated with all chore stories created from release types in Pivotal."""
PIVOTAL_RELEASE_TYPE_LABEL = "pivotal-release"


def single_sc_creator(items):
    """Create a Shortcut entities on at a time.

    Accepts a list of dicts that must have at least two keys `type`
    and `entity`. `type` must be either story or epic. `entity` must
    be the payload that is sent to the Shortcut API.

    Returns a list of created entity ids.

    """
    ids = []
    for item in items:
        if item["type"] == "story":
            res = sc_post("/stories", item["entity"])
            ids.append(res["id"])
        else:
            res = sc_post("/epics", item["entity"])
            ids.append(res["id"])

    return ids


def bulk_sc_creator(items):
    """Create Shortcut entities utilizing bulk APIs whenever possible.

    Accepts a list of dicts that must have at least two keys `type`
    and `entity`. `type` must be either story or epic. `entity` must
    be the payload that is sent to the Shortcut API.

    Returns a list of created entity ids in order.

    """
    stories = []
    ids = []

    def create_stories(stories):
        res = sc_post("/stories/bulk", {"stories": stories})
        ids.extend([s["id"] for s in res])
        stories.clear()

    for item in items:
        if item["type"] == "story":
            stories.append(item["entity"])
        else:
            res = sc_post("/epics", item["entity"])
            ids.append(res["id"])

        if len(stories) >= BATCH_SIZE:
            create_stories(stories)

    if stories:
        create_stories(stories)

    return ids


def url_to_external_links(url):
    return [url]


def parse_labels(labels: str):
    return [{"name": label} for label in re.split(r"\s*,\s*", labels)]


def split_by_comma(owners: str):
    return re.split(r"[,\s]", owners)


col_map = {
    "id": "external_id",
    "title": "name",
    "description": "description",
    "type": "story_type",
    "estimate": ("estimate", int),
    "priority": "priority",
    "current state": "pt_state",
    "labels": ("labels", parse_labels),
    "url": ("external_links", url_to_external_links),
    "created at": ("created_at", parse_date),
    "accepted at": ("accepted_at", parse_date),
    "deadline": ("deadline", parse_date),
    "requested by": "requester",
    "owned by": ("owners", split_by_comma),
}

nested_col_map = {
    "blocker": "blocker",
    "blocker status": "blocker_state",
    "task": "task_titles",
    "task status": "task_states",
    "comment": ("comments", parse_comment),
}

# These are the keys that are currently correctly populated in the
# build_entity map. They can be passed to the SC api unchanged. This
# list is effectively an allow list of top level attributes.
select_keys = {
    "story": [
        "name",
        "description",
        "external_links",
        "estimate",
        "workflow_state_id",
        "story_type",
        "created_at",
        "comments",
        "tasks",
        "labels",
        "external_id",
        "owner_ids",
        "requested_by_id",
    ],
    "epic": [
        "name",
        "description",
        "labels",
        "created_at",
        "external_id",
    ],
}


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


def build_entity(ctx, d):
    """Process the row to generate the payload needed to create the entity in Shortcut."""
    # ensure import label
    d.setdefault("labels", []).append({"name": PIVOTAL_TO_SHORTCUT_LABEL})

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
    if comments:
        d["comments"] = comments
    elif "comments" in d:
        del d["comments"]

    # releases become chores
    if d["story_type"] == "release":
        d["story_type"] = "chore"
        d.setdefault("labels", []).append({"name": PIVOTAL_RELEASE_TYPE_LABEL})

    if type == "story":
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
                # filter out woners that aren't found
                user_to_sc_id[owner]
                for owner in owners
                if owner in user_to_sc_id
            ]

    elif type == "epic":
        pass

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


def load_workflow_states(csv_file):
    logger.debug(f"Loading workflow states from {csv_file}")
    return load_mapping_csv(csv_file, "pt_state", "shortcut_state_id", int)


def load_users(csv_file):
    logger.debug(f"Loading users from {csv_file}")
    email_to_id = {user["email"]: user["id"] for user in fetch_members()}
    user_to_email = load_mapping_csv(csv_file, "pt_user_name", "shortcut_user_email")
    return {
        pt_user: email_to_id.get(sc_email)
        for pt_user, sc_email in user_to_email.items()
        if sc_email
    }


def print_stats(stats):
    print("Import stats")
    for k, v in stats.items():
        print(f"  - {k} : {v}")


def mock_emitter(items):
    ret = []
    for ix, item in enumerate(items):
        print("Creating {} {}".format(ix, item["entity"]))
        ret.append(ix)
    return ret


class EntityCollector:
    """Collect and process entities for import into Shortcut.

    The emitter is a function that takes a list of entities and
    performs the actions needed to create those entities in
    Shortcut. Must return a list of ids that represent the created
    entities.
    """

    def __init__(self, emitter=mock_emitter):
        self.epics = []
        self.stories = []

        self.emitter = emitter

    def collect(self, item):
        if item["type"] == "story":
            self.stories.append(item)
        else:
            self.epics.append(item)

        return {item["type"]: 1}

    def link_entities(self):
        # find all epics and their associated label
        # find all stories
        pass

    def commit(self):
        # create all the epics and find their associated epic ids
        epic_ids = self.emitter(self.epics)

        logger.debug("Finished epics {}".format(epic_ids))
        epic_label_map = {}
        for epic_id, epic in zip(epic_ids, self.epics):
            for label in epic["entity"]["labels"]:
                label_name = label["name"]
                if label_name is not PIVOTAL_TO_SHORTCUT_LABEL:
                    epic_label_map[label_name] = epic_id

        # update all the stories with the appropriate epic ids
        for story in self.stories:
            for label in story["entity"].get("labels", []):
                label_name = label["name"]
                epic_id = epic_label_map.get(label_name)
                if epic_id is not None:
                    story["entity"]["epic_id"] = epic_id

        # create all the stories
        self.emitter(self.stories)


def process_pt_csv_export(ctx, pt_csv_file, entity_collector):
    stats = Counter()

    with open(pt_csv_file) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            row_info = parse_row(row, header)
            entity = build_entity(ctx, row_info)
            logger.debug("Emitting Entity: %s", entity)
            stats.update(entity_collector.collect(entity))

    print_stats(stats)


def build_ctx(cfg):
    ctx = {
        "workflow_config": load_workflow_states(cfg["states_csv_file"]),
        "user_config": load_users(cfg["users_csv_file"]),
    }
    logger.debug("Built context %s", ctx)
    return ctx


def main(argv):
    args = parser.parse_args(argv[1:])
    emitter = mock_emitter
    if args.apply:
        if args.bulk:
            emitter = bulk_sc_creator
        else:
            emitter = single_sc_creator

    entity_collector = EntityCollector(emitter)

    cfg = load_config()
    ctx = build_ctx(cfg)
    process_pt_csv_export(ctx, cfg["pt_csv_file"], entity_collector)

    entity_collector.commit()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
