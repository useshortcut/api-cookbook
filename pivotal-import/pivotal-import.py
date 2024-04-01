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


def console_emitter(item):
    print(
        "Creating {type} {entity[name]} created at {entity[created_at]}".format_map(
            item
        )
    )
    return {item["type"]: 1}


def single_entity_emitter(item):
    if item["type"] == "story":
        sc_post("/stories", item["entity"])
    else:
        sc_post("/epics", item["entity"])
    return {item["type"]: 1}


def bulk_emitter(bulk_commit_fn):
    _bulk_accumulator = []
    _bulk_limit = 20

    def commit():
        bulk_commit_fn(_bulk_accumulator)
        _bulk_accumulator.clear()

    def emitter(item):
        _bulk_accumulator.append(item)

        if len(_bulk_accumulator) >= _bulk_limit:
            commit()
        return {item["type"]: 1}

    emitter.commit = commit
    return emitter


def bulk_console_emitter(items):
    for item in items:
        console_emitter(item)


def bulk_entity_creator(items):
    stories = []
    epics = []
    for item in items:
        if item["type"] == "story":
            stories.append(item["entity"])
        elif item["type"] == "epic":
            epics.append(item["entity"])

    if stories:
        sc_post("/stories/bulk", {"stories": stories})

    for epic in epics:
        sc_post("/epics", epic)


def url_to_external_links(url):
    return [url]


def parse_labels(labels: str):
    return [{"name": label} for label in labels.split(", ")]


def pivotal_state_to_workflow_state_id(state: str):
    # TODO use the actual workflow state mapping
    return state


def parse_username(name):
    # TODO convert the name to the best guess for the users
    return name


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
    "requested by": ("requester", parse_username),
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


def build_entity(ctx, row, headers):
    d = parse_row(row, headers)

    # ensure import label
    d.setdefault("labels", []).append({"name": "pivotal->shortcut"})

    # reconcile entity types
    type = "story"
    if d["story_type"] == "epic":
        type = "epic"

    # releases become chores
    if d["story_type"] == "release":
        d["story_type"] = "chore"
        d.setdefault("labels", []).append({"name": "pivotal-release"})

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

    elif type == "epic":
        pass

    entity = {k: d[k] for k in select_keys[type] if k in d}
    return {"type": type, "entity": entity, "parsed_row": d}


def load_workflow_states(csv_file):
    logger.debug(f"Loading workflow states from {csv_file}")
    d = {}
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sc_state_id = row.get("shortcut_state_id")
            if sc_state_id:
                d[row["pt_state"]] = int(sc_state_id)
    return d


def print_stats(stats):
    print("Import stats")
    for k, v in stats.items():
        print(f"  - {k} : {v}")


def main(argv):
    args = parser.parse_args(argv[1:])
    emitter = console_emitter

    if args.apply:
        if args.bulk:
            emitter = bulk_emitter(bulk_entity_creator)
        else:
            emitter = single_entity_emitter
    else:
        if args.bulk:
            emitter = bulk_emitter(bulk_console_emitter)
        else:
            emitter = console_emitter

    cfg = load_config()
    ctx = {}
    ctx["workflow_config"] = load_workflow_states(cfg["states_csv_file"])
    stats = Counter()

    with open(cfg["pt_csv_file"]) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            entity = build_entity(ctx, row, header)
            logger.debug("Emitting Entity: %s", entity)
            stats.update(emitter(entity))

    if hasattr(emitter, "commit"):
        emitter.commit()

    print_stats(stats)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
