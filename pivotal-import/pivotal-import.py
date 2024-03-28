#!/usr/bin/env python
# This imports a pivotal export CSV into Shortcut. Requires that users
# and states are properly mapped in users.csv and states.csv.
# See README.md for prerequisites, setup, and usage.
import argparse
import csv
import sys
from datetime import datetime


from api import *

parser = argparse.ArgumentParser(
    description='Imports the Pivotal Tracker CSV export to Shortcut',
)
parser.add_argument('--apply', action='store_true', required=False)
parser.add_argument('--bulk', action='store_true', required=False)

def console_emitter(item):
    print(item)

def single_story_emitter(item):
    sc_post('/stories', item)

_bulk_accumulator = []
_bulk_limit = 20
def bulk_emitter(bulk_commit_fn):

    def flush():
        bulk_commit_fn(_bulk_accumulator)
        _bulk_accumulator.clear()

    def emitter(item):
        _bulk_accumulator.append(item)

        if len(_bulk_accumulator) >= _bulk_limit:
            flush()

    emitter.flush = flush
    return emitter

def bulk_console_emitter(items):
    print(items)

def bulk_story_creator(items):
    sc_post('/stories/bulk', items)


def url_to_external_links(url):
    return [url]

def split_labels(labels: str):
    return labels.split(', ')

def pivotal_state_to_workflow_state_id(state: str):
    # TODO use the actual workflow state mapping
    return state

def parse_date(d: str):
    return datetime.strptime(d, '%b %d, %Y').isoformat()

def parse_username(name):
    # TODO convert the name to the best guess for the users
    return name


col_map = {
    'title': 'name',
    'description': 'description',
    'type': 'story_type',
    'estimate': ('estimate', int),
    'priority': 'priority',
    'current state': ('workflow_state_id', pivotal_state_to_workflow_state_id),
    'labels': ('labels', split_labels),
    'url': ('external_links', url_to_external_links),
    'created at': ('created_at', parse_date),
    'accepted at': ('accepted_at', parse_date),
    'deadline': ('deadline', parse_date),
    'requested by': ('requester', parse_username),


}

nested_col_map = {
    'blocker': 'blocker',
    'blocker status': 'blocker_state',
    'task': 'task',
    'task status': 'task_state',
    'comment': 'comment'
}


def build_story(row: list[str], header: list[str]):

    d = dict()

    for ix, val in enumerate(row):
        v = val.strip()
        if not v:
            continue


        col = header[ix]
        if col in col_map:
            col_info = col_map[col]
            if isinstance(col_info, str):
                d[col_info] = v
            else:
                (key, translator) = col_info
                d[key] = translator(v)

        if col in nested_col_map:
            key = nested_col_map[col]
            d.setdefault(key, list()).append(v)

    if d['story_type'] in ['bug','feature','chore']:
        return d

def main(argv):
    args = parser.parse_args(argv[1:])
    emitter = console_emitter

    if args.apply:
        if args.bulk:
            emitter = bulk_emitter(bulk_story_creator)
        else:
            emitter = single_story_emitter
    else:
        if args.bulk:
            emitter = bulk_emitter(bulk_console_emitter)
        else:
            emitter = console_emitter

    with open("data/pivotal_export.csv", ) as csvfile:
        reader = csv.reader(csvfile)
        header = [col.lower() for col in next(reader)]
        for row in reader:
            story = build_story(row, header)
            if story:
                emitter(story)

    if hasattr(emitter, 'flush'):
        emitter.flush()

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
